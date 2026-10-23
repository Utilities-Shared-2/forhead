import pigpio
import time
import subprocess
import threading
from config import *

class PIDController:
    """PID controller using global constants with anti-windup & robust dt"""
    def __init__(self, kp=PID_KP, ki=PID_KI, kd=PID_KD, output_limits=(-5, 5)):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.setpoint = 0.0
        self.input = 0.0
        self.output = 0.0

        self.last_input = 0.0
        self.integral = 0.0
        self.last_time = time.time()

        # Output limits in degrees (incremental movement per update)
        self.min_output, self.max_output = output_limits
        self.integral_limit = 50.0  # Prevents windup runaway

    def set_input(self, value):
        self.input = value

    def update(self):
        current_time = time.time()
        dt = current_time - self.last_time
        
        # Guard against zero or negative dt (clock jitter)
        if dt <= 0.0001:
            return self.output

        self.last_time = current_time

        error = self.setpoint - self.input

        # Proportional
        P = self.kp * error

        # Integral with anti-windup clamp
        self.integral += error * dt
        self.integral = max(-self.integral_limit, min(self.integral_limit, self.integral))
        I = self.ki * self.integral

        # Derivative on measurement (prevents sudden setpoint jolts)
        derivative = (self.input - self.last_input) / dt
        D = self.kd * derivative

        # Combined output
        output = P + I - D

        # Clamp output to incremental degree limits
        self.output = max(self.min_output, min(self.max_output, output))

        # Save state
        self.last_input = self.input
        return self.output

    def reset(self):
        self.integral = 0.0
        self.last_input = 0.0
        self.output = 0.0
        self.last_time = time.time()

class IoControl:
    defaultInc = SERVO_INCREMENT

    def __init__(self, debug=False):
        self.debug = debug
        # --- Auto-start pigpiod if it's not running ---
        if not self._is_pigpiod_running():
            print("[INFO] pigpiod not detected, starting daemon...")
            self._start_pigpiod()
            time.sleep(0.5)  # small delay for it to initialize

        # Connect to pigpiod daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise IOError("[Warning] Could not connect to pigpiod. Make sure it’s running with: sudo pigpiod")

        # Setup the pins
        self.base_pin = GPIO_BASE_PIN
        self.camera_pin = GPIO_CAMERA_PIN
        self.switch_pin = GPIO_SWITCH_PIN
        self.resetToggled = False

        # Initialize pins
        self.pi.set_mode(self.base_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.camera_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.switch_pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.switch_pin, pigpio.PUD_UP)

        #Apply Glitch Filter (Debounce)
        self.pi.set_glitch_filter(self.switch_pin, GPIO_DEBOUNCE_TIME_US)
        # pigpio.EITHER_EDGE will trigger on both FALLING (0) and RISING (1) transitions
        self.cb = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.switch_callback)

        # Initialize PID controllers
        self.pan_pid = PIDController(PAN_KP, PAN_KI, PAN_KD)
        self.pitch_pid = PIDController(PITCH_KP, PITCH_KI, PITCH_KD)

        # Initialize positions
        self.camera_angle = SERVO_CENTER
        self.base_angle = SERVO_CENTER
        print("[INFO] initializing servo position")
        self.center()

        # Track when new input is available
        self.new_input_available = threading.Event()
        self.new_input_lock = threading.Lock()

        # Start PID update thread
        self.running = True
        self.pid_thread = threading.Thread(target=self._pid_loop, daemon=True)
        self.pid_thread.start()

    # ------------------------
    # Helper methods
    # ------------------------
    def _is_pigpiod_running(self):
        """Check if pigpiod process is running."""
        try:
            output = subprocess.check_output(["pgrep", "pigpiod"])
            return bool(output.strip())
        except subprocess.CalledProcessError:
            return False

    def _start_pigpiod(self):
        """Start the pigpio daemon using sudo."""
        try:
            subprocess.run(["sudo", "pigpiod"], check=True)
        except Exception as e:
            raise RuntimeError(f"Failed to start pigpiod: {e}")

    @staticmethod
    def degrees_to_pulsewidth(angle):
        """Maps a 0-270 degree angle to 500-2500 microseconds.

        - 0 deg -> 0.5 ms (500 µs) - 135 deg -> 1.5 ms (1500 µs) - 270 deg -> 2.5 ms
        (2500 µs)
        """
        # Clamp angle between 0 and 270 degrees
        angle = max(0.0, min(270.0, angle))
        # Linear mapping formula
        pulsewidth = 500 + (angle / 270.0) * 2000
        return int(pulsewidth)

    def set_servo_pulsewidth(self, pin, pulsewidth):
        """
        Set the servo pulse width on the given pin.
        """
        self.pi.set_servo_pulsewidth(pin, pulsewidth)

    def set_servo_degree(self,pin,degree):
        """
        Set the servo degree on the given pin.
        """
        pulsewidth = self.degrees_to_pulsewidth(degree)
        self.set_servo_pulsewidth(pin, pulsewidth)

    def set_delta(self, pan_delta, pitch_delta):
        """Set both pan and pitch deltas directly (for PID control)"""
        with self.new_input_lock:
            self.pan_pid.set_input(pan_delta)
            self.pitch_pid.set_input(pitch_delta)
            # Reset integral when no face detected (zero input) to prevent drift
            if pan_delta == 0 and pitch_delta == 0:
                self.pan_pid.integral = 0.0
                self.pitch_pid.integral = 0.0
            self.new_input_available.set()

    def get_base_angle(self):
        return self.base_angle

    def get_camera_angle(self):
        return self.camera_angle

    def switch_callback(self,gpio, level, tick):
        """Handles the press (FALLING) and release (RISING) events."""

        if level == 0:  # FALLING edge (Switch Pressed)
            print("--- Limit Switch Pressed! ---")
            self.resetToggled = True
            self.center()

        elif level == 1:  # RISING edge (Switch Released)
            print("--- Limit Switch Released! ---")
            self.resetToggled = False

    def _pid_loop(self):
        """Background thread to update PID controllers only when new input is available"""
        while self.running:
            # Wait for new input (with timeout to allow graceful shutdown)
            self.new_input_available.wait(timeout=0.1)
            self.new_input_available.clear()

            with self.new_input_lock:
                # Update PID controllers
                pan_output = self.pan_pid.update()
                pitch_output = self.pitch_pid.update()

            # Apply incremental movement (PID output is delta in degrees)
            pan_degrees = self.base_angle + pan_output
            pitch_degrees = self.camera_angle + pitch_output

            # Clamp to valid range with software limits
            pan_degrees = max(PAN_MIN, min(PAN_MAX, pan_degrees))
            pitch_degrees = max(PITCH_MIN, min(PITCH_MAX, pitch_degrees))

            # Debug output: show movement direction based on delta
            if self.debug:
                pan_direction = "LEFT" if pan_output < 0 else "RIGHT" if pan_output > 0 else "NONE"
                pitch_direction = "DOWN" if pitch_output < 0 else "UP" if pitch_output > 0 else "NONE"
                print(f"[DEBUG] Pan delta: {pan_output:.2f}° -> {pan_direction}, Pitch delta: {pitch_output:.2f}° -> {pitch_direction}")

            # Update servos
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(pan_degrees))
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(pitch_degrees))

            # Update angle tracking
            self.base_angle = pan_degrees
            self.camera_angle = pitch_degrees

    def stop_all(self):
        self.running = False
        if self.pid_thread.is_alive():
            self.pid_thread.join(timeout=1.0)
        self.pi.set_servo_pulsewidth(self.base_pin, 0)
        self.pi.set_servo_pulsewidth(self.camera_pin, 0)
        self.cb.cancel()
        self.pi.stop()

    def center(self):
        # Reset PID controllers
        self.pan_pid.reset()
        self.pitch_pid.reset()
        self.pan_pid.set_input(0)
        self.pitch_pid.set_input(0)

        self.camera_angle = SERVO_CENTER
        self.base_angle = SERVO_CENTER
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle))
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle))
        time.sleep(1)

    def read_switch(self):
        self.pi.read(self.switch_pin)

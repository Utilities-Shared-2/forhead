import pigpio
import time
import subprocess
import threading
from config import *

class PIDController:
    """Simple PID controller for smooth servo movement"""
    def __init__(self, kp=PID_KP, ki=PID_KI, kd=PID_KD):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = 0.0
        self.input = 0.0
        self.output = 0.0
        self.last_input = 0.0
        self.integral = 0.0
        self.last_time = time.time()

    def set_input(self, value):
        self.input = value

    def update(self):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt == 0:
            return
        self.last_time = current_time

        error = self.setpoint - self.input

        # Proportional
        P = self.kp * error

        # Integral
        self.integral += error * dt
        I = self.ki * self.integral

        # Derivative
        derivative = (self.input - self.last_input) / dt
        D = self.kd * derivative

        # Calculate output
        self.output = P + I - D

        # Update state
        self.last_input = self.input

    def reset(self):
        self.integral = 0.0
        self.last_input = 0.0
        self.output = 0.0

class IoControl:
    defaultInc = SERVO_INCREMENT

    def __init__(self):
        # --- Auto-start pigpiod if it's not running ---
        if not self._is_pigpiod_running():
            print("[INFO] pigpiod not detected, starting daemon...")
            self._start_pigpiod()
            time.sleep(0.5)  # small delay for it to initialize

        # Connect to pigpiod daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise IOError("[Warning] Could not connect to pigpiod. Make sure it’s running with: sudo pigpiod")

        # GPIO pin numbers (BOARD → BCM conversion if needed)
        # BOARD 11 → BCM 17
        # BOARD 13 → BCM 27
        # BOARD 37 → BCM 26
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
        self.pan_pid = PIDController(PID_KP, PID_KI, PID_KD)
        self.pitch_pid = PIDController(PID_KP, PID_KI, PID_KD)

        # Initialize positions
        self.camera_angle = SERVO_CENTER
        self.base_angle = SERVO_CENTER
        print("[INFO] initializing servo position")
        self.center()

        # Start PID update thread - RE-ENABLED with proper tuning for ~30 FPS
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
    def degrees_to_pulsewidth(degrees):
        """
        Convert degrees (SERVO_DEGREES_MIN–SERVO_DEGREES_MAX) to pulse width (SERVO_PULSE_MIN–SERVO_PULSE_MAX µs)
        """
        degrees = max(SERVO_DEGREES_MIN, min(SERVO_DEGREES_MAX, degrees))
        # min pulse width(0.5 = 0 deg) + (degrees we want to get*(relation between pulsewidth and degrees)
        return SERVO_PULSE_MIN + degrees * ((SERVO_PULSE_MAX - SERVO_PULSE_MIN) / (SERVO_DEGREES_MAX - SERVO_DEGREES_MIN))


    def set_servo_pulsewidth(self, pin, pulsewidth):
        """
        Set the servo pulse width on the given pin.
        """
        self.pi.set_servo_pulsewidth(pin, pulsewidth)


    def rotate_right(self, inc = defaultInc):
        """Set positive pan delta (object is to the right, move right)"""
        # Direct servo control - bypass PID
        self.base_angle = min(PAN_MAX, self.base_angle + inc)
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle))

    def rotate_left(self, inc = defaultInc):
        """Set negative pan delta (object is to the left, move left)"""
        # Direct servo control - bypass PID
        self.base_angle = max(PAN_MIN, self.base_angle - inc)
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle))

    def rotate_up(self, inc = defaultInc):
        """Set negative pitch delta (object is up, move up)"""
        # Direct servo control - bypass PID
        self.camera_angle = max(PITCH_MIN, self.camera_angle - inc)
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle))

    def rotate_down(self, inc = defaultInc):
        """Set positive pitch delta (object is down, move down)"""
        # Direct servo control - bypass PID
        self.camera_angle = min(PITCH_MAX, self.camera_angle + inc)
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle))

    def set_delta(self, pan_delta, pitch_delta):
        """Set both pan and pitch deltas directly (for PID control)"""
        self.pan_pid.set_input(pan_delta)
        self.pitch_pid.set_input(pitch_delta)

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
        """Background thread to update PID controllers at fixed rate"""
        while self.running:
            self.pan_pid.update()
            self.pitch_pid.update()

            # Convert PID output to absolute degrees (0-270)
            pan_degrees = SERVO_CENTER + self.pan_pid.output
            pitch_degrees = SERVO_CENTER + self.pitch_pid.output

            # Clamp to valid range with software limits
            pan_degrees = max(PAN_MIN, min(PAN_MAX, pan_degrees))
            pitch_degrees = max(PITCH_MIN, min(PITCH_MAX, pitch_degrees))

            # # Debug: print PID outputs
            # print(f"PID: pan_input={self.pan_pid.input:.1f}, pan_output={self.pan_pid.output:.1f}, pan_degrees={pan_degrees:.1f}")
            # print(f"PID: pitch_input={self.pitch_pid.input:.1f}, pitch_output={self.pitch_pid.output:.1f}, pitch_degrees={pitch_degrees:.1f}")

            # Update servos
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(pan_degrees))
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(pitch_degrees))

            # Update angle tracking
            self.base_angle = pan_degrees
            self.camera_angle = pitch_degrees

            time.sleep(PID_SAMPLE_TIME / 1000.0)

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

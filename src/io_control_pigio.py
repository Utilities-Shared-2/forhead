import pigpio
import time
import subprocess
import threading

class PIDController:
    """Simple PID controller for smooth servo movement"""
    def __init__(self, kp=2.0, ki=0.0, kd=0.5):
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
    defaultInc = 2
    # Debouncing: Glitch filter time in microseconds (us)
    DEBOUNCE_TIME_US = 10000
    # PID constants (matching ESP32 defaults)
    DEFAULT_KP = 2.0
    DEFAULT_KI = 0.0
    DEFAULT_KD = 0.5
    # Sample time for PID updates (ms)
    SAMPLE_TIME = 20

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
        self.base_pin = 17
        self.camera_pin = 27
        self.switch_pin = 26
        self.resetToggled = False
        # Initialize pins
        self.pi.set_mode(self.base_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.camera_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.switch_pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.switch_pin, pigpio.PUD_UP)
        #Apply Glitch Filter (Debounce)
        self.pi.set_glitch_filter(self.switch_pin, self.DEBOUNCE_TIME_US)
        # pigpio.EITHER_EDGE will trigger on both FALLING (0) and RISING (1) transitions
        self.cb = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.switch_callback)

        # Initialize PID controllers
        self.pan_pid = PIDController(self.DEFAULT_KP, self.DEFAULT_KI, self.DEFAULT_KD)
        self.pitch_pid = PIDController(self.DEFAULT_KP, self.DEFAULT_KI, self.DEFAULT_KD)

        # Initialize positions
        self.camera_angle = 135
        self.base_angle = 135
        print("[INFO] initializing servo position")
        self.center()

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
    def degrees_to_pulsewidth(degrees):
        """
        Convert degrees (0–270) to pulse width (500–2500 µs)
        """
        degrees = max(0, min(270, degrees))
        # min pulse width(0.5 = 0 deg) + (degrees we want to get*(relation between pulsewidth and degrees)
        return 500 + degrees * ((2500 - 500) / 270)


    def set_servo_pulsewidth(self, pin, pulsewidth):
        """
        Set the servo pulse width on the given pin.
        """
        self.pi.set_servo_pulsewidth(pin, pulsewidth)


    def rotate_right(self, inc = defaultInc):
        """Set positive pan delta (object is to the right, move right)"""
        self.pan_pid.set_input(inc)

    def rotate_left(self, inc = defaultInc):
        """Set negative pan delta (object is to the left, move left)"""
        self.pan_pid.set_input(-inc)

    def rotate_up(self, inc = defaultInc):
        """Set negative pitch delta (object is up, move up)"""
        self.pitch_pid.set_input(-inc)

    def rotate_down(self, inc = defaultInc):
        """Set positive pitch delta (object is down, move down)"""
        self.pitch_pid.set_input(inc)

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
            pan_degrees = 135 + self.pan_pid.output
            pitch_degrees = 135 + self.pitch_pid.output

            # Clamp to valid range
            pan_degrees = max(0, min(270, pan_degrees))
            pitch_degrees = max(0, min(270, pitch_degrees))

            # Update servos
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(pan_degrees))
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(pitch_degrees))

            # Update angle tracking
            self.base_angle = pan_degrees
            self.camera_angle = pitch_degrees

            time.sleep(self.SAMPLE_TIME / 1000.0)

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

        self.camera_angle = 135
        self.base_angle = 135
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.camera_angle))
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.base_angle))
        time.sleep(1)

    def read_switch(self):
        self.pi.read(self.switch_pin)

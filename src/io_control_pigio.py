import pigpio
import time
import subprocess

class IoControl:
    defaultInc = 2
    # Debouncing: Glitch filter time in microseconds (us)
    DEBOUNCE_TIME_US = 10000
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
        # BOARD 37 → BCM 26 (if used)
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
        cb = self.pi.callback(self.switch_pin, pigpio.EITHER_EDGE, self.switch_callback)


        # Initialize positions
        print("[INFO] initalizing servo position")
        self.center()

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
        if self.base_angle <= 270:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle + inc))
            self.base_angle += inc
        return


    def rotate_left(self, inc = defaultInc):
        if self.base_angle >= 0:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle - inc))
            self.base_angle -= inc
        return

    def rotate_up(self, inc = defaultInc):
        if self.camera_angle <= 270:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle + inc))
            self.camera_angle += inc
        return

    def rotate_down(self, inc = defaultInc):
        if self.camera_angle >= 0:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle - inc))
            self.camera_angle -= inc
        return

    def get_base_angle(self):
        return self.base_angle

    def get_camera_angle(self):
        return self.camera_angle

    def switch_callback(self,level, tick):
        """Handles the press (FALLING) and release (RISING) events."""

        if level == 0:  # FALLING edge (Switch Pressed)
            print("--- Limit Switch Pressed! ---")
            self.resetToggled = True
            self.center()

        elif level == 1:  # RISING edge (Switch Released)
            print("--- Limit Switch Released! ---")
            self.resetToggled = False
            time.sleep(4)

    def stop_all(self):
        self.pi.set_servo_pulsewidth(self.base_pin, 0)
        self.pi.set_servo_pulsewidth(self.camera_pin, 0)
        self.pi.stop()

    def center(self):
        self.camera_angle = 135
        self.base_angle = 135
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.camera_angle))
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.base_angle))
        time.sleep(1)


import pigpio
import time


class IoControl:
    defaultInc = 0.1
    def __init__(self):
        # Connect to pigpiod daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise IOError("Could not connect to pigpiod. Make sure it’s running with: sudo pigpiod")

        # GPIO pin numbers (BOARD → BCM conversion if needed)
        # BOARD 11 → BCM 17
        # BOARD 13 → BCM 27
        # BOARD 37 → BCM 26 (if used)
        self.base_pin = 17
        self.camera_pin = 27
        #self.switch_pin = 26

        # PWM frequency and angle setup
        self.camera_angle = 135
        self.base_angle = 135

        # Initialize pins
        self.pi.set_mode(self.base_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.camera_pin, pigpio.OUTPUT)
        # self.pi.set_mode(self.switch_pin, pigpio.INPUT)
        # self.pi.set_pull_up_down(self.switch_pin, pigpio.PUD_OFF)

        # Initialize positions
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.camera_angle))
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.base_angle))
        time.sleep(1)


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
            time.sleep(1)
        return


    def rotate_left(self, inc = defaultInc):
        if self.base_angle >= 0:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle - inc))
            self.base_angle -= inc
            time.sleep(1)
        return

    def rotate_up(self, inc = defaultInc):
        if self.camera_angle <= 270:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle + inc))
            self.camera_angle += inc
            time.sleep(1)
        return

    def rotate_down(self, inc = defaultInc):
        if self.camera_angle >= 0:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle - inc))
            self.camera_angle -= inc
            time.sleep(1)
        return

    def get_base_angle(self):
        return self.base_angle

    def get_camera_angle(self):
        return self.camera_angle

    # def get_toggled_status(self):
    #     value = self.pi.read(self.switch_pin)
    #     print(value)
    #     return value == 0
    def stop_all(self):
        self.pi.set_servo_pulsewidth(self.base_pin, 0)
        self.pi.set_servo_pulsewidth(self.camera_pin, 0)
        self.pi.stop()

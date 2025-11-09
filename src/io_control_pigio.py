import pigpio
import time


class IoControl:
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
        self.switch_pin = 26

        # PWM frequency and angle setup
        self.camera_angle = 270
        self.base_angle = 270

        # Initialize pins
        self.pi.set_mode(self.base_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.camera_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.switch_pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.switch_pin, pigpio.PUD_OFF)

        # Initialize positions
        self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(135))
        self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(135))
        time.sleep(1)
        self.stop_servo(self.base_pin)
        self.stop_servo(self.camera_pin)


    def degrees_to_pulsewidth(self, degrees):
        """
        Convert degrees (0–270) to pulse width (500–2500 µs)
        """
        degrees = max(0, min(270, degrees))
        return 500 + (degrees * 2000 / 270)


    def set_servo_pulsewidth(self, pin, pulsewidth):
        """
        Set the servo pulse width on the given pin.
        """
        self.pi.set_servo_pulsewidth(pin, pulsewidth)


    def stop_servo(self, pin):
        """
        Stop PWM signal to prevent jitter.
        """
        self.pi.set_servo_pulsewidth(pin, 0)


    def moveRight(self):
        if self.base_angle <= 270:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle + 0.1))
            self.base_angle += 0.1
            time.sleep(1)
            self.stop_servo(self.base_pin)
        return

    def moveRightInc(self, inc):
        if self.base_angle <= 270:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle + inc))
            self.base_angle += inc
            time.sleep(1)
            self.stop_servo(self.base_pin)
        return

    def moveLeft(self):
        if self.base_angle >= 0:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle - 0.1))
            self.base_angle -= 0.1
            time.sleep(1)
            self.stop_servo(self.base_pin)
        return

    def moveLeftInc(self, inc):
        if self.base_angle >= 0:
            self.set_servo_pulsewidth(self.base_pin, self.degrees_to_pulsewidth(self.base_angle - inc))
            self.base_angle -= inc
            time.sleep(1)
            self.stop_servo(self.base_pin)
        return

    def moveUp(self):
        if self.camera_angle <= 270:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle + 0.1))
            self.camera_angle += 0.1
            time.sleep(1)
            self.stop_servo(self.camera_pin)
        return

    def moveUpInc(self, inc):
        if self.camera_angle <= 270:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle + inc))
            self.camera_angle += inc
            time.sleep(1)
            self.stop_servo(self.camera_pin)
        return

    def moveDown(self):
        if self.camera_angle >= 0:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle - 0.1))
            self.camera_angle -= 0.1
            time.sleep(1)
            self.stop_servo(self.camera_pin)
        return

    def moveDownInc(self, inc):
        if self.camera_angle >= 0:
            self.set_servo_pulsewidth(self.camera_pin, self.degrees_to_pulsewidth(self.camera_angle - inc))
            self.camera_angle -= inc
            time.sleep(1)
            self.stop_servo(self.camera_pin)
        return

    def getBaseAngle(self):
        return self.base_angle

    def getCameraAngle(self):
        return self.camera_angle

    def getToggledStatus(self):
        value = self.pi.read(self.switch_pin)
        print(value)
        return value == 0

import RPi.GPIO as GPIO
import time


class IoControl:
    def __init__(self):
        # PWM signal .5ms  = 0, 2.5ms = 270
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(37, GPIO.IN)  # Flip Switch
        GPIO.setup(11, GPIO.OUT)  # Base motor(pin32)
        GPIO.setup(13, GPIO.OUT)  # Camera motor (pin33)


        self.base = GPIO.PWM(11, 50)
        self.camera = GPIO.PWM(13, 50)
        self.base.start(0)
        self.camera.start(0)
        self.base.ChangeDutyCycle(7.5) #initalize the position to be 135 deg
        self.camera.ChangeDutyCycle(7.5)
        self.base.stop()
        self.camera.stop()
        self.camera_angle = 135
        self.base_angle = 135
        time.sleep(0.5)
        #base.ChangeDutyCycle(0)
        #base.ChangeDutyCycle(0)


    def degrees_to_duty_cycle(self, degrees):
        """
        Convert degrees to duty cycle percentage for a servo motor.
        
        Args:
            degrees (float): Angle in degrees (0-270)
            
        Returns:
            float: Duty cycle percentage (2.5% to 12.5%)
        """
        # Ensure degrees are within valid range
        degrees = max(0, min(270, degrees))
        # Convert degrees to duty cycle (0.5ms to 2.5ms for 0-270 degrees at 50Hz)
        # 50Hz = 20ms period
        duty_cycle = (0.5 + (degrees * 2 / 270)) / 20 * 100
        # Simplified formula:
        #duty_cycle = (2.5 + (degrees * 10 / 270)
        return duty_cycle


    def moveRight(self):
        if self.base_angle <=270:
            self.base.start(0)
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle+0.1))
            self.base_angle += 0.1
            self.base.stop()
        return

    def moveRightInc(self, inc):
        if self.base_angle <= 270:
            self.base.start(0)
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle + inc))
            self.base_angle += inc
            self.base.stop()
        return

    def moveLeft(self):
        if self.base_angle >= 0:
            self.base.start(0)
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle-0.1))
            self.base_angle -= 0.1
            self.base.stop()
        return

    def moveLeftInc(self, inc):
        if self.base_angle >= 0:
            self.base.start(0)
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle - inc))
            self.base_angle -= inc
            self.base.stop()
        return

    def moveUp(self):
        if self.camera_angle <=270:
            self.camera.start(0)
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle+0.1))
            self.camera_angle += 0.1
            self.camera.stop()
        return

    def moveUpInc(self, inc):
        if self.camera_angle <=270:
            self.camera.start(0)
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle+inc))
            self.camera_angle += inc
            self.camera.stop()
        return

    def moveDown(self):
        if self.camera_angle >= 0:
            self.camera.start(0)
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle-0.1))
            self.camera_angle -= 0.1
            self.camera.stop()
        return

    def moveDownInc(self, inc):
        if self.camera_angle >= 0:
            self.camera.start(0)
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle-inc))
            self.camera_angle -= inc
            self.camera.stop()
        return


    def getBaseAngle(self):
        return self.base_angle

    def getCameraAngle(self):
        return self.camera_angle

    def getToggledStatus(self):
        if GPIO.input(37) == GPIO.LOW:
            return True
        else:
            return False

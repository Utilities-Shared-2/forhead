import RPi.GPIO as GPIO
import time


#self.base_angle = 135
#self.camera_angle = 135
#base = None
#camera = None

class Io_Control:
    def __init__(self):
        # PWM signal .5ms  = 0, 2.5ms = 270
        GPIO.setmode(GPIO.BOARD)
        #GPIO.setup(37, GPIO.IN)  # Flip Switch
        GPIO.setup(11, GPIO.OUT)  # Base motor(pin32)
        GPIO.setup(13, GPIO.OUT)  # Camera motor (pin33)
        #GPIO.setup(12, GPIO.OUT)
        #GPIO.setup(13, GPIO.OUT)

        self.base = GPIO.PWM(11, 50)
        self.camera = GPIO.PWM(13, 50)
        self.base.start(0)
        self.camera.start(0)
        self.base.ChangeDutyCycle(7.5) #initalize the position to be 135 deg
        self.camera.ChangeDutyCycle(7.5)
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
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle+0.1))
            time.sleep(0.5)
            self.base_angle += 0.1
        return

    def moveRightInc(self, inc):
        if self.base_angle <= 270:
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle + inc))
            time.sleep(0.5)
            self.base_angle += inc
        return

    def moveLeft(self):
        if self.base_angle >= 0:
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle-0.1))
            time.sleep(0.5)
            self.base_angle -= 0.1
        return

    def moveLeftInc(self, inc):
        if self.base_angle >= 0:
            self.base.ChangeDutyCycle(self.degrees_to_duty_cycle(self.base_angle - inc))
            time.sleep(0.5)
            self.base_angle -= inc
        return

    def moveUp(self):
        if self.camera_angle <=270:
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle+0.1))
            time.sleep(0.5)
            self.camera_angle += 0.1
        return

    def moveUpInc(self, inc):
        if self.camera_angle <=270:
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle+inc))
            time.sleep(0.5)
            self.camera_angle += inc
        return

    def moveDown(self):
        if self.camera_angle >= 0:
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle-0.1))
            self.camera_angle -= 0.1
        return

    def moveDownInc(self, inc):
        if self.camera_angle >= 0:
            self.camera.ChangeDutyCycle(self.degrees_to_duty_cycle(self.camera_angle-inc))
            time.sleep(0.5)
            self.camera_angle -= inc
        return


    def getBaseAngle(self):
        return self.base_angle

    def getCameraAngle(self):
        return self.camera_angle

    def getToggledStatus(self):
        return True
        if GPIO.input(37) == GPIO.LOW:
            return True
        else:
            return False

import RPi.GPIO as GPIO

base_angle = 135
camera_angle = 135
base = None
camera = None

def __init__():
    global base, camera
    # PWM signal .5ms  = 0, 2.5ms = 270
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(37, GPIO.IN)  # Flip Switch
    GPIO.setup(32, GPIO.OUT)  # Base motor(pin32)
    GPIO.setup(33, GPIO.OUT)  # Camera motor (pin33)
    base = GPIO.PWM(12, 50)
    camera = GPIO.PWM(13, 50)
    base.start(0)
    camera.start(0)
    base.ChangeDutyCycle(7.5) #initalize the position to be 135 deg
    camera.ChangeDutyCycle(7.5)


def degrees_to_duty_cycle(degrees):
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
    # duty_cycle = (0.5 + (degrees * 2 / 270)) / 20 * 100
    # Simplified formula:
    duty_cycle = 2.5 + (degrees * 10 / 270)
    return duty_cycle


def moveRight():
    global base_angle
    if base_angle <=270:
        base.ChangeDutyCycle(degrees_to_duty_cycle(base_angle+0.1))
        base_angle += 0.1
    return

def moveRight(inc):
    global base_angle
    if base_angle <= 270:
        base.ChangeDutyCycle(degrees_to_duty_cycle(base_angle + inc))
        base_angle += inc
    return

def moveLeft():
    global base_angle
    if base_angle >= 0:
        base.ChangeDutyCycle(degrees_to_duty_cycle(base_angle-0.1))
        base_angle -= 0.1
    return

def moveLeft(inc):
    global base_angle
    if base_angle >= 0:
        base.ChangeDutyCycle(degrees_to_duty_cycle(base_angle - inc))
        base_angle -= inc
    return

def moveUp():
    global camera_angle
    if camera_angle <=270:
        camera.ChangeDutyCycle(degrees_to_duty_cycle(camera_angle+0.1))
        camera_angle += 0.1
    return

def moveUp(inc):
    global camera_angle
    if camera_angle <=270:
        camera.ChangeDutyCycle(degrees_to_duty_cycle(camera_angle+inc))
        camera_angle += inc
    return

def moveDown():
    global camera_angle
    if camera_angle >= 0:
        camera.ChangeDutyCycle(degrees_to_duty_cycle(camera_angle-0.1))
        camera_angle -= 0.1
    return

def moveDown(inc):
    global camera_angle
    if camera_angle >= 0:
        camera.ChangeDutyCycle(degrees_to_duty_cycle(camera_angle-inc))
        camera_angle -= inc
    return


def getBaseAngle():
    global base_angle
    return base_angle

def getCameraAngle():
    global camera_angle
    return camera_angle

def getToggledStatus():
    if GPIO.input(37) == GPIO.LOW:
        return True
    else:
        return False
import serial
import time

class IoControl:
    defaultInc = 2

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        Initialize UART communication with ESP32
        Default port is /dev/ttyUSB0, can be changed to /dev/ttyACM0 or other
        ESP32 expects commands in format: pan_delta,pitch_delta
        where delta is pixels from center (negative = left/up, positive = right/down)
        """
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for ESP32 to initialize
            print(f"[INFO] Connected to ESP32 on {port} at {baudrate} baud")
            self.resetToggled = False
            # Initialize to center position
            self.center()
        except serial.SerialException as e:
            raise IOError(f"[ERROR] Could not open serial port {port}: {e}")

    def set_delta(self, pan_delta, pitch_delta):
        """
        Send both pan and pitch deltas directly to ESP32
        This is the preferred method for PID control
        """
        command = f"{pan_delta},{pitch_delta}\n"
        self.serial.write(command.encode())
        print(f"set delta: {command.strip()}")

    def stop_all(self):
        """Send center command and close serial connection"""
        self.center()
        if self.serial.is_open:
            self.serial.close()
            print("[INFO] Serial connection closed")

import serial
import time
from config import *

class IoControl:
    defaultInc = SERVO_INCREMENT

    def __init__(self, port=UART_PORT, baudrate=UART_BAUD_RATE, debug=False):
        """
        Initialize UART communication with ESP32
        Default port is UART_PORT, can be changed to /dev/ttyACM0 or other
        ESP32 expects commands in format: pan_delta,pitch_delta
        where delta is pixels from center (negative = left/up, positive = right/down)
        """
        self.debug = debug
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # Wait for ESP32 to initialize
            print(f"[INFO] Connected to ESP32 on {port} at {baudrate} baud")
            self.resetToggled = False
            # Initialize to center position
            self.center()
        except serial.SerialException as e:
            raise IOError(f"[ERROR] Could not open serial port {port}: {e}")

    def center(self):
        """Send center command (0, 0 deltas) to ESP32"""
        self.set_delta(0, 0)
        time.sleep(1)

    def set_delta(self, pan_delta, pitch_delta):
        """
        Send both pan and pitch deltas directly to ESP32
        This is the preferred method for PID control
        """
        command = f"{pan_delta},{pitch_delta}\n"
        self.serial.write(command.encode())

        # Debug output: show movement direction based on delta
        if self.debug:
            pan_direction = "LEFT" if pan_delta < 0 else "RIGHT" if pan_delta > 0 else "NONE"
            pitch_direction = "UP" if pitch_delta < 0 else "DOWN" if pitch_delta > 0 else "NONE"
            print(f"[DEBUG] Pan delta: {pan_delta:.2f} -> {pan_direction}, Pitch delta: {pitch_delta:.2f} -> {pitch_direction}")
        else:
            print(f"set delta: {command.strip()}")

    def stop_all(self):
        """Send center command and close serial connection"""
        self.center()
        if self.serial.is_open:
            self.serial.close()
            print("[INFO] Serial connection closed")

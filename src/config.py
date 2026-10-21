"""
Configuration file for face tracking system
All tunable parameters and defaults are centralized here
"""

# ====================
# Servo Hardware Settings
# ====================
SERVO_PULSE_MIN = 500      # Minimum pulse width in microseconds
SERVO_PULSE_MAX = 2500     # Maximum pulse width in microseconds
SERVO_DEGREES_MIN = 0      # Minimum servo angle in degrees
SERVO_DEGREES_MAX = 270    # Maximum servo angle in degrees
SERVO_CENTER = 135         # Center position in degrees

# GPIO Pin assignments (BCM numbering)
GPIO_BASE_PIN = 27         # Pan servo (base rotation)
GPIO_CAMERA_PIN = 17        # Pitch servo (camera tilt)
GPIO_SWITCH_PIN = 26        # Limit switch
GPIO_DEBOUNCE_TIME_US = 10000  # Glitch filter time in microseconds

# ====================
# Servo Software Limits
# ====================
# Pitch limits relative to center (135 degrees)
PITCH_MIN = 95             # 135 - 40 = 95 (40 degrees above horizontal)
PITCH_MAX = 180            # 135 + 45 = 180 (45 degrees below horizontal)
# Pan limits
PAN_MIN = 0                # Full range
PAN_MAX = 270              # Full range

# ====================
# PID Controller Settings
# ====================
# Proportional-Integral-Derivative controller gains
# P - Current Size
# I - Past History
# D - Future Speed
# Default Value
PID_KP = 0.1               # Proportional gain
PID_KI = 0.0               # Integral gain
PID_KD = 0.05              # Derivative gain
PID_SAMPLE_TIME = 30       # Sample time in milliseconds (match detection FPS)

PITCH_KP = 0.25             # Proportional gain
PITCH_KI = 0            # Integral gain
PITCH_KD = 0.5            # Derivative gain

PAN_KP = 0.35              # Proportional gain
PAN_KI = 0              # Integral gain
PAN_KD = 0.45            # Derivative gain

# ====================
# Face Detection Settings
# ====================
DETECTION_CONFIDENCE_THR = 0.5      # Minimum confidence threshold
DETECTION_OVERLAP_THR = 0.7         # NMS overlap threshold
DETECTION_INPUT_SIZE = (128, 128)   # Model input resolution
DETECTION_MODEL_PATH = "../model/blazeface.tflite"
DETECTION_NUM_THREADS = 4           # Number of threads for TFLite inference

# ====================
# Control Loop Settings
# ====================
DELTA_SCALE_FACTOR = 10.0   # Scale pixel deltas for PID (divide by this value)
SERVO_INCREMENT = 2         # Default servo movement increment

# ====================
# Camera Settings
# ====================
CAMERA_INDEX = 0            # OpenCV camera index
CAMERA_WIDTH = 640          # Default capture width
CAMERA_HEIGHT = 480         # Default capture height

# ====================
# UART Settings (ESP32 fallback)
# ====================
UART_PORT = "/dev/ttyUSB0"
UART_BAUD_RATE = 115200

# ====================
# Server Settings
# ====================
SERVER_PORT = 50300
SERVER_HOST = "0.0.0.0"

# ====================
# Client Settings
# ====================
CLIENT_JPEG_QUALITY = 80            # JPEG quality for frame upload (0-100)
CLIENT_REQUEST_TIMEOUT = 5          # HTTP request timeout in seconds
CLIENT_LOOP_DELAY = 0.05            # Delay between capture loops in seconds

# ====================
# Display Settings
# ====================
FPS_PRINT_INTERVAL = 30     # Print FPS every N frames
FPS_CUMULATIVE_RESET = 5000 # Reset cumulative FPS counter after this value

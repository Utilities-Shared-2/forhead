import cv2
import time
import argparse
import sys
import os
import signal
from config import *

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from recognition import FaceDetector
import utils
import framebox as app
from io_control_pigio import IoControl as IoControlPi
from io_control_uart import IoControl as IoControlUart

parser = argparse.ArgumentParser(description='Face tracking with servo control')
parser.add_argument('--raspi', action='store_true', help='Set if running on Raspberry Pi (enables GPIO control via pigpio). If not set, uses UART to communicate with ESP32.')
parser.add_argument('--uart-port', default=UART_PORT, help=f'UART port for ESP32 communication (default: {UART_PORT})')
parser.add_argument('--headless', action='store_true', help='Disable GUI display (useful for headless systems or when running via SSH without VNC)')
args = parser.parse_args()

if args.raspi:
    io = IoControlPi()
    print("[INFO] Using Raspberry Pi GPIO control mode")
else:
    try:
        io = IoControlUart(port=args.uart_port)
        print(f"[INFO] Using UART control mode on {args.uart_port}")
    except IOError as e:
        print(f"[ERROR] Failed to initialize UART: {e}")
        print("[INFO] Falling back to no control mode")
        io = None
#midpoint of the face box and the size of the frame
def center(midpoint, size):
    if io is None:
        return

    x_mid = size[1]//2
    y_mid = size[0]//2

    x = midpoint[0]
    y = midpoint[1]

    # Calculate delta from center (positive = right/down, negative = left/up)
    x_delta = x - x_mid
    y_delta = y - y_mid

    # Scale down deltas for PID controller (divide by DELTA_SCALE_FACTOR)
    # PID will smooth out the jitter
    x_delta_scaled = x_delta / DELTA_SCALE_FACTOR
    y_delta_scaled = y_delta / DELTA_SCALE_FACTOR

    # Send both deltas at once using set_delta (PID control)
    io.set_delta(x_delta_scaled, y_delta_scaled)
    print(f"delta: pan={x_delta}, pitch={y_delta}")

# Signal handler for graceful shutdown
shutdown_requested = False
def signal_handler(sig, frame):
    global shutdown_requested
    print("\n[INFO] Graceful shutdown requested...")
    shutdown_requested = True

def inital_movement():
    if io is not None:
        io.set_servo_degree(io.base_pin, 0)
        time.sleep(2)
        io.set_servo_degree(io.base_pin, 270)
        time.sleep(2)
        io.set_servo_degree(io.base_pin, 135)
        time.sleep(1)
        io.set_servo_degree(io.camera_pin, 95)
        time.sleep(2)
        io.set_servo_degree(io.camera_pin, 180)
        time.sleep(2)
        io.set_servo_degree(io.camera_pin, 135)
        time.sleep(2)


def main():
    inital_movement()
    global shutdown_requested
    if not args.headless:
        cv2.namedWindow("preview")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)


    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Use TFLite BlazeFace model (MediaPipe standard model)
    file = DETECTION_MODEL_PATH
    
    # Check if model exists
    if not os.path.exists(file):
        print(f"[ERROR] Model file not found: {file}")
        print("[INFO] Please run 'cd .. && python download_model.py' to download the model")
        sys.exit(1)
    
    face = FaceDetector(
        model=file,
        confidence_thr=DETECTION_CONFIDENCE_THR,
        overlap_thr=DETECTION_OVERLAP_THR,
        input_size=DETECTION_INPUT_SIZE
    )
    
    n_frames = 0
    fps_cum = 0.0

    while not shutdown_requested:
        if io is not None and args.raspi:
            io.read_switch()
        ret, frame=cap.read()

        start_time = time.perf_counter()
        bboxes, scores = face.inference(frame)
        end_time = time.perf_counter()

        n_frames += 1
        fps = 1.0 / (end_time - start_time)
        fps_cum += fps
        fps_avg = fps_cum / n_frames
        if fps_cum > FPS_CUMULATIVE_RESET:
            fps_cum = 0
            n_frames = 0

        # Print FPS every FPS_PRINT_INTERVAL frames
        if n_frames % FPS_PRINT_INTERVAL == 0:
            print(f"[FPS] Current: {fps:.1f}, Average: {fps_avg:.1f}")

        frame, rectangle = app.draw_largest_box(frame, bboxes, scores)
        #if the rectangle has nothing, this will be skipped
        if rectangle:
            (a,b),(c,d) = rectangle
            midpoint = (a+(c-a)//2, b+(d-b)//2)
            midpoint = (int(midpoint[0]), int(midpoint[1]))
            frame = utils.put_text_on_image(frame, position=(10, 150), text=f"midpoint{midpoint}")
            center(midpoint, frame.shape[:2])
        frame = utils.put_text_on_image(frame, position=(10,50), text='FPS: {:.2f}'.format( fps_avg ))

        # Display frame unless headless mode
        if not args.headless:
            cv2.imshow('preview', frame)
            k = cv2.waitKey(1) & 0xFF
            if k == 27 or k == ord('q'):
                shutdown_requested = True

    # Graceful shutdown
    print("[INFO] Shutting down...")
    if io is not None:
        io.center()  # Return servos to center
        io.stop_all()
    cap.release()
    if not args.headless:
        cv2.destroyAllWindows()
    print("[INFO] Shutdown complete")


if __name__ == "__main__":
    main()



import cv2
import time
import argparse


from recognition import FaceDetector
import utils
import framebox as app
from io_control_pigio import IoControl as IoControlPi
from io_control_uart import IoControl as IoControlUart

parser = argparse.ArgumentParser(description='Face tracking with servo control')
parser.add_argument('--raspi', action='store_true', help='Set if running on Raspberry Pi (enables GPIO control via pigpio). If not set, uses UART to communicate with ESP32.')
parser.add_argument('--uart-port', default='/dev/ttyUSB0', help='UART port for ESP32 communication (default: /dev/ttyUSB0)')
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

    # Send both deltas at once using set_delta (more efficient for PID control)
    io.set_delta(x_delta, y_delta)
    print(f"delta: pan={x_delta}, pitch={y_delta}")

def main():
    # cv2.namedWindow("preview")

    cap = cv2.VideoCapture(0)

    file = "model/public/ultra-lightweight-face-detection-slim-320/FP16/ultra-lightweight-face-detection-slim-320.xml"
    face = FaceDetector(model=file, confidence_thr = 0.5, overlap_thr = 0.7)
    
    n_frames = 0
    fps_cum = 0.0
    # fps_avg = 0.0

    while True:
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
        if fps_cum > 5000:
            fps_cum = 0
            n_frames = 0

        frame, rectangle = app.draw_largest_box(frame, bboxes, scores)
        #if the rectangle has nothing, this will be skipped
        if rectangle:
            (a,b),(c,d) = rectangle
            midpoint = (a+(c-a)//2, b+(d-b)//2)
            midpoint = (int(midpoint[0]), int(midpoint[1]))
            frame = utils.put_text_on_image(frame, position=(10, 150), text=f"midpoint{midpoint}")
            center(midpoint, frame.shape[:2])
        frame = utils.put_text_on_image(frame, position=(10,50), text='FPS: {:.2f}'.format( fps_avg ))

        cv2.imshow('frame', frame)
        k = cv2.waitKey(1) & 0xFF#copied straight from another repo. not sure why they used 0xff. maybe to extract just the ascii bytes
        if k == 27 or k == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    if io is not None:
        io.stop_all()



if __name__ == "__main__":
    main()



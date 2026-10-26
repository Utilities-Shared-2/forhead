import cv2
import time
import signal
import sys
import argparse


from recognition import FaceDetector
import utils
import framebox as app
from io_control_pigio import IoControl

io = None
running = True
args = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    print("\n[INFO] Shutdown signal received, cleaning up...")
    running = False

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class PIDController:
    def __init__(self, kp, ki, kd, MAX_PIXEL_ERROR, output_limits=1):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limits = output_limits
        self.MAX_PIXEL_ERROR = MAX_PIXEL_ERROR
        self.reset()

    def reset(self):
        self._prev_error = 0
        self._integral = 0
        self._last_time = time.time()

    def compute(self, setpoint, measured_value):
        #Calculate time delta
        current_time = time.time()
        dt = current_time - self._last_time
        if dt <= 0:
            dt = 0.02
        #Calculate error
        raw_error = setpoint - measured_value
        #Normalize error
        """
        Note :
        - We need to normalized because the error is delta in pixels, meaning each delta is on the magnitude few 100.
        - we normalize by dividing the error with the half of the resolution in respect to the axis.
        """
        normalized_error = max(-1.0, min(1.0, raw_error / self.MAX_PIXEL_ERROR))

        self._integral += normalized_error * dt
        derivative = (normalized_error - self._prev_error) / dt

        output = (self.kp * normalized_error) + (self.ki * self._integral) + (self.kd * derivative)
        print(f"output:{output}")
        output = output*self.output_limits
        self._prev_error = normalized_error
        self._last_time = current_time

        return output

# Initialize PID controllers for pan (x-axis) and tilt (y-axis)
# kp: proportional gain, ki: integral gain, kd: derivative gain
# These values may need tuning based on your specific servo characteristics
pan_pid = PIDController(kp=0.7, ki=0, kd=0.2, MAX_PIXEL_ERROR=540, output_limits=15)
tilt_pid = PIDController(kp=0.5, ki=0, kd=0.4, MAX_PIXEL_ERROR=320, output_limits=5)

#midpoint of the face box and the size of the frame
def center(midpoint, size):
    """
    How it works:
    - calculate the midpoint of the face box
    - calculate the midpoint of the frame
    - calculate the delta between the midpoint of the face box and the midpoint of the frame
    - runs it to PIDController.compute() to get the change in degree needed for the robot
    :param midpoint: array of the mid-point of the rectangle
    :param size: pixel coordinate of the face box
    """
    x_mid = size[1]//2
    y_mid = size[0]//2

    x = midpoint[0]
    y = midpoint[1]
    
    # print(f"Center X delta: {x_mid - x}")
    # print(f"Center Y delta: {y_mid - y}")
    # Calculate PID outputs for pan (x-axis) and tilt (y-axis)
    pan_output = pan_pid.compute(x_mid, x)
    tilt_output = tilt_pid.compute(y_mid, y)

    # Apply servo adjustments based on PID output
    if pan_output > 0:
        io.rotate_left(inc=abs(pan_output))
        print(f"rotate left: {abs(pan_output):.2f}")
    else:
        io.rotate_right(inc=abs(pan_output))
        print(f"rotate right: {pan_output:.2f}")

    if tilt_output > 0:
        io.rotate_up(inc=abs(tilt_output))
        print(f"rotate up: {tilt_output:.2f}")
    else:
        io.rotate_down(inc=abs(tilt_output))
        print(f"rotate down: {abs(tilt_output):.2f}")

def main():
    global io, args
    parser = argparse.ArgumentParser(description='Face tracking with servo control')
    parser.add_argument('--headless', action='store_true', help='Run without displaying video feed')
    parser.add_argument('--help', action='store_true', help='Show this list')
    args = parser.parse_args()

    if args.help:
        parser.print_help()
        return
    io = IoControl()

    cap = cv2.VideoCapture(0)

    file = "model/public/ultra-lightweight-face-detection-slim-320/FP16/ultra-lightweight-face-detection-slim-320.xml"
    face = FaceDetector(model=file, confidence_thr = 0.5, overlap_thr = 0.7)
    
    n_frames = 0
    fps_cum = 0.0
    # fps_avg = 0.0

    while running:
        io.read_switch()
        if not io.resetToggled:
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

            # Process face detection regardless of headless mode
            frame, rectangle = app.draw_largest_box(frame, bboxes, scores)
            #if the rectangle has nothing, this will be skipped
            if rectangle:
                (a,b),(c,d) = rectangle
                #calculate the midpoint of the rectangle
                midpoint = (a+(c-a)//2, b+(d-b)//2)
                #creating the midpoint object
                midpoint = (int(midpoint[0]), int(midpoint[1]))
                center(midpoint, frame.shape[:2])

            if not args.headless:
                if rectangle:
                    frame = utils.put_text_on_image(frame, position=(10, 150), text=f"midpoint{midpoint}")
                    frame = utils.put_text_on_image(frame, position=(10,50), text='FPS: {:.2f}'.format( fps_avg ))

                cv2.imshow('frame', frame)
                k = cv2.waitKey(1) & 0xFF#copied straight from another repo. not sure why they used 0xff. maybe to extract just the ascii bytes
                if k == 27 or k == ord('q'):
                    break
            else:
                # In headless mode, just a small delay to prevent CPU saturation
                # Use Ctrl+C to exit (handled by signal handler)
                time.sleep(0.001)
    io.center()
    # Cleanup resources
    print("[INFO] Releasing camera...")
    cap.release()
    if not args.headless:
        print("[INFO] Closing windows...")
        cv2.destroyAllWindows()
    print("[INFO] Stopping servos and GPIO...")
    io.stop_all()
    print("[INFO] Shutdown complete.")



if __name__ == "__main__":
    main()



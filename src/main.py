import cv2
import time


from recognition import FaceDetector
import utils
import framebox as app
from io_control_pigio import IoControl

io = IoControl()

class PIDController:
    def __init__(self, kp, ki, kd, output_limits=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limits = output_limits
        self.reset()

    def reset(self):
        self._prev_error = 0
        self._integral = 0
        self._last_time = time.time()

    def compute(self, setpoint, measured_value):
        current_time = time.time()
        dt = current_time - self._last_time
        if dt <= 0:
            dt = 0.01

        error = setpoint - measured_value

        self._integral += error * dt
        derivative = (error - self._prev_error) / dt

        output = (self.kp * error) + (self.ki * self._integral) + (self.kd * derivative)

        if self.output_limits:
            output = max(self.output_limits[0], min(self.output_limits[1], output))

        self._prev_error = error
        self._last_time = current_time

        return output

# Initialize PID controllers for pan (x-axis) and tilt (y-axis)
# kp: proportional gain, ki: integral gain, kd: derivative gain
# These values may need tuning based on your specific servo characteristics
pan_pid = PIDController(kp=0.08, ki=0.001, kd=0.02, output_limits=(-5, 5))
tilt_pid = PIDController(kp=0.08, ki=0.001, kd=0.02, output_limits=(-5, 5))

#midpoint of the face box and the size of the frame
def center(midpoint, size):
    x_mid = size[1]//2
    y_mid = size[0]//2

    x = midpoint[0]
    y = midpoint[1]

    # Calculate PID outputs for pan (x-axis) and tilt (y-axis)
    pan_output = pan_pid.compute(x_mid, x)
    tilt_output = tilt_pid.compute(y_mid, y)

    # Apply servo adjustments based on PID output
    if abs(pan_output) > 0.1:
        if pan_output > 0:
            io.rotate_right(inc=abs(pan_output))
            print(f"rotate right: {pan_output:.2f}")
        else:
            io.rotate_left(inc=abs(pan_output))
            print(f"rotate left: {abs(pan_output):.2f}")

    if abs(tilt_output) > 0.1:
        if tilt_output > 0:
            io.rotate_up(inc=abs(tilt_output))
            print(f"rotate up: {tilt_output:.2f}")
        else:
            io.rotate_down(inc=abs(tilt_output))
            print(f"rotate down: {abs(tilt_output):.2f}")

def main():
    # cv2.namedWindow("preview")

    cap = cv2.VideoCapture(0)

    file = "model/public/ultra-lightweight-face-detection-slim-320/FP16/ultra-lightweight-face-detection-slim-320.xml"
    face = FaceDetector(model=file, confidence_thr = 0.5, overlap_thr = 0.7)
    
    n_frames = 0
    fps_cum = 0.0
    # fps_avg = 0.0

    while True:
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
            cv2.waitKey(1)
            k = cv2.waitKey(1) & 0xFF#copied straight from another repo. not sure why they used 0xff. maybe to extract just the ascii bytes
            if k == 27 or k == ord('q'):
                break
    cv2.release()
    cv2.destroyAllWindows()
    io.stop_all()



if __name__ == "__main__":
    main()



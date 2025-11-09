import cv2
import time
from openvino.runtime import Core
import numpy as np

from recognition import FaceDetector
import utils
import framebox as app
from io_control_pigio import IoControl

io = IoControl()


#midpoint of the face box and the size of the frame
def center(midpoint, size):
    x_mid = size[1]//2
    y_mid = size[0]//2

    x = midpoint[0]
    y = midpoint[1]

    #we only rotate by a tiny bit. we can probably just recursively call it until it's centered
    if x > x_mid:
        io.rotate_left()
        print("rotate left")
        pass
    elif x < x_mid:
        io.rotate_right()
        print("rotate right")
        pass
    # print("base angle")
    # print(io.getBaseAngle())
    # time.sleep(1)
    if y < y_mid:
        io.rotate_up()
        print("rotate up",end=" ")
        pass
    elif y > y_mid:
        io.rotate_down()
        print("rotate down",end=" ")
        pass
    # print("camera angle")
    # print(io.getCameraAngle())
    # time.sleep(1)


def main():
    # cv2.namedWindow("preview")

    cap = cv2.VideoCapture(0)

    file = "model/public/ultra-lightweight-face-detection-slim-320/FP16/ultra-lightweight-face-detection-slim-320.xml"
    face = FaceDetector(model=file, confidence_thr = 0.5, overlap_thr = 0.7)
    
    n_frames = 0
    fps_cum = 0.0
    # fps_avg = 0.0

    while True:
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
            # if (io.getToggledStatus()):
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



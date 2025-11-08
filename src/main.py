import cv2
import time
from openvino.runtime import Core
import numpy as np

from recognition import FaceDetector
import utils
import app

def main():
    print("hi")
    # cv2.namedWindow("preview")

    cap = cv2.VideoCapture(0)

    file = "model/public/ultra-lightweight-face-detection-slim-320/FP16/ultra-lightweight-face-detection-slim-320.xml"
    face = FaceDetector(model=file, confidence_thr = 0.5, overlap_thr = 0.7)

    n_frames = 0
    fps_cum = 0.0
    fps_avg = 0.0
    while True:
        ret, frame=cap.read()

        start_time = time.perf_counter()
        bboxes, scores = face.inference(frame)
        end_time = time.perf_counter()

        n_frames += 1
        fps = 1.0 / (end_time - start_time)
        fps_cum += fps
        fps_avg = fps_cum / n_frames


        # frame = utils.draw_boxes_with_scores(frame, bboxes, scores)

        frame, rectangle = app.draw_largest_box(frame, bboxes, scores)
        
        

        frame = utils.put_text_on_image(frame, text='FPS: {:.2f}'.format( fps_avg ))


        cv2.imshow('frame', frame)
        cv2.waitKey(1)

        # print("hi")


        k = cv2.waitKey(1) & 0xFF#copied straight from another repo. not sure why they used 0xff. maybe to extract just the ascii bytes
        if k == 27 or k == ord('q'):
            break

    

    cv2.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
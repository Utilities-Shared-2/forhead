import cv2
import time


from recognition import FaceDetector
import utils
import framebox as app
# from io_control_pigio import IoControl

# io = IoControl()

commands = []


#midpoint of the face box and the size of the frame
def center(midpoint, size):
    x_mid = size[1]//2
    y_mid = size[0]//2

    x = midpoint[0]
    y = midpoint[1]

    #we only rotate by a tiny bit. we can probably just recursively call it until it's centered
    if x > x_mid:
        # io.rotate_left()
        commands.append({"cmd": "rotate_left",  "args": [0.1]})
        print("rotate left")
        pass
    elif x < x_mid:
        # io.rotate_right()
        commands.append({"cmd": "rotate_right",  "args": [0.1]})
        print("rotate right")
        pass
    # print("base angle")
    # print(io.getBaseAngle())
    # time.sleep(1)
    if y < y_mid:
        # io.rotate_up()
        commands.append({"cmd": "rotate_up",  "args": [0.1]})
        print("rotate up",end=" ")
        pass
    elif y > y_mid:
        # io.rotate_down()
        commands.append({"cmd": "rotate_down",  "args": [0.1]})
        print("rotate down",end=" ")
        pass
    # print("camera angle")
    # print(io.getCameraAngle())
    # time.sleep(.2)


# server_return_commands.py (on processor machine)
from flask import Flask, request, jsonify
import uuid, datetime

app = Flask(__name__)


cap = cv2.VideoCapture(0)

file = "model/public/ultra-lightweight-face-detection-slim-320/FP16/ultra-lightweight-face-detection-slim-320.xml"
face = FaceDetector(model=file, confidence_thr = 0.5, overlap_thr = 0.7)

n_frames = 0
fps_cum = 0.0
# fps_avg = 0.0




# server_no_checks.py
# Minimal Flask server: accept multipart 'image', decode to OpenCV frame, return commands.
# pip install flask opencv-python-headless numpy
from flask import Flask, request, jsonify
import numpy as np
import cv2
import uuid
import datetime

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process():
    # Expect form file named 'image'
    if "image" not in request.files:
        return jsonify({"error": "no image"}), 400

    data = request.files["image"].read()
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)   # <-- OpenCV BGR ndarray

    if img is None:
        return jsonify({"error": "invalid image"}), 400

    # At this point `img` is available to be processed (no AI here).
    # Return a simple commands list for the Pi to execute.
    # Replace the list below with your real command-generation later.

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
        exit()


    response = {
        "msg_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "shape": [int(img.shape[0]), int(img.shape[1])],   # height, width
        "commands": commands
    }
    return jsonify(response), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# if __name__ == "":
    # server_main()
app.run(host="0.0.0.0", port=6000)


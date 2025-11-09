# pi_dispatch_no_checks.py
# Minimal: capture frame -> POST to server -> call returned commands (no checks)
# pip install requests opencv-python-headless
import cv2
import requests
import time
from io_control_pigio import IoControl

SERVER = "http://192.168.1.100:50300/process"   # change to your server IP
AUTH = {"Authorization": "Bearer my-secret-token"}  # optional

io = IoControl()

# --- movement stubs (do not implement servo logic here) ---
def move_right(amount):
    io.rotate_right()
    # print(f"[stub] move_right({amount})")

def move_left(amount):
    io.rotate_left()
    # print(f"[stub] move_left({amount})")

def move_up(amount):
    io.rotate_up()
    # print(f"[stub] move_up({amount})")

def move_down(amount):
    io.rotate_down()
    # print(f"[stub] move_down({amount})")

def stop():
    io.stop_all()
    print("[stub] stop()")

# --- simple map (no validation) ---
CMD_MAP = {
    "move_right": move_right,
    "move_left":  move_left,
    "move_up":    move_up,
    "move_down":  move_down,
    "stop":       stop,
}

def post_frame_and_get_commands(frame_bgr, timeout=5):
    _, jpg = cv2.imencode('.jpg', frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    files = {"image": ("frame.jpg", jpg.tobytes(), "image/jpeg")}
    resp = requests.post(SERVER, headers=AUTH, files=files, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def main_loop(capture_index=0, loop_delay=0.05):
    cap = cv2.VideoCapture(capture_index)
    if not cap.isOpened():
        print("Failed to open camera.")
        return

    print("Starting capture loop. Ctrl-C to stop.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("camera read failed; retrying")
                time.sleep(0.5)
                continue

            try:
                payload = post_frame_and_get_commands(frame, timeout=5)
            except Exception as e:
                print("post error:", e)
                time.sleep(0.2)
                continue

            # Directly iterate returned commands and call mapped functions with unpacked args.
            # This intentionally performs NO validation.
            commands = payload.get("commands", [])
            for cmd in commands:
                name = cmd.get("cmd")
                args = cmd.get("args", [])
                fn = CMD_MAP.get(name)
                if fn is None:
                    print("unknown command (ignored):", name)
                    continue
                try:
                    # call with unpacked args (could raise if args mismatch)
                    fn(*args)
                except Exception as e:
                    print("command error:", name, e)

            time.sleep(loop_delay)

    except KeyboardInterrupt:
        print("Interrupted by user, exiting.")
    finally:
        cap.release()

# if __name__ == "__client__":
main_loop()

# resources

https://condadoslgpc.medium.com/an-extremely-fast-face-detection-using-openvino-openvinoexploration-375a796e4902

https://github.com/davidsandberg/facenet
https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/ultra-lightweight-face-detection-slim-320
https://github.com/openvinotoolkit/openvino_notebooks/tree/latest/notebooks/yolov12-optimization


omz_downloader --name ultra-lightweight-face-detection-rfb-slim --output_dir model

omz_converter --name ultra-lightweight-face-detection-rfb-slim --download_dir model --output_dir model --precision=FP16



# credits
https://github.com/Gabriellgpc/ultra-lightweight-face-detection/blob/main/main.py
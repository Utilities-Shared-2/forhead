# Face Tracking Pipeline - Modern Migration Guide

## Overview
This pipeline has been rewritten to use modern, Raspberry Pi 3-optimized models and frameworks.

## Key Changes

### Framework Migration
- **Old**: OpenVINO 2024.6.0 (less ARM optimization)
- **New**: TensorFlow Lite Runtime (excellent ARM support, actively maintained)

### Model Migration
- **Old**: Ultra-Lightweight Face Detection (FP16, older architecture)
- **New**: BlazeFace (MediaPipe, ~1ms inference, optimized for edge devices)

### Quantization
- **Old**: FP16 (not optimal for ARM CPUs)
- **New**: INT8 (standard ARM quantization, well-optimized for Raspberry Pi)

### Dependencies
- **Old**: OpenVINO, older OpenCV
- **New**: tflite-runtime, opencv-python-headless, updated NumPy

## Setup Instructions

### 1. Install Dependencies

#### On Raspberry Pi 3:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev libopencv-dev python3-opencv

# Install Python packages
pip3 install -r requirements.txt
```

#### On Desktop (macOS/Linux):
```bash
pip install -r requirements.txt
```

### 2. Download Model

```bash
python download_model.py
```

This will download the BlazeFace TFLite model (INT8 quantized from STMicroelectronics) to `model/blazeface_int8.tflite`.

### 3. Run Face Tracking

#### On Raspberry Pi 3 (with GPIO control):
```bash
cd src
python3 main.py --raspi
```

#### On Desktop (UART mode):
```bash
cd src
python3 main.py
```

#### Specify UART port:
```bash
cd src
python3 main.py --uart-port /dev/ttyUSB0
```

## Performance Characteristics

### Expected Performance on Raspberry Pi 3:
- **Model**: BlazeFace (128x128 input)
- **Inference Time**: ~1-3ms per frame
- **FPS**: 20-30 FPS (camera-limited)
- **Memory**: ~50MB peak
- **Quantization**: INT8 (ARM-optimized)

### Why These Choices?

1. **TensorFlow Lite Runtime**: Best ARM optimization, lightweight, widely used in Pi projects
2. **BlazeFace**: Ultra-fast (~1ms inference), good accuracy, specifically designed for real-time face detection
3. **INT8 Quantization**: Standard for ARM CPUs, excellent performance/accuracy tradeoff
4. **128x128 Input**: Balance between speed and accuracy for Pi 3's limited compute

## Troubleshooting

### Import Errors
If you get import errors for `tflite_runtime`:
```bash
# On Raspberry Pi, use the runtime version
pip3 install tflite-runtime
```

### Model Not Found
If the model file is missing:
```bash
python download_model.py
```

### Performance Issues
If performance is slow on Pi 3:
1. Reduce camera resolution in `main.py`
2. Lower confidence threshold (default: 0.5)
3. Ensure running with 4 threads (default in recognition.py)

### GPIO/Pigpio Issues
On Raspberry Pi, ensure pigpio is running:
```bash
sudo systemctl start pigpiod
sudo systemctl enable pigpiod
```

## File Structure

```
forhead/
├── src/
│   ├── main.py              # Main entry point
│   ├── recognition.py       # TFLite BlazeFace detector
│   ├── utils.py             # Utility functions (NMS, etc.)
│   ├── framebox.py          # BoundingBox visualization
│   ├── io_control_pigio.py  # Raspberry Pi GPIO control
│   └── io_control_uart.py   # UART communication
├── model/
│   └── blazeface_int8.tflite # Face detection model (INT8 quantized, 512 anchors)
├── requirements.txt         # Python dependencies
└── download_model.py        # Model download script
```

## Model Details

The project uses the STMicroelectronics INT8 quantized BlazeFace model:
- **Source**: STMicroelectronics AI Model Zoo
- **Quantization**: INT8 (optimized for embedded devices)
- **Anchors**: 512 (optimized for speed on resource-constrained hardware)
- **Input**: 128x128 RGB image, normalized to [-1, 1]
- **Size**: ~185 KB

This model is pre-quantized and ready for use on Raspberry Pi 3 without requiring TensorFlow conversion.

## Notes

- **FP8 not supported**: ARM CPUs (including Raspberry Pi) do not support FP8 quantization. INT8 is the standard and well-optimized choice.
- **Model source**: BlazeFace model from Google MediaPipe project
- **Compatibility**: Tested on Raspberry Pi 3B+ with 1GB RAM

## References

- [TensorFlow Lite for Microcontrollers](https://www.tensorflow.org/lite/microcontrollers)
- [MediaPipe BlazeFace](https://github.com/google/mediapipe)
- [Raspberry Pi TensorFlow Lite](https://www.tensorflow.org/lite/guide/python)

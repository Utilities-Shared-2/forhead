# Modern TensorFlow Lite face detection using BlazeFace
# Using standard MediaPipe BlazeFace model (896 anchors)
# Optimized for Raspberry Pi 3

import numpy as np
import cv2
import tflite_runtime.interpreter as tflite
import utils
from config import (
    DETECTION_MODEL_PATH,
    DETECTION_CONFIDENCE_THR,
    DETECTION_OVERLAP_THR,
    DETECTION_INPUT_SIZE,
    DETECTION_NUM_THREADS,
)

class FaceDetector:
    def __init__(self,
                 model=DETECTION_MODEL_PATH,
                 confidence_thr=DETECTION_CONFIDENCE_THR,
                 overlap_thr=DETECTION_OVERLAP_THR,
                 input_size=DETECTION_INPUT_SIZE,
                 num_threads=DETECTION_NUM_THREADS):
        """
        Initialize TFLite BlazeFace detector

        Args:
            model: Path to .tflite model file
            confidence_thr: Minimum confidence threshold for detections
            overlap_thr: NMS overlap threshold
            input_size: Model input size (width, height) - BlazeFace uses 128x128
            num_threads: Number of threads for TFLite inference
        """
        self.confidence_thr = confidence_thr
        self.overlap_thr = overlap_thr
        self.input_size = input_size

        # Load TFLite model
        self.interpreter = tflite.Interpreter(model_path=model, num_threads=num_threads)
        self.interpreter.allocate_tensors()

        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        print(f"[INFO] Model loaded: {model}")
        print(f"[INFO] Input shape: {self.input_details[0]['shape']}")
        print(f"[INFO] Output tensors: {len(self.output_details)}")

    def preprocess(self, image):
        """
        Preprocess image for BlazeFace model

        Args:
            image: BGR image (numpy array)

        Returns:
            Preprocessed tensor ready for inference
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize to model input size
        image_resized = cv2.resize(image_rgb, self.input_size)

        # Normalize to [-1, 1] and convert to float32 (STMicro model expects this range)
        image_normalized = (image_resized.astype(np.float32) / 127.5) - 1.0

        # Add batch dimension
        input_tensor = np.expand_dims(image_normalized, axis=0)

        return input_tensor

    def postprocess(self, outputs, image_shape):
        """
        Postprocess BlazeFace outputs

        BlazeFace outputs (MediaPipe task model):
        - Output 0: Bounding boxes [1, 896, 16] - anchor-encoded boxes
        - Output 1: Confidence scores [1, 896, 1]

        The box format has 16 values per box (y_center, x_center, h, w, + landmarks).
        Values are in 128x128 input space, need sigmoid and scaling.

        Args:
            outputs: Model output tensors
            image_shape: Original image shape (height, width)

        Returns:
            bboxes: Array of [x_min, y_min, x_max, y_max]
            scores: Array of confidence scores
        """
        boxes = outputs[0][0]  # [896, 16]
        scores = outputs[1][0]  # [896, 1]

        # Apply sigmoid to confidence scores
        scores = np.where(
            scores >= 0, 1 / (1 + np.exp(-scores)), np.exp(scores) / (1 + np.exp(scores))
        )

        # Filter by confidence threshold
        valid_indices = np.where(scores.flatten() > self.confidence_thr)[0]

        if len(valid_indices) == 0:
            return [], []

        valid_boxes = boxes[valid_indices]
        valid_scores = scores[valid_indices]

        # Decode boxes
        # Format: [y_center, x_center, height, width, ...landmarks]
        # Values are in 128x128 input space, need sigmoid and scaling
        h, w = image_shape[:2]
        decoded_boxes = []

        for i, box in enumerate(valid_boxes):
            # Apply sigmoid to first 4 values
            y_center = 1 / (1 + np.exp(-box[0]))
            x_center = 1 / (1 + np.exp(-box[1]))
            box_h = 1 / (1 + np.exp(-box[2]))
            box_w = 1 / (1 + np.exp(-box[3]))

            # Convert to absolute coordinates (normalized to image size)
            x_min = int(max(0, x_center * w - box_w * w / 2))
            y_min = int(max(0, y_center * h - box_h * h / 2))
            x_max = int(min(w, x_center * w + box_w * w / 2))
            y_max = int(min(h, y_center * h + box_h * h / 2))

            decoded_boxes.append([x_min, y_min, x_max, y_max])

        if len(decoded_boxes) == 0:
            return [], []

        decoded_boxes = np.array(decoded_boxes)

        # Apply NMS
        final_boxes, keep_indices = utils.non_max_suppression(
            decoded_boxes,
            overlapThresh=self.overlap_thr
        )
        final_scores = valid_scores[keep_indices]

        return final_boxes, final_scores

    def draw_bboxes(self, image, bboxes, color=(0, 255, 0)):
        """Draw bounding boxes on image (for visualization)"""
        for box in bboxes:
            x_min, y_min, x_max, y_max = box
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)

    def inference(self, image):
        """
        Run face detection inference
        
        Args:
            image: Input BGR image
            
        Returns:
            bboxes: Array of detected face boxes [x_min, y_min, x_max, y_max]
            scores: Array of confidence scores
        """
        # Preprocess
        input_tensor = self.preprocess(image)
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_tensor)
        
        # Run inference
        self.interpreter.invoke()
        
        # Get outputs
        outputs = []
        for output_detail in self.output_details:
            output = self.interpreter.get_tensor(output_detail['index'])
            outputs.append(output)
        
        # Postprocess
        image_shape = image.shape[:2]
        bboxes, scores = self.postprocess(outputs, image_shape)
        
        return bboxes, scores
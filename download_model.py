#!/usr/bin/env python3
"""
Download and prepare BlazeFace model for Raspberry Pi 3

This script downloads the BlazeFace model from MediaPipe and prepares it
for use with TensorFlow Lite Runtime on Raspberry Pi 3.
"""

import os
import sys
import urllib.request
import hashlib

def download_file(url, destination):
    """Download file from URL to destination with progress bar"""
    print(f"[INFO] Downloading from: {url}")
    print(f"[INFO] Saving to: {destination}")
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = (downloaded / total_size) * 100 if total_size > 0 else 0
        sys.stdout.write(f"\r[DOWNLOAD] {percent:.1f}% ({downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, destination, progress_hook)
        print("\n[INFO] Download complete!")
        return True
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        return False

def create_model_directory():
    """Create model directory if it doesn't exist"""
    model_dir = "model"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"[INFO] Created directory: {model_dir}")
    return model_dir

def download_blazeface_model():
    """
    Download BlazeFace TFLite model
    
    Note: For production use on Raspberry Pi 3, you should use:
    1. The official MediaPipe BlazeFace TFLite model
    2. OR convert to INT8 quantization using TensorFlow Lite Converter
    
    This script provides a placeholder - users should obtain the model
    from official MediaPipe sources.
    """
    model_dir = create_model_directory()
    model_path = os.path.join(model_dir, "blazeface_int8.tflite")
    
    # Official MediaPipe BlazeFace model URL from Google Storage
    # This is the standard BlazeFace short-range model from MediaPipe
    model_url = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
    
    print("=" * 60)
    print("BlazeFace Model Download for Raspberry Pi 3")
    print("=" * 60)
    print()
    print("NOTE: This downloads the standard BlazeFace model.")
    print("For optimal performance on Raspberry Pi 3, consider:")
    print("1. Using INT8 quantized version (requires TensorFlow model conversion)")
    print("2. Reducing input resolution if needed")
    print()
    
    if os.path.exists(model_path):
        print(f"[INFO] Model already exists: {model_path}")
        response = input("Do you want to re-download? (y/n): ")
        if response.lower() != 'y':
            print("[INFO] Using existing model")
            return model_path
    
    success = download_file(model_url, model_path)
    
    if success:
        print(f"[SUCCESS] Model downloaded to: {model_path}")
        print()
        print("Next steps:")
        print("1. Test the model: python src/main.py --raspi")
        print("2. If performance is slow, consider INT8 quantization")
        print()
        return model_path
    else:
        print("[ERROR] Failed to download model")
        print()
        print("Alternative: Manual download")
        print("1. Visit: https://github.com/google/mediapipe")
        print("2. Download BlazeFace TFLite model")
        print("3. Save as: model/blazeface_int8.tflite")
        return None

def main():
    """Main function"""
    print("=" * 60)
    print("BlazeFace Model Downloader")
    print("=" * 60)
    print()
    
    model_path = download_blazeface_model()
    
    if model_path:
        print(f"[SUCCESS] Model ready at: {model_path}")
        print()
        print("To run face tracking:")
        print("  On Raspberry Pi: python src/main.py --raspi")
        print("  On desktop: python src/main.py")
        return 0
    else:
        print("[ERROR] Model setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

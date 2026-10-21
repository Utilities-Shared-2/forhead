#!/bin/bash
# Setup script for Raspberry Pi 3 face tracking pipeline

set -e

echo "=========================================="
echo "Face Tracking Pipeline Setup"
echo "=========================================="
echo ""

# Detect if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(tr -d '\0' < /proc/device-tree/model)
    echo "Detected: $MODEL"
    IS_RASPI=true
else
    echo "Not running on Raspberry Pi (desktop mode)"
    IS_RASPI=false
fi

echo ""

# Install system dependencies
if [ "$IS_RASPI" = true ]; then
    echo "[1/4] Installing system dependencies..."
    sudo apt update
    sudo apt install -y python3-pip python3-dev libopencv-dev python3-opencv pigpio
else
    echo "[1/4] Skipping system dependencies (desktop mode)"
    echo "[1/4] Checking desktop dependencies..."
    # Desktop uses full tensorflow instead of tflite-runtime
    echo "[INFO] Desktop mode: Using full tensorflow package"
fi

echo ""

# Check for virtual environment
if [ -d "venv" ]; then
    echo "[2/4] Activating existing virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "[2/4] Activating existing virtual environment..."
    source .venv/bin/activate
elif [ -d "env" ]; then
    echo "[2/4] Activating existing virtual environment..."
    source env/bin/activate
else
    echo "[2/4] Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if [ "$IS_RASPI" = true ]; then
    pip install -r requirements-pi.txt
else
pip install -r requirements.txt
fi

echo ""

# Download model
echo "[3/4] Downloading BlazeFace model..."
python download_model.py --force

echo ""

if [ "$IS_RASPI" = true ]; then
    echo "[4/4] Starting pigpiod"
    # Start pigpiod service
    sudo systemctl start pigpiod
    sudo systemctl enable pigpiod
    echo "[INFO] Started pigpiod service"
else
    echo "[4/4] Skipping permissions setup (desktop mode)"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To run face tracking:"
if [ "$IS_RASPI" = true ]; then
    echo "  cd src && python3 main.py --raspi"
    echo "  (add --headless flag for SSH without VNC)"
else
    echo "  cd src && python3 main.py"
    echo "  (add --headless flag to disable GUI)"
fi
echo ""
echo "For more information, see README_MIGRATION.md"

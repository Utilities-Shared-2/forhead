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
fi

echo ""

# Install Python dependencies
echo "[2/4] Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""

# Download model
echo "[3/4] Downloading BlazeFace model..."
python3 download_model.py

echo ""

# Create model directory if it doesn't exist
if [ ! -d "model" ]; then
    mkdir -p model
    echo "[INFO] Created model directory"
fi

echo ""

# Set permissions
if [ "$IS_RASPI" = true ]; then
    echo "[4/4] Setting up permissions..."
    sudo usermod -a -G video $USER
    echo "[INFO] Added user to video group for camera access"
    echo "[INFO] You may need to log out and log back in for this to take effect"
    
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
else
    echo "  cd src && python3 main.py"
fi
echo ""
echo "For more information, see README_MIGRATION.md"

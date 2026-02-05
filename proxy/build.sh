#!/bin/bash
# Build script for Meshtastic Proxy GUI
#
# Usage: ./build.sh
#
# This script builds a standalone macOS application bundle that includes:
# - Python runtime
# - Qt GUI framework
# - All dependencies
# - Your proxy and AI handler code
#
# After modifying multi_client_proxy.py, proxy_gui.py, or ai_handler.py,
# run this script to rebuild the app with your changes.

echo "======================================"
echo "Meshtastic Proxy - Build Script"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Using Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install PyInstaller if not already installed
echo "Installing PyInstaller..."
pip install pyinstaller

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build the application
echo ""
echo "Building application..."
pyinstaller proxy_gui_onedir.spec

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "Build completed successfully!"
    echo "======================================"

    if [ "$(uname)" == "Darwin" ]; then
        echo "macOS Application Bundle: dist/MeshtasticProxy.app"
        echo "Executable Directory: dist/MeshtasticProxy/"
        echo ""
        echo "To run the app:"
        echo "  open dist/MeshtasticProxy.app"
        echo "  OR"
        echo "  ./dist/MeshtasticProxy/MeshtasticProxy"
    else
        echo "Executable Directory: dist/MeshtasticProxy/"
        echo ""
        echo "To run the app:"
        echo "  ./dist/MeshtasticProxy/MeshtasticProxy"
    fi
else
    echo ""
    echo "======================================"
    echo "Build failed!"
    echo "======================================"
    exit 1
fi

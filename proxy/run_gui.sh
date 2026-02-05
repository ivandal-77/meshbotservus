#!/bin/bash
# Launcher script for Meshtastic Proxy GUI

cd "$(dirname "$0")"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    echo ""
    echo "Setup complete!"
    echo ""
else
    source venv/bin/activate
fi

# Run the GUI
python3 proxy_gui.py

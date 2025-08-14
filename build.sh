#!/bin/bash

# This script builds the CoffeeCleaner application using PyInstaller.

# Exit immediately if a command exits with a non-zero status.
set -e


echo "--- Setting up virtual environment ---"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "--- Installing/updating build dependencies ---"
pip install --upgrade pyinstaller

echo "--- Building the application ---"
pyinstaller main.py \
    --name "CoffeeCleaner" \
    --windowed \
    --noconfirm \
    --clean \
    --icon "icon.icns"

echo "--- Build complete ---"
echo "The application bundle can be found in the 'dist' directory."


# Only sign if --sign is passed
if [[ "$1" == "--sign" ]]; then
    echo "--- Signing the .app bundle (development ad-hoc signature) ---"
    codesign --deep --force --sign - "dist/CoffeeCleaner.app"
    echo "--- Codesign complete ---"
else
    echo "--- Skipping codesign (no --sign flag) ---"
fi

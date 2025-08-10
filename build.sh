#!/bin/bash

# This script builds the Mac Cleaner & Analyzer application using PyInstaller.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Setting up virtual environment ---"
source venv/bin/activate

echo "--- Installing/updating build dependencies ---"
pip install --upgrade pyinstaller

echo "--- Building the application ---"
pyinstaller main.py \
    --name "Mac Cleaner & Analyzer" \
    --windowed \
    --noconfirm \
    --clean

echo "--- Build complete ---"
echo "The application bundle can be found in the 'dist' directory."

echo "--- Signing the .app bundle (development ad-hoc signature) ---"
codesign --deep --force --sign - "dist/Mac Cleaner & Analyzer.app"
echo "--- Codesign complete ---"

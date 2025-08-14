#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

SVG_FILE="icon.svg"
PNG_FILE="icon.png"
ICONSET_DIR="icon.iconset"
ICNS_FILE="icon.icns"

echo "--- Converting $SVG_FILE to $PNG_FILE ---"
rsvg-convert -w 1024 -h 1024 "$SVG_FILE" -o "$PNG_FILE"

echo "--- Creating temporary iconset directory ---"
mkdir "$ICONSET_DIR"

echo "--- Generating various PNG sizes for iconset ---"
sips -z 16 16   "$PNG_FILE" --out "$ICONSET_DIR/icon_16x16.png"
sips -z 32 32   "$PNG_FILE" --out "$ICONSET_DIR/icon_16x16@2x.png"
sips -z 32 32   "$PNG_FILE" --out "$ICONSET_DIR/icon_32x32.png"
sips -z 64 64   "$PNG_FILE" --out "$ICONSET_DIR/icon_32x32@2x.png"
sips -z 128 128 "$PNG_FILE" --out "$ICONSET_DIR/icon_128x128.png"
sips -z 256 256 "$PNG_FILE" --out "$ICONSET_DIR/icon_128x128@2x.png"
sips -z 256 256 "$PNG_FILE" --out "$ICONSET_DIR/icon_256x256.png"
sips -z 512 512 "$PNG_FILE" --out "$ICONSET_DIR/icon_256x256@2x.png"
sips -z 512 512 "$PNG_FILE" --out "$ICONSET_DIR/icon_512x512.png"
sips -z 1024 1024 "$PNG_FILE" --out "$ICONSET_DIR/icon_512x512@2x.png"

echo "--- Creating $ICNS_FILE from iconset ---"
iconutil -c icns "$ICONSET_DIR"

echo "--- Cleaning up temporary files ---"
rm "$PNG_FILE"
rm -rf "$ICONSET_DIR"

echo "--- $ICNS_FILE generated successfully! ---"
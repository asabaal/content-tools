#!/bin/bash
# Validate first 2 caption lines by frame extraction
# Line 1: "Where there was not" (visible after 0.859s)
# Line 2: "God's folk," (visible after 1.939s)

set -e

ROOT="/mnt/storage/repos/content-tools"
VIDEO="$ROOT/data/output/first_2_lines_manual.mp4"
OUTPUT_DIR="$ROOT/data/output/verification/first_2_lines"

mkdir -p "$OUTPUT_DIR"

echo "=== Extracting validation frames ==="

# Line 1: "Where there was not" - all visible at 1.0s
echo "Line 1: extracting at 1.0s..."
ffmpeg -y -ss 1.0 -i "$VIDEO" -frames:v 1 -q:v 2 "$OUTPUT_DIR/line1_full.png" 2>/dev/null

# Line 2: "God's folk," - all visible at 2.0s
echo "Line 2: extracting at 2.0s..."
ffmpeg -y -ss 2.0 -i "$VIDEO" -frames:v 1 -q:v 2 "$OUTPUT_DIR/line2_full.png" 2>/dev/null

# Additional: transition point where line 2 starts appearing
echo "Transition: extracting at 1.7s..."
ffmpeg -y -ss 1.7 -i "$VIDEO" -frames:v 1 -q:v 2 "$OUTPUT_DIR/transition.png" 2>/dev/null

echo ""
echo "=== Done ==="
echo "Frames saved to: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"

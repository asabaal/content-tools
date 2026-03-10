#!/bin/bash
# Render first 2 caption lines using two-pass method
# Line 1: "Where there was not"
# Line 2: "God's folk,"

set -e

ROOT="/mnt/storage/repos/content-tools"
OUTPUT_DIR="$ROOT/data/output"
CONCAT_LIST="$OUTPUT_DIR/concat_list.txt"
PASS2_FILTER="$OUTPUT_DIR/pass2_filter.txt"
ASSEMBLED="$OUTPUT_DIR/assembled.mp4"
OUTPUT="$OUTPUT_DIR/first_2_lines_manual.mp4"

echo "=== Pass 1: Timeline Assembly (concat demuxer) ==="
ffmpeg -y -f concat -safe 0 \
  -i "$CONCAT_LIST" \
  -c:v libx264 -preset fast -crf 18 \
  -c:a aac -b:a 128k \
  "$ASSEMBLED"

echo ""
echo "=== Pass 2: Caption Overlay ==="
ffmpeg -y -i "$ASSEMBLED" \
  -filter_complex_script "$PASS2_FILTER" \
  -map '[vout]' -map 0:a \
  -c:v libx264 -preset medium -crf 23 \
  -c:a copy \
  "$OUTPUT"

echo ""
echo "=== Done ==="
echo "Output: $OUTPUT"

#!/usr/bin/env bash
# Center-crop any aspect to 9:16, scale to 1080x1920 @ 30fps, strip audio.
# Usage: crop_to_9x16.sh <input.mp4> <output.mp4>
set -euo pipefail
IN="${1:?input required}"
OUT="${2:?output required}"

ffmpeg -y -i "$IN" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -an \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  "$OUT"
echo "wrote $OUT"

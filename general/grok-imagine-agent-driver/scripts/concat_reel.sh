#!/usr/bin/env bash
# Concat a list of normalised 1080x1920 mp4 shots into a single reel.
# Usage: concat_reel.sh <out.mp4> <shot1.mp4> <shot2.mp4> [...]
set -euo pipefail
OUT="${1:?output mp4 required}"; shift
[ "$#" -ge 1 ] || { echo "ERR: at least 1 shot required" >&2; exit 1; }

LIST=$(mktemp)
for f in "$@"; do
  printf "file '%s'\n" "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" >> "$LIST"
done

ffmpeg -y -f concat -safe 0 -i "$LIST" -c copy "$OUT"
rm -f "$LIST"
echo "wrote $OUT"
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 "$OUT"

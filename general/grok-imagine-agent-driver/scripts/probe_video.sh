#!/usr/bin/env bash
# Probe a downloaded video: dimensions, duration, codecs, audio presence; extract a mid-clip frame for judging.
# Usage: probe_video.sh <mp4-path>
set -euo pipefail
VID="${1:?mp4 path required}"
[ -f "$VID" ] || { echo "ERR: $VID not found" >&2; exit 1; }

ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,duration,r_frame_rate,channels,sample_rate -of default=noprint_wrappers=1 "$VID"

DUR=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 "$VID")
MID=$(python3 -c "print(round(float('$DUR')/2, 2))")
FRAME="${VID%.mp4}_frame.jpg"
ffmpeg -y -ss "$MID" -i "$VID" -frames:v 1 -q:v 2 "$FRAME" 2>/dev/null
echo "frame: $FRAME"

# Silence ratio — flag if speech-like audio present
echo "silence-density check:"
ffmpeg -i "$VID" -af silencedetect=n=-30dB:d=0.5 -f null - 2>&1 | grep -iE "silence_(start|end|duration)" | head -8

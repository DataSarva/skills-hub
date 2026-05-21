#!/bin/bash
# Validate a reel against Instagram Reels format requirements.
# Exit 0 = OK, 1 = at least one FAIL. Prints a per-field report.
set -u

VIDEO="${1:-}"
if [ -z "$VIDEO" ] || [ ! -f "$VIDEO" ]; then
  echo "Usage: validate_reel.sh <video.mp4>" >&2
  exit 2
fi

FAIL=0
ok () { echo "  OK    $1"; }
bad () { echo "  FAIL  $1"; FAIL=1; }

probe_v=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,pix_fmt,duration -of default=noprint_wrappers=1:nokey=0 "$VIDEO" 2>/dev/null)
probe_a=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=noprint_wrappers=1:nokey=0 "$VIDEO" 2>/dev/null)

vcodec=$(echo "$probe_v" | awk -F= '/^codec_name=/ {print $2}')
width=$(echo "$probe_v"  | awk -F= '/^width=/ {print $2}')
height=$(echo "$probe_v" | awk -F= '/^height=/ {print $2}')
pix_fmt=$(echo "$probe_v" | awk -F= '/^pix_fmt=/ {print $2}')
duration=$(echo "$probe_v" | awk -F= '/^duration=/ {print $2}')
acodec=$(echo "$probe_a" | awk -F= '/^codec_name=/ {print $2}')

echo "Validating: $VIDEO"
echo "----------------------------------------"
[ "$vcodec" = "h264" ] && ok "video codec = h264" || bad "video codec = '$vcodec' (want h264)"
[ "$pix_fmt" = "yuv420p" ] && ok "pixel format = yuv420p" || bad "pixel format = '$pix_fmt' (want yuv420p)"
[ "$width" = "1080" ] && [ "$height" = "1920" ] && ok "resolution = 1080x1920" || bad "resolution = ${width}x${height} (want 1080x1920)"

# Duration: 3 <= d <= 90
if [ -n "$duration" ]; then
  in_range=$(python3 -c "d=float('$duration'); print('1' if 3.0 <= d <= 90.0 else '0')" 2>/dev/null)
  if [ "$in_range" = "1" ]; then ok "duration = ${duration}s (3-90s)"; else bad "duration = ${duration}s (need 3-90s)"; fi
else
  bad "could not read duration"
fi

[ -n "$acodec" ] && ok "audio stream present (codec=$acodec)" || bad "no audio stream — IG rejects video-only mp4. Add silent AAC."
[ "$acodec" = "aac" ] || [ -z "$acodec" ] || bad "audio codec = '$acodec' (want aac)"

# faststart (moov atom at front)
faststart=$(ffmpeg -v trace -i "$VIDEO" 2>&1 | grep -m1 -c "moov\b.*0x" || true)
# Simpler: probe the first 1MB for `moov` tag
if head -c 1048576 "$VIDEO" | strings | grep -q "moov"; then
  ok "moov atom near front (faststart-friendly)"
else
  bad "moov atom not in first 1MB — re-encode with -movflags +faststart"
fi

echo "----------------------------------------"
if [ "$FAIL" -eq 0 ]; then
  echo "PASS — reel meets IG format requirements"
  exit 0
else
  echo "FAIL — fix issues above before uploading"
  exit 1
fi

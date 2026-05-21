#!/bin/bash
# Assemble N storyboard frames into a 9:16 Instagram reel with Ken Burns motion + crossfades.
# CONFIG: edit the 4 vars below per reel. Frames must be 1080x1920 jpg/png in <RUN_DIR>/storyboard_frames/frame_NN.jpg.
# OUTPUT: <RUN_DIR>/clips/shot_NN.mp4 + <RUN_DIR>/final/reel.mp4 (IG-ready, yuv420p, silent AAC).
set -euo pipefail

# ============================================================================
# CONFIG — customize per reel
# ============================================================================
RUN_DIR="${RUN_DIR:-$(pwd)}"
# frame_NN.jpg filenames in narrative order (NN = source frame number, not output shot number)
declare -a ORDER=(01 02 03 04)
# per-shot duration in seconds
declare -a DURS=(3.5 3.5 6 3)
# per-shot motion: in | out | down | up | left | right | static
declare -a ZOOMS=("in" "in" "down" "out")
# ============================================================================

SRC="$RUN_DIR/storyboard_frames"
CLIPS="$RUN_DIR/clips"
FINAL="$RUN_DIR/final"
mkdir -p "$CLIPS" "$FINAL"

W=1080; H=1920; FPS=30; XFADE=0.3
N=${#ORDER[@]}
[ "$N" -eq "${#DURS[@]}" ] || { echo "ORDER and DURS length mismatch" >&2; exit 1; }
[ "$N" -eq "${#ZOOMS[@]}" ] || { echo "ORDER and ZOOMS length mismatch" >&2; exit 1; }

build_clip () {
  local frame=$1 dur=$2 zoom=$3 out=$4
  local frames=$(python3 -c "print(int($dur * $FPS))")
  local zexpr xexpr yexpr
  case "$zoom" in
    in)     zexpr="min(zoom+0.0008,1.10)"; xexpr="iw/2-(iw/zoom/2)"; yexpr="ih/2-(ih/zoom/2)" ;;
    out)    zexpr="if(eq(on,0),1.10,max(zoom-0.0008,1.0))"; xexpr="iw/2-(iw/zoom/2)"; yexpr="ih/2-(ih/zoom/2)" ;;
    down)   zexpr="min(zoom+0.0005,1.08)"; xexpr="iw/2-(iw/zoom/2)"; yexpr="min(ih/2-(ih/zoom/2) + on*2, ih-ih/zoom)" ;;
    up)     zexpr="min(zoom+0.0005,1.08)"; xexpr="iw/2-(iw/zoom/2)"; yexpr="max(ih/2-(ih/zoom/2) - on*2, 0)" ;;
    left)   zexpr="min(zoom+0.0005,1.08)"; xexpr="max(iw/2-(iw/zoom/2) - on*2, 0)"; yexpr="ih/2-(ih/zoom/2)" ;;
    right)  zexpr="min(zoom+0.0005,1.08)"; xexpr="min(iw/2-(iw/zoom/2) + on*2, iw-iw/zoom)"; yexpr="ih/2-(ih/zoom/2)" ;;
    static) zexpr="1.0"; xexpr="iw/2-(iw/zoom/2)"; yexpr="ih/2-(ih/zoom/2)" ;;
    *) echo "unknown zoom direction: $zoom" >&2; return 1 ;;
  esac
  ffmpeg -y -loop 1 -framerate $FPS -i "$SRC/frame_${frame}.jpg" \
    -filter_complex "[0:v]scale=${W}*4:${H}*4:force_original_aspect_ratio=increase:out_range=tv,crop=${W}*4:${H}*4,zoompan=z='${zexpr}':x='${xexpr}':y='${yexpr}':d=${frames}:s=${W}x${H}:fps=${FPS},setrange=range=tv,format=yuv420p" \
    -t "$dur" -c:v libx264 -pix_fmt yuv420p -color_range tv -profile:v high -level 4.0 -preset medium -crf 18 \
    "$out" 2>/dev/null
  echo "  built $(basename "$out")  ($(ls -la "$out" | awk '{print $5}') bytes)"
}

echo "[1/3] Building $N per-shot clips with Ken Burns motion..."
SHOT=0
for i in "${!ORDER[@]}"; do
  SHOT=$((SHOT+1))
  PADDED=$(printf "%02d" $SHOT)
  build_clip "${ORDER[$i]}" "${DURS[$i]}" "${ZOOMS[$i]}" "$CLIPS/shot_${PADDED}.mp4"
done

echo "[2/3] Concatenating with ${XFADE}s crossfades..."
# Build the xfade filter chain dynamically.
INPUTS=""; FILTER=""; CUMOFF=0
for i in $(seq 1 $N); do
  PADDED=$(printf "%02d" $i)
  INPUTS+=" -i $CLIPS/shot_${PADDED}.mp4"
done

if [ "$N" -eq 1 ]; then
  cp "$CLIPS/shot_01.mp4" "$FINAL/reel_silent.mp4"
else
  PREV="[0:v]"
  for i in $(seq 1 $((N-1))); do
    # offset = cumulative duration of all prior shots minus (i * XFADE)
    PRIOR_SUM=0
    for j in $(seq 0 $((i-1))); do
      PRIOR_SUM=$(python3 -c "print($PRIOR_SUM + ${DURS[$j]})")
    done
    OFFSET=$(python3 -c "print(round($PRIOR_SUM - $i * $XFADE, 3))")
    if [ "$i" -lt $((N-1)) ]; then
      LABEL="[v$i]"
      FILTER+="${PREV}[$i:v]xfade=transition=fade:duration=${XFADE}:offset=${OFFSET}${LABEL};"
      PREV="$LABEL"
    else
      FILTER+="${PREV}[$i:v]xfade=transition=fade:duration=${XFADE}:offset=${OFFSET},format=yuv420p[outv]"
    fi
  done
  ffmpeg -y $INPUTS -filter_complex "$FILTER" -map "[outv]" \
    -c:v libx264 -profile:v high -level 4.0 -preset medium -crf 18 -pix_fmt yuv420p \
    "$FINAL/reel_silent.mp4" 2>/dev/null
fi
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL/reel_silent.mp4")
echo "  silent reel: $(basename "$FINAL/reel_silent.mp4")  ${DURATION}s"

echo "[3/3] Adding silent AAC track (Instagram requires audio stream)..."
ffmpeg -y -i "$FINAL/reel_silent.mp4" -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=44100" \
  -shortest -c:v copy -c:a aac -b:a 128k -movflags +faststart \
  "$FINAL/reel.mp4" 2>/dev/null

echo ""
echo "DONE."
echo "  final:      $FINAL/reel.mp4"
echo "  duration:   $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FINAL/reel.mp4")s"
echo "  size:       $(ls -la "$FINAL/reel.mp4" | awk '{print $5}') bytes"
echo "  resolution: $(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$FINAL/reel.mp4")"
echo ""
echo "Next: validate + upload"
echo "  bash ~/.skills-hub/general/instagram-reel-publish/scripts/validate_reel.sh $FINAL/reel.mp4"

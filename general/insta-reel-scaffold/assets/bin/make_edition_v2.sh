#!/usr/bin/env bash
# v2 edition: multi-clip-per-beat. fit clips to VO (VO_X) -> render (segments) -> foley -> hook -> IG.
# Usage: make_edition_v2.sh <male|female> <VO_X> <out_basename>   env: SHOW_KEYWORDS=0|1
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"   # project root = parent of bin/
G="${1:?male|female}"; VOX="${2:?VO_X}"; OUTB="${3:?out basename}"
AUD="$ROOT/audio_$G"; FA="$ROOT/final_audio_$G"; FC="$ROOT/final_clips_$G"
SHOTS_G="$ROOT/shots_v2_$G.json"; HOOK="$ROOT/hook/hook_conf.mp4"
cp "$ROOT/shots_v2.json" "$SHOTS_G"

echo "[$G@$VOX] 1/5 rebuild_v2 (multi-clip fit)"
SHOTS="$SHOTS_G" AUDIO_DIR="$AUD" FINAL_AUDIO="$FA" FINAL_CLIPS="$FC" SRC_DIR=clean_clips VO_X="$VOX" BREATH=0.15 \
  python3 "$ROOT/bin/rebuild_v2.py"
echo "[$G@$VOX] 2/5 timeline + render"
SHOTS="$SHOTS_G" TIMELINE="$ROOT/remotion/timeline.json" python3 "$ROOT/bin/gen_timeline_v2.py"
ln -sfn "../../final_audio_$G" "$ROOT/remotion/public/audio"
ln -sfn "../../final_clips_$G" "$ROOT/remotion/public/clips"
( cd "$ROOT/remotion" && npx remotion render Reel "out/tel_$G.mp4" --concurrency=2 2>&1 | tail -2 )
echo "[$G@$VOX] 3/5 foley"
python3 "$ROOT/bin/gen_sfx_cues.py" "$G" "$SHOTS_G" >/dev/null
python3 "$ROOT/bin/sfx_mix.py" "$ROOT/remotion/out/tel_$G.mp4" "$ROOT/music/bed.wav" "$ROOT/out/tel_${G}_foley.mp4" "$ROOT/sfx_cues_$G.json" >/dev/null
echo "[$G@$VOX] 4/5 prepend hook + encode"
ffmpeg -y -i "$HOOK" -i "$ROOT/out/tel_${G}_foley.mp4" \
  -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" \
  -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -color_range tv -r 30 -crf 19 -preset medium \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$ROOT/$OUTB.mp4" >/dev/null 2>&1
echo "[$G@$VOX] 5/5 DONE -> $OUTB.mp4 ($(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$ROOT/$OUTB.mp4")s)"

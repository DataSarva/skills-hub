#!/usr/bin/env bash
# Make the voiceover continuous across the whole reel: each shot's duration = its (sped) VO length
# + small breath, and the clean source clip is time-fitted to that length so motion maps onto the
# narration with no dead gaps (single setpts, no double-transform).
# Edition-aware (defaults = master/Instagram):
#   SHOTS (shots.json)  AUDIO_DIR (raw VO in, <root>/audio)  FINAL_AUDIO  FINAL_CLIPS
#   SRC_DIR (clean source clips; default clean_clips, fallback .src_clips)
#   VO_X (1.25)  BREATH (0.2)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
VO_X="${VO_X:-1.25}"; BREATH="${BREATH:-0.2}"
SHOTS="${SHOTS:-$ROOT/shots.json}"
AUDIO_DIR="${AUDIO_DIR:-$ROOT/audio}"
FINAL_AUDIO="${FINAL_AUDIO:-$ROOT/final_audio}"
FINAL_CLIPS="${FINAL_CLIPS:-$ROOT/final_clips}"
SRC_DIR="${SRC_DIR:-clean_clips}"; [ -d "$ROOT/$SRC_DIR" ] || SRC_DIR=".src_clips"
mkdir -p "$FINAL_CLIPS" "$FINAL_AUDIO"
dur(){ ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$1"; }

IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$SHOTS'))['shots']))")
for ID in $IDS; do
  RAW_VO="$AUDIO_DIR/shot$ID.mp3"; SRC="$ROOT/$SRC_DIR/shot$ID.mp4"
  FA="$FINAL_AUDIO/shot$ID.mp3"; FC="$FINAL_CLIPS/shot$ID.mp4"
  ffmpeg -y -i "$RAW_VO" -filter:a "atempo=$VO_X" "$FA" >/dev/null 2>&1
  VO=$(dur "$FA"); SRCLEN=$(dur "$SRC")
  TARGET=$(python3 -c "print(round($VO + $BREATH,3))")
  MULT=$(python3 -c "print(round($TARGET/$SRCLEN,5))")
  ffmpeg -y -i "$SRC" -filter:v "setpts=PTS*$MULT" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$FC" >/dev/null 2>&1
  echo "shot$ID: vo=${VO}s target=${TARGET}s srcClip=${SRCLEN}s mult=${MULT} -> $(dur "$FC")s"
done

python3 - "$SHOTS" "$FINAL_CLIPS" "$FINAL_AUDIO" <<'PY'
import json,os,subprocess,sys
p,fcd,fad=sys.argv[1],sys.argv[2],sys.argv[3]; d=json.load(open(p))
def dur(f): return round(float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f]).decode().strip()),3)
for s in d["shots"]:
    fc=os.path.join(fcd,f"shot{s['id']}.mp4"); fa=os.path.join(fad,f"shot{s['id']}.mp3")
    if os.path.exists(fc): s["dur"]=dur(fc)
    if os.path.exists(fa): s["vo_dur"]=dur(fa)
json.dump(d,open(p,"w"),ensure_ascii=False,indent=2)
print(f"total reel: {sum(s['dur'] for s in d['shots']):.1f}s, continuous VO sum: {sum(s.get('vo_dur',0) for s in d['shots']):.1f}s")
PY
echo "REBUILD DONE"

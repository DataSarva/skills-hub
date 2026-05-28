#!/usr/bin/env bash
# Post-process raw Flow clips -> final assets used by Remotion:
#   1) remove Veo watermark (reverse alpha blending)  2) speed video VID_X, drop native Gemini audio
#   3) speed Telugu VO VO_X (pitch-preserved)  4) recompute shots.json dur/vo_dur
# Resumable: skips shots whose final_clips/shotN.mp4 + final_audio/shotN.mp3 already exist.
# Usage: postprocess.sh   (env: VID_X=1.5 VO_X=1.25)
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
WM="$DIR/tools/veo_wmremove"
VID_X="${VID_X:-1.5}"; VO_X="${VO_X:-1.25}"
mkdir -p "$ROOT/final_clips" "$ROOT/final_audio" "$ROOT/.wm_tmp"

IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$ROOT/shots.json'))['shots']))")
for ID in $IDS; do
  RAW="$ROOT/clips/shot$ID.mp4"; FC="$ROOT/final_clips/shot$ID.mp4"; FA="$ROOT/final_audio/shot$ID.mp3"
  [ -f "$RAW" ] || { echo "shot$ID: no raw clip yet, skip"; continue; }
  if [ -f "$FC" ] && [ -f "$FA" ]; then echo "shot$ID: final exists, skip"; continue; fi

  # 1) watermark removal -> .wm_tmp/shotN.mp4
  CLEAN="$ROOT/.wm_tmp/shot$ID.mp4"
  if [ ! -f "$CLEAN" ]; then
    echo "shot$ID: removing watermark"
    "$WM" --no-banner -i "$RAW" -o "$CLEAN" >/dev/null 2>&1 || { echo "  WM failed, using raw"; cp "$RAW" "$CLEAN"; }
  fi
  # 2) speed video + drop audio
  echo "shot$ID: speed video x$VID_X (mute native audio)"
  ffmpeg -y -i "$CLEAN" -filter:v "setpts=PTS/$VID_X" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$FC" >/dev/null 2>&1
  # 3) speed VO (pitch-preserved)
  echo "shot$ID: speed VO x$VO_X"
  ffmpeg -y -i "$ROOT/audio/shot$ID.mp3" -filter:a "atempo=$VO_X" "$FA" >/dev/null 2>&1
done

# 4) recompute durations into shots.json (dur = final clip len, vo_dur = final vo len)
python3 - "$ROOT" <<'PY'
import json,os,subprocess,sys
root=sys.argv[1]; p=os.path.join(root,"shots.json"); d=json.load(open(p))
def dur(f): return round(float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f]).decode().strip()),3)
for s in d["shots"]:
    fc=os.path.join(root,"final_clips",f"shot{s['id']}.mp4"); fa=os.path.join(root,"final_audio",f"shot{s['id']}.mp3")
    if os.path.exists(fc): s["dur"]=dur(fc)
    if os.path.exists(fa): s["vo_dur"]=dur(fa)
json.dump(d,open(p,"w"),ensure_ascii=False,indent=2)
print("updated durs:",[(s["id"],s["dur"],s.get("vo_dur")) for s in d["shots"]])
PY
echo "POSTPROCESS DONE: $(ls "$ROOT/final_clips"/*.mp4 2>/dev/null | wc -l) clips"

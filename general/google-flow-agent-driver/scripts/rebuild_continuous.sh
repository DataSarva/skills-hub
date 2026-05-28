#!/usr/bin/env bash
# Make the voiceover continuous across the whole reel: each shot's duration = its (sped) VO length
# + small breath, and the clean source clip is time-fitted to that length so motion maps onto the
# narration with no dead gaps. Sources: audio/shotN.mp3 (raw TTS), .src_clips/shotN.mp4 (clean 1.5x).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
VO_X="${VO_X:-1.25}"; BREATH="${BREATH:-0.2}"
mkdir -p "$ROOT/final_clips" "$ROOT/final_audio"
dur(){ ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$1"; }

IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$ROOT/shots.json'))['shots']))")
for ID in $IDS; do
  RAW_VO="$ROOT/audio/shot$ID.mp3"; SRC="$ROOT/.src_clips/shot$ID.mp4"
  FA="$ROOT/final_audio/shot$ID.mp3"; FC="$ROOT/final_clips/shot$ID.mp4"
  # 1) speed VO (pitch-preserved)
  ffmpeg -y -i "$RAW_VO" -filter:a "atempo=$VO_X" "$FA" >/dev/null 2>&1
  VO=$(dur "$FA"); SRCLEN=$(dur "$SRC")
  TARGET=$(python3 -c "print(round($VO + $BREATH,3))")
  # 2) time-fit clean clip to TARGET (PTS multiplier = target/src), drop audio
  MULT=$(python3 -c "print(round($TARGET/$SRCLEN,5))")
  ffmpeg -y -i "$SRC" -filter:v "setpts=PTS*$MULT" -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$FC" >/dev/null 2>&1
  echo "shot$ID: vo=${VO}s target=${TARGET}s srcClip=${SRCLEN}s mult=${MULT} -> $(dur "$FC")s"
done

# write dur (=target=final clip len) + vo_dur into shots.json
python3 - "$ROOT" <<'PY'
import json,os,subprocess,sys
root=sys.argv[1]; p=os.path.join(root,"shots.json"); d=json.load(open(p))
def dur(f): return round(float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f]).decode().strip()),3)
for s in d["shots"]:
    fc=os.path.join(root,"final_clips",f"shot{s['id']}.mp4"); fa=os.path.join(root,"final_audio",f"shot{s['id']}.mp3")
    s["dur"]=dur(fc); s["vo_dur"]=dur(fa)
json.dump(d,open(p,"w"),ensure_ascii=False,indent=2)
tot=sum(s["dur"] for s in d["shots"])
print(f"total reel: {tot:.1f}s, continuous VO sum: {sum(s['vo_dur'] for s in d['shots']):.1f}s")
PY
echo "REBUILD DONE"

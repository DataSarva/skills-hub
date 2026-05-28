#!/usr/bin/env bash
# TTS every shot's narration_te -> audio/shotN.mp3 (eve voice), write vo durations back into shots.json.
# Run under: iex contentgen -- bash bin/tts_all.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
export XAI_API_KEY="${XAI_API_KEY:-$GROK_API_KEY}"
VOICE="${VOICE:-eve}"; LANG="${LANG:-te}"
mkdir -p "$ROOT/audio"

IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$ROOT/shots.json'))['shots']))")
for ID in $IDS; do
  python3 -c "import json;print([s['narration_te'] for s in json.load(open('$ROOT/shots.json'))['shots'] if s['id']==$ID][0])" > "/tmp/gaj_n_$ID.txt"
  bash "$DIR/tts.sh" "/tmp/gaj_n_$ID.txt" "$ROOT/audio/shot$ID.mp3" "$VOICE" "$LANG"
done

# write vo_dur back into shots.json
python3 - "$ROOT" <<'PY'
import json,subprocess,os,sys
root=sys.argv[1]; p=os.path.join(root,"shots.json"); d=json.load(open(p))
for s in d["shots"]:
    f=os.path.join(root,"audio",f"shot{s['id']}.mp3")
    if os.path.exists(f):
        s["vo_dur"]=round(float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f]).decode().strip()),3)
json.dump(d,open(p,"w"),ensure_ascii=False,indent=2)
print("vo durations:",[ (s["id"],s.get("vo_dur")) for s in d["shots"] ])
PY
echo "TTS ALL DONE"

#!/usr/bin/env bash
# TTS every shot's narration_te -> AUDIO_DIR/shotN.mp3 (eve voice); write raw vo durations into SHOTS.
# Edition-aware: SHOTS (default shots.json), AUDIO_DIR (default <root>/audio). Defaults = master (IG).
# Run under: iex contentgen -- bash bin/tts_all.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
export XAI_API_KEY="${XAI_API_KEY:-$GROK_API_KEY}"
VOICE="${VOICE:-eve}"; LANG="${LANG:-te}"
SHOTS="${SHOTS:-$ROOT/shots.json}"; AUDIO_DIR="${AUDIO_DIR:-$ROOT/audio}"
mkdir -p "$AUDIO_DIR"

IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$SHOTS'))['shots']))")
for ID in $IDS; do
  python3 -c "import json;print([s['narration_te'] for s in json.load(open('$SHOTS'))['shots'] if s['id']==$ID][0])" > "/tmp/gaj_n_$ID.txt"
  bash "$DIR/tts.sh" "/tmp/gaj_n_$ID.txt" "$AUDIO_DIR/shot$ID.mp3" "$VOICE" "$LANG"
done

python3 - "$SHOTS" "$AUDIO_DIR" <<'PY'
import json,subprocess,os,sys
p=sys.argv[1]; ad=sys.argv[2]; d=json.load(open(p))
for s in d["shots"]:
    f=os.path.join(ad,f"shot{s['id']}.mp3")
    if os.path.exists(f):
        s["vo_dur"]=round(float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nk=1:nw=1",f]).decode().strip()),3)
json.dump(d,open(p,"w"),ensure_ascii=False,indent=2)
print("vo durations:",[ (s["id"],s.get("vo_dur")) for s in d["shots"] ])
PY
echo "TTS ALL DONE"

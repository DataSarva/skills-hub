#!/usr/bin/env bash
# Authentic Telugu VO via Google Cloud TTS (native te-IN Chirp3-HD voices).
# Usage: cloud_tts.sh <text_file> <out_mp3> [voice=te-IN-Chirp3-HD-Leda] [rate=1.05]
set -euo pipefail
TXT="${1:?}"; OUT="${2:?}"; VOICE="${3:-te-IN-Chirp3-HD-Leda}"; RATE="${4:-1.05}"
GP="${GOOGLE_TTS_PROJECT:-aisarva-flash-demo-4020}"
TOKEN=$(gcloud auth print-access-token 2>/dev/null)
mkdir -p "$(dirname "$OUT")"
python3 - "$TXT" "$OUT" "$VOICE" "$RATE" "$TOKEN" "$GP" <<'PY'
import sys,json,base64,urllib.request,urllib.error
txtf,out,voice,rate,tok,proj=sys.argv[1:7]
txt=open(txtf,encoding="utf-8").read()
body=json.dumps({"input":{"text":txt},"voice":{"languageCode":"te-IN","name":voice},
  "audioConfig":{"audioEncoding":"MP3","speakingRate":float(rate)}}).encode()
req=urllib.request.Request("https://texttospeech.googleapis.com/v1/text:synthesize",data=body,
  headers={"Authorization":f"Bearer {tok}","x-goog-user-project":proj,"Content-Type":"application/json"})
try:
  r=json.load(urllib.request.urlopen(req)); open(out,"wb").write(base64.b64decode(r["audioContent"]))
except urllib.error.HTTPError as e:
  sys.stderr.write(f"TTS ERR {e.code}: {e.read().decode()[:200]}\n"); sys.exit(1)
PY
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OUT"

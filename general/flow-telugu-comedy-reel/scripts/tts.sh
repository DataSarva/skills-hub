#!/usr/bin/env bash
# tts.sh <text_file> <out_mp3> [voice=Leo] [lang=te]  — funny Telugu VO via xAI TTS
set -euo pipefail
TXT="${1:?}"; OUT="${2:?}"; VOICE="${3:-Leo}"; LANG="${4:-te}"
: "${XAI_API_KEY:?set XAI_API_KEY}"; mkdir -p "$(dirname "$OUT")"
BODY=$(python3 - "$TXT" "$VOICE" "$LANG" <<'PY'
import sys, json
print(json.dumps({"text": open(sys.argv[1], encoding="utf-8").read(),
  "voice_id": sys.argv[2], "language": sys.argv[3],
  "output_format": {"codec":"mp3","sample_rate":44100,"bit_rate":192000}}))
PY
)
H=$(curl -s -w "%{http_code}" -X POST https://api.x.ai/v1/tts \
  -H "Authorization: Bearer $XAI_API_KEY" -H "Content-Type: application/json" \
  -d "$BODY" --output "$OUT")
[ "$H" = 200 ] || { echo "HTTP $H: $(head -c 300 "$OUT")" >&2; exit 1; }
ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OUT"

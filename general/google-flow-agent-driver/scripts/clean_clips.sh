#!/usr/bin/env bash
# Stage: watermark removal only. raw clips/shotN.mp4 -> clean_clips/shotN.mp4 (Veo "✦" removed,
# NO speed change — timing is decided later by rebuild_continuous so motion isn't double-transformed).
# Resumable. See the veo-watermark-remover skill for the binary.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
WM="${WM_BIN:-$DIR/tools/veo_wmremove}"
mkdir -p "$ROOT/clean_clips"
IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$ROOT/shots.json'))['shots']))")
for ID in $IDS; do
  RAW="$ROOT/clips/shot$ID.mp4"; OUT="$ROOT/clean_clips/shot$ID.mp4"
  [ -f "$RAW" ] || { echo "shot$ID: no raw clip, skip"; continue; }
  [ -f "$OUT" ] && { echo "shot$ID: clean exists, skip"; continue; }
  echo "shot$ID: removing watermark"
  "$WM" --no-banner -i "$RAW" -o "$OUT" >/dev/null 2>&1 || { echo "  WM failed, copying raw"; cp "$RAW" "$OUT"; }
done
echo "CLEAN DONE: $(ls "$ROOT/clean_clips"/*.mp4 2>/dev/null|wc -l) clips"

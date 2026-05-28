#!/usr/bin/env bash
# Build timeline.json from shots.json then render the final 1080x1920 reel.
# Telugu subtitles (Remotion + Noto Sans Telugu) + per-shot VO + music bed. Clips are muted.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
python3 "$DIR/gen_timeline.py"
cd "$ROOT/remotion"
npx remotion render Reel out/gajendra.mp4 --concurrency=2
echo "RENDERED: $ROOT/remotion/out/gajendra.mp4"

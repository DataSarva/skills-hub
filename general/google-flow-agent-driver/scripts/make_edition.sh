#!/usr/bin/env bash
# Build a DERIVED edition (e.g. a <60s YouTube cut) WITHOUT touching the master (shots.json / IG reel).
# Reuses the already-generated clean source clips (clean_clips/ or .src_clips/) — no Flow re-gen.
# Usage: make_edition.sh <edition_name> <shots_file>   e.g. make_edition.sh yt60 shots.yt60.json
# Env knobs: VO_X (1.15 good for YT), BREATH (0.2)
set -euo pipefail
ED="${1:?edition name}"; SHOTS_REL="${2:?shots file}"
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
SHOTS="$ROOT/$SHOTS_REL"; [ -f "$SHOTS" ] || SHOTS="$SHOTS_REL"
EDDIR="$ROOT/editions/$ED"
export AUDIO_DIR="$EDDIR/audio" FINAL_AUDIO="$EDDIR/final_audio" FINAL_CLIPS="$EDDIR/final_clips" SHOTS
export VO_X="${VO_X:-1.15}" BREATH="${BREATH:-0.2}"
mkdir -p "$AUDIO_DIR" "$FINAL_AUDIO" "$FINAL_CLIPS"

echo "=== [$ED] VO ==="; iex contentgen -- bash "$DIR/tts_all.sh"
echo "=== [$ED] continuous fit ==="; bash "$DIR/rebuild_continuous.sh"

echo "=== [$ED] render ==="
# point the comp's public assets at this edition, render, then restore to master
rm -f "$ROOT/remotion/public/clips" "$ROOT/remotion/public/audio"
ln -sf "../../editions/$ED/final_clips" "$ROOT/remotion/public/clips"
ln -sf "../../editions/$ED/final_audio" "$ROOT/remotion/public/audio"
SHOTS="$SHOTS" TIMELINE="$ROOT/remotion/timeline.json" python3 "$DIR/gen_timeline.py"
(cd "$ROOT/remotion" && mkdir -p out && npx remotion render Reel "out/$ED.mp4" --concurrency=2)
cp "$ROOT/remotion/out/$ED.mp4" "$ROOT/reel_$ED.mp4"
# restore master symlinks so the IG/master render still works
rm -f "$ROOT/remotion/public/clips" "$ROOT/remotion/public/audio"
ln -sf "../../final_clips" "$ROOT/remotion/public/clips"
ln -sf "../../final_audio" "$ROOT/remotion/public/audio"
echo "EDITION DONE: $ROOT/reel_$ED.mp4 ($(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$ROOT/reel_$ED.mp4")s)"

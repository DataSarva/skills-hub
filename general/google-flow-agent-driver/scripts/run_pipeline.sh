#!/usr/bin/env bash
# ============================================================================
#  Google Flow reel — production pipeline orchestrator (canonical template)
#  Model-version-agnostic: works for any Gemini/Veo video model exposed in
#  Flow's settings popover (Omni Flash today; pick the latest there in future).
#
#  Usage:
#    bin/run_pipeline.sh <PROFILE> <PROJECT_URL> [stage]
#      stage = all (default) | preflight | characters | clips | tts | clean | assemble | render
#  Env knobs: VO_X (1.25) BREATH (0.2)
#  Prereqs: opencli bridge signed into labs.google/fx (Veo access); shots.json authored;
#           Flow Characters' @handles match shots.json; veo_wmremove in bin/tools/;
#           remotion deps installed (cd remotion && npm i); iex 'contentgen' for xAI TTS key.
# ============================================================================
set -euo pipefail
PROFILE="${1:?profile alias}"; PROJ="${2:?project url}"; STAGE="${3:-all}"
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
run(){ echo; echo "===== STAGE: $1 ====="; }

if [ "$STAGE" = all ] || [ "$STAGE" = preflight ]; then run preflight
  opencli doctor; opencli --profile "$PROFILE" profile list || true
fi
if [ "$STAGE" = all ] || [ "$STAGE" = characters ]; then run "characters (identity gate — review before clips)"
  bash "$DIR/build_characters.sh" "$PROFILE" "$PROJ"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = clips ]; then run "clips (text-free, @name refs, resumable)"
  bash "$DIR/gen_all_clips.sh" "$PROFILE" "$PROJ"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = tts ]; then run "Telugu VO (xAI eve)"
  iex contentgen -- bash "$DIR/tts_all.sh"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = clean ]; then run "watermark removal (Veo ✦ -> clean_clips/)"
  bash "$DIR/clean_clips.sh"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = assemble ]; then run "continuous VO + fit clips to narration"
  bash "$DIR/rebuild_continuous.sh"
fi
if [ "$STAGE" = all ] || [ "$STAGE" = render ]; then run "timeline + Remotion render (1080x1920)"
  python3 "$DIR/gen_timeline.py"
  (cd "$ROOT/remotion" && mkdir -p out && npx remotion render Reel out/reel.mp4 --concurrency=2)
  cp "$ROOT/remotion/out/reel.mp4" "$ROOT/reel_FINAL.mp4"
  echo "FINAL: $ROOT/reel_FINAL.mp4"
fi
echo; echo "pipeline stage '$STAGE' complete."

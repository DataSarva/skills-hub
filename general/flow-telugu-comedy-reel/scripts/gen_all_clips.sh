#!/usr/bin/env bash
# Generate + download all shot clips from shots.json (resumable: skips existing clips/shotN.mp4).
# Usage: gen_all_clips.sh <profile> <project_url>
set -euo pipefail
PROFILE="${1:?profile}"; PROJ="${2:?project url}"
DIR="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$DIR")"
LEAD="Animated comedy film scene. "   # ensures prompt never starts with '@' (Slate mention-mode guard)

# ensure on project root + direct mode (Agent off)
opencli --profile "$PROFILE" browser open "$PROJ" >/dev/null 2>&1; sleep 3
opencli --profile "$PROFILE" browser eval '(() => {
  function fire(el){const r=el.getBoundingClientRect();const o={bubbles:true,cancelable:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2,button:0,pointerId:1,pointerType:"mouse",isPrimary:true};["pointerdown","mousedown","pointerup","mouseup","click"].forEach(t=>el.dispatchEvent(t.startsWith("pointer")?new PointerEvent(t,o):new MouseEvent(t,o)));}
  const chip=[...document.querySelectorAll("button[aria-haspopup=menu]")].find(x=>/Video|Banana|Image/.test(x.innerText));
  if(!chip){const ag=[...document.querySelectorAll("button")].find(b=>(b.innerText||"").trim()==="Agent"); if(ag)fire(ag);}
  return "direct mode";
})()' >/dev/null 2>&1; sleep 1

IDS=$(python3 -c "import json;print(' '.join(str(s['id']) for s in json.load(open('$ROOT/shots.json'))['shots']))")
for ID in $IDS; do
  OUT="$ROOT/clips/shot$ID.mp4"
  if [ -f "$OUT" ]; then echo "=== shot$ID exists, skip ==="; continue; fi
  DUR=8   # Flow only accepts 4/6/8/10s; continuous-VO rebuild time-fits each clip to its VO line
  PROMPT=$(python3 -c "import json;print([s['video_prompt'] for s in json.load(open('$ROOT/shots.json'))['shots'] if s['id']==$ID][0])")
  echo "=== shot$ID (dur=$DUR) ==="
  bash "$DIR/flow_gen_clip.sh" "$PROFILE" "$PROJ" "$ID" "$DUR" "$OUT" "$LEAD$PROMPT" || echo "!!! shot$ID FAILED (continue)"
done
echo "ALL CLIPS DONE: $(ls "$ROOT/clips"/*.mp4 2>/dev/null | wc -l) files"

#!/usr/bin/env bash
# Generate ONE Flow video clip (Omni Flash, direct mode) and download it.
# Usage: flow_gen_clip.sh <profile> <project_url> <id> <dur> <out_mp4> <prompt...>
# Prompt MUST NOT start with '@' (Slate eats a leading @ as a mention query). Caller prepends a lead-in.
set -euo pipefail
PROFILE="${1:?profile}"; PROJ="${2:?project url}"; ID="${3:?id}"; DUR="${4:?dur}"; OUT="${5:?out}"; shift 5; PROMPT="$*"

oc(){ opencli --profile "$PROFILE" browser "$@"; }
FIRE='function fire(el){const r=el.getBoundingClientRect();const o={bubbles:true,cancelable:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2,button:0,pointerId:1,pointerType:"mouse",isPrimary:true};["pointerdown","mousedown","pointerup","mouseup","click"].forEach(t=>el.dispatchEvent(t.startsWith("pointer")?new PointerEvent(t,o):new MouseEvent(t,o)));}'

echo "[shot$ID] set Video/9:16/${DUR}s/1x"
# open settings chip (matches icon-prefixed label e.g. "🍌 Nano Banana 2" or "Video · 8s")
oc eval "(() => { $FIRE const c=[...document.querySelectorAll('button[aria-haspopup=menu]')].find(x=>/Video|Banana|Image|Omni|Flash|Veo/.test(x.innerText)); if(c)fire(c); return 'open'; })()" >/dev/null 2>&1
sleep 1
# STEP 1: switch to Video mode (durations only appear after this). Labels are "icon\nLabel" -> normalize \n to |, regex match.
oc eval "(() => { $FIRE const m=document.querySelector('[role=menu]')||document.querySelector('[data-radix-menu-content]'); if(!m)return 'no panel'; const els=[...m.querySelectorAll('button,[role=menuitem],[role=menuitemradio],[role=radio]')]; const v=els.find(x=>/(^|\|)Video\$/.test((x.innerText||'').trim().replace(/\n/g,'|'))); if(v)fire(v); return 'video'; })()" >/dev/null 2>&1
sleep 1
# STEP 2: pick aspect 9:16, duration, count 1x (menu re-rendered; re-query)
oc eval "(() => { $FIRE const m=document.querySelector('[role=menu]')||document.querySelector('[data-radix-menu-content]'); if(!m)return 'no panel'; const els=[...m.querySelectorAll('button,[role=menuitem],[role=menuitemradio],[role=radio]')]; const N=x=>(x.innerText||'').trim().replace(/\n/g,'|'); const pick=re=>{const e=els.find(x=>re.test(N(x))); if(e){fire(e);return true} return false}; pick(/9_16|9:16/); pick(/(^|\|)${DUR}s\$/); pick(/(^|\|)1x\$/); return 'set'; })()" >/dev/null 2>&1
oc keys Escape >/dev/null 2>&1; sleep 0.4

# count finished clips before
BEFORE=$(oc eval '(()=>[...document.querySelectorAll("video")].filter(v=>/media/.test(v.src||v.currentSrc||"")).length)()' 2>/dev/null | head -1)
echo "[shot$ID] ready clips before: $BEFORE"

echo "[shot$ID] type prompt + submit"
oc type "div[contenteditable=true]" "$PROMPT" >/dev/null 2>&1; sleep 1
oc eval "(() => { $FIRE const b=[...document.querySelectorAll('button')].find(x=>{const i=x.querySelector('i');const r=x.getBoundingClientRect();return i&&i.innerText.trim()==='arrow_forward'&&r.y>650}); if(b){fire(b);return 'submitted'} return 'no submit'; })()" >/dev/null 2>&1

echo "[shot$ID] poll for completion"
DONE=0
for i in $(seq 1 24); do
  sleep 15
  R=$(oc eval '(()=>{const pct=(document.body.innerText.match(/\d+%/)||[])[0]||""; const ready=[...document.querySelectorAll("video")].filter(v=>/media/.test(v.src||v.currentSrc||"")).length; return JSON.stringify({pct,ready});})()' 2>/dev/null | head -1)
  echo "  poll $i: $R"
  if echo "$R" | grep -q '"pct":""' && [ "$(echo "$R" | sed -E 's/.*"ready":([0-9]+).*/\1/')" -gt "$BEFORE" ]; then DONE=1; break; fi
done
[ "$DONE" = 1 ] || { echo "[shot$ID] TIMEOUT"; exit 2; }

echo "[shot$ID] download newest"
BEFORE_FILES=$(ls -t "$HOME/Downloads"/*.mp4 2>/dev/null | head -1 || true)
oc eval "(() => { $FIRE fire(document.querySelector('video')); return 'opened'; })()" >/dev/null 2>&1; sleep 2
oc eval "(() => { $FIRE const dl=[...document.querySelectorAll('button')].find(b=>{const i=b.querySelector('i');return i&&i.innerText.trim()==='download'}); if(dl){fire(dl);return 'dl'} return 'no dl'; })()" >/dev/null 2>&1
sleep 5
NEW=""
for t in 1 2 3 4 5; do
  NEW=$(ls -t "$HOME/Downloads"/*.mp4 2>/dev/null | head -1)
  [ "$NEW" != "$BEFORE_FILES" ] && [ -n "$NEW" ] && break
  sleep 2
done
[ -n "$NEW" ] && [ "$NEW" != "$BEFORE_FILES" ] || { echo "[shot$ID] download failed"; exit 3; }
mkdir -p "$(dirname "$OUT")"; mv "$NEW" "$OUT"   # move (not copy) so nothing piles up in ~/Downloads
oc keys Escape >/dev/null 2>&1
echo "[shot$ID] saved $OUT ($(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OUT")s)"

#!/usr/bin/env bash
# Create one Flow native Character (image base via Nano Banana) and name it.
# Usage: flow_make_character.sh <profile> <project_url> <name> <description>
# Identity is reused later by typing @<name> in scene prompts.
set -euo pipefail
PROFILE="${1:?profile}"; PROJ="${2:?project url}"; NAME="${3:?name}"; DESC="${4:?description}"

oc(){ opencli --profile "$PROFILE" browser "$@"; }

# pointer-event fire helper (Radix/Flow buttons ignore synthetic .click())
FIRE='function fire(el){const r=el.getBoundingClientRect();const o={bubbles:true,cancelable:true,clientX:r.x+r.width/2,clientY:r.y+r.height/2,button:0,pointerId:1,pointerType:"mouse",isPrimary:true};["pointerdown","mousedown","pointerup","mouseup","click"].forEach(t=>el.dispatchEvent(t.startsWith("pointer")?new PointerEvent(t,o):new MouseEvent(t,o)));}'

echo "[$NAME] open characters page"
oc open "$PROJ/characters" >/dev/null 2>&1; sleep 3

echo "[$NAME] type description + submit"
oc type "div[contenteditable=true]" "$DESC" >/dev/null 2>&1; sleep 0.5
oc click "div[contenteditable=true]" >/dev/null 2>&1; sleep 0.3
oc keys Enter >/dev/null 2>&1

echo "[$NAME] wait for base image"
for i in $(seq 1 18); do
  sleep 8
  R=$(oc eval '(() => {
    const editorOpen=[...document.querySelectorAll("input")].some(e=>e.value==="Untitled Character"||e.value==="'"$NAME"'");
    const media=[...document.querySelectorAll("img")].filter(m=>/media|googleuser/.test(m.src||"")).length;
    return JSON.stringify({editorOpen,media});
  })()' 2>/dev/null | head -1)
  echo "  poll $i: $R"
  echo "$R" | grep -q '"editorOpen":true' && echo "$R" | grep -qE '"media":[1-9]' && break
done

echo "[$NAME] set name + Done"
oc eval '(() => {
  const inp=[...document.querySelectorAll("input")].find(e=>e.value==="Untitled Character");
  if(inp){const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,"value").set;s.call(inp,"'"$NAME"'");inp.dispatchEvent(new Event("input",{bubbles:true}));inp.dispatchEvent(new Event("change",{bubbles:true}));inp.blur();}
  return "named "+(inp?inp.value:"?");
})()' >/dev/null 2>&1
sleep 0.6
oc eval "(() => { $FIRE const d=[...document.querySelectorAll('button')].find(b=>(b.innerText||'').trim()==='Done'); if(d){fire(d);return 'done';} return 'no done btn'; })()" >/dev/null 2>&1
sleep 3
echo "[$NAME] created"

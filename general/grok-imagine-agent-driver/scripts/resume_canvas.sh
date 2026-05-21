#!/usr/bin/env bash
# Resume an in-progress Grok Imagine canvas after a Chrome tab recycle.
# Navigates to imagine, toggles Agent (Beta), finds the canvas with a matching title fragment, clicks it.
# Usage: resume_canvas.sh <profile> <title-fragment>
# Example: resume_canvas.sh mxtkmkyn "Reference sheet"
set -euo pipefail
PROFILE="${1:?profile alias required}"
FRAGMENT="${2:?title fragment required}"

opencli --profile "$PROFILE" browser open https://grok.com/imagine >/dev/null 2>&1
sleep 4

# Toggle Agent (Beta) to show canvas gallery
opencli --profile "$PROFILE" browser eval '(() => { const t = Array.from(document.querySelectorAll("button")).filter(b => b.offsetParent !== null).find(b => (b.textContent||"").trim() === "Agent (Beta)"); if (!t) return "AGENT_NOT_FOUND"; t.click(); return "ok"; })()' >/dev/null 2>&1
sleep 3

# Find topmost (most recent) canvas with matching title fragment, walk up parents to clickable element, click
FRAG_JSON=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$FRAGMENT")
opencli --profile "$PROFILE" browser eval "(() => { const span = Array.from(document.querySelectorAll('span')).filter(e => e.offsetParent !== null && (e.textContent||'').includes($FRAG_JSON)).sort((a,b) => a.getBoundingClientRect().y - b.getBoundingClientRect().y)[0]; if (!span) return 'NO_MATCH'; let p = span; for (let i = 0; i < 10; i++) { p = p.parentElement; if (!p) break; if (p.onclick || p.tagName === 'BUTTON' || p.tagName === 'A' || p.getAttribute('role') === 'button') { p.click(); return 'clicked'; } } span.click(); return 'fallback_clicked'; })()" >/dev/null 2>&1
sleep 4

# Verify composer present
opencli --profile "$PROFILE" browser eval '(() => { const c = Array.from(document.querySelectorAll("div[contenteditable=true]")).filter(e => e.offsetParent !== null)[0]; const url = location.href; return c && c.editor ? `READY ${url}` : `NO_COMPOSER ${url}`; })()' 2>&1 | grep -oE "READY|NO_COMPOSER" | head -1

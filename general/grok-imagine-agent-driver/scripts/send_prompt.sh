#!/usr/bin/env bash
# Inject prompt text into the ProseMirror composer and click Send.
# Usage: send_prompt.sh <opencli-profile-alias> <prompt-file>
set -euo pipefail
PROFILE="${1:?profile alias required}"
PROMPT_FILE="${2:?prompt file required}"

PROMPT_JSON=$(python3 -c "import sys,json; print(json.dumps(open('$PROMPT_FILE').read()))")

opencli --profile "$PROFILE" browser eval "(() => { const c = Array.from(document.querySelectorAll('div[contenteditable=true]')).filter(e => e.offsetParent !== null)[0]; if (!c) return 'NO_COMPOSER'; const e = c.editor; if (!e) return 'NO_EDITOR_API'; e.commands.focus(); e.commands.clearContent(); e.commands.insertContent($PROMPT_JSON); return { len: c.textContent.length }; })()" 2>&1 | grep -oE '"len":\s*[0-9]+' | head -1

opencli --profile "$PROFILE" browser eval '(() => { const b = Array.from(document.querySelectorAll("button[aria-label=\"Send\"]")).filter(b => b.offsetParent !== null && !b.disabled)[0]; if (!b) return "NO_SEND_BTN"; b.click(); return "sent"; })()' 2>&1 | grep -oE "sent|NO_SEND_BTN" | head -1

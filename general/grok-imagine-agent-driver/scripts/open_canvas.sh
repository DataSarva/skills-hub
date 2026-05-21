#!/usr/bin/env bash
# Open grok.com/imagine, toggle Agent (Beta), click + Empty Canvas.
# Usage: open_canvas.sh <opencli-profile-alias>
set -euo pipefail
PROFILE="${1:?profile alias required}"

opencli --profile "$PROFILE" browser open https://grok.com/imagine >/dev/null 2>&1
sleep 4

# Click Agent (Beta) toggle on landing
opencli --profile "$PROFILE" browser eval '(() => { const t = Array.from(document.querySelectorAll("button")).filter(b => b.offsetParent !== null).find(b => (b.textContent||"").trim() === "Agent (Beta)"); if (!t) return "AGENT_BUTTON_NOT_FOUND"; t.click(); return "agent_toggled"; })()' >/dev/null 2>&1
sleep 2

# Click + Empty Canvas
opencli --profile "$PROFILE" browser eval '(() => { const t = Array.from(document.querySelectorAll("button")).filter(b => b.offsetParent !== null).find(b => (b.textContent||"").trim().includes("Empty Canvas")); if (!t) return "EMPTY_CANVAS_NOT_FOUND"; t.click(); return "canvas_opened"; })()' >/dev/null 2>&1
sleep 3

# Verify composer present
opencli --profile "$PROFILE" browser eval '(() => { const c = Array.from(document.querySelectorAll("div[contenteditable=true]")).filter(e => e.offsetParent !== null)[0]; return c ? "READY" : "NO_COMPOSER"; })()' 2>&1 | grep -oE "READY|NO_COMPOSER" | head -1

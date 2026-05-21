#!/usr/bin/env bash
# Poll DOM until a NEW image/video UUID appears (not in the known list).
# Emits new UUID to stdout when found, exits 0. Exits 2 on timeout, 3 on error message detected.
# Usage: poll_new_uuids.sh <profile> <image|video> <known-uuids-space-separated> [poll-seconds] [max-iters]
# IMPORTANT: known UUIDs must be FULL UUIDs (e.g. "1bbde874-2ca5-4453-9f22-7adafdf6f03d"), not prefixes.
set -euo pipefail
PROFILE="${1:?profile alias required}"
KIND="${2:?image|video required}"
KNOWN="${3:-}"
POLL="${4:-30}"
MAX="${5:-60}"

case "$KIND" in
  image) SEL='img'; MIN_W=1000;;
  video) SEL='video'; MIN_W=0;;
  *) echo "ERR: kind must be image or video" >&2; exit 1;;
esac

for i in $(seq 1 "$MAX"); do
  R=$(opencli --profile "$PROFILE" browser eval "(() => { const els = Array.from(document.querySelectorAll('$SEL')).filter(e => e.offsetParent !== null && (e.src||e.currentSrc||'').includes('assets.grok.com/users')); const filtered = '$KIND' === 'image' ? els.filter(i => i.naturalWidth >= $MIN_W) : els; const uuids = [...new Set(filtered.map(e => ((e.src||e.currentSrc||'').split('/generated/')[1]||'').split('/')[0]))]; const rt = Array.from(document.querySelectorAll('p, div, span')).filter(e => e.offsetParent !== null && e.getBoundingClientRect().x > 800 && e.getBoundingClientRect().y < 600).map(e => (e.textContent||'').trim()).filter(t => t.length > 30 && t.length < 400); const last = rt[rt.length-1] || ''; const error = /unfortunately|failed|error|encountered|parsing/i.test(last); return { uuids: uuids.join(' '), error, msg: last.slice(0,160) }; })()" 2>/dev/null | python3 -c "import sys,re; d=sys.stdin.read(); m=re.search(r'\{[^}]+\}', d, re.S); print(m.group(0) if m else '{}')" 2>/dev/null)

  ALL_UUIDS=$(echo "$R" | grep -oE '"uuids":\s*"[^"]*"' | sed -E 's/.*"([^"]*)"$/\1/')

  # FULL-UUID exact match (NOT prefix). UUID format: 8-4-4-4-12 hex chars.
  for u in $ALL_UUIDS; do
    [ -z "$u" ] && continue
    found=0
    for k in $KNOWN; do
      if [ "$u" = "$k" ]; then found=1; break; fi
    done
    if [ "$found" -eq 0 ]; then
      echo "$u"
      exit 0
    fi
  done

  if echo "$R" | grep -q '"error":\s*true'; then
    echo "$R" >&2
    exit 3
  fi

  sleep "$POLL"
done

exit 2

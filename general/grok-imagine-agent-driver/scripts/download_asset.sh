#!/usr/bin/env bash
# Download a grok-generated asset via in-page fetch + base64 decode.
# Bypasses Cloudflare gating using credentials:include + referrer trick.
# Usage: download_asset.sh <profile> <user-uuid> <asset-uuid> <image|video> <out-path>
set -euo pipefail
PROFILE="${1:?profile alias required}"
USER_UUID="${2:?user uuid required}"
ASSET_UUID="${3:?asset uuid required}"
KIND="${4:?image|video required}"
OUT="${5:?output path required}"

case "$KIND" in
  image) FILE="image.png";;
  video) FILE="generated_video.mp4";;
  *) echo "ERR: kind must be image or video" >&2; exit 1;;
esac

URL="https://assets.grok.com/users/${USER_UUID}/generated/${ASSET_UUID}/${FILE}?cache=1&dl=1"
TMP=$(mktemp)

opencli --profile "$PROFILE" browser eval "(async () => { try { const r = await fetch('$URL', { credentials: 'include', referrer: 'https://grok.com/' }); if (!r.ok) return { error: 'http', status: r.status }; const b = await r.blob(); const buf = await b.arrayBuffer(); const bytes = new Uint8Array(buf); let bin = ''; for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]); return { size: bytes.length, b64: btoa(bin) }; } catch(e) { return { err: e.message }; } })()" > "$TMP" 2>/dev/null

mkdir -p "$(dirname "$OUT")"
python3 - "$TMP" "$OUT" <<'PY'
import sys, re, base64, pathlib
data = pathlib.Path(sys.argv[1]).read_text()
m = re.search(r'"b64":\s*"([A-Za-z0-9+/=]+)"', data)
if not m:
    print(f"NO_B64 (response head: {data[:200]})", file=sys.stderr)
    sys.exit(1)
out = pathlib.Path(sys.argv[2])
out.write_bytes(base64.b64decode(m.group(1)))
print(f"saved {out} {out.stat().st_size} bytes")
PY

rm -f "$TMP"

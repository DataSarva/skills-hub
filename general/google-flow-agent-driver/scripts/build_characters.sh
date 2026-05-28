#!/usr/bin/env bash
# Build all Flow characters from shots.json (skips any already created via SKIP env).
# Usage: build_characters.sh <profile> <project_url>
set -euo pipefail
PROFILE="${1:?profile}"; PROJ="${2:?project url}"
DIR="$(cd "$(dirname "$0")" && pwd)"
SKIP="${SKIP:-Gajendra}"   # comma-separated names already built

python3 - "$DIR/../shots.json" <<'PY' > /tmp/gaj_chars.tsv
import json,sys
d=json.load(open(sys.argv[1]))
for c in d["characters"]:
    print(c["handle"].lstrip("@")+"\t"+c["desc"])
PY

while IFS=$'\t' read -r NAME DESC; do
  case ",$SKIP," in *",$NAME,"*) echo "skip $NAME"; continue;; esac
  echo "=== building $NAME ==="
  bash "$DIR/flow_make_character.sh" "$PROFILE" "$PROJ" "$NAME" "$DESC, cinematic devotional lighting, plain neutral background" || echo "FAILED $NAME"
done < /tmp/gaj_chars.tsv
echo "ALL CHARACTERS DONE"

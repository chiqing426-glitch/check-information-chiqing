#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/validate_skill.py .
python3 scripts/secret_scan.py .
python3 -m unittest discover -s scripts -p 'test_*.py' -v

NODE_BIN="${NODE:-node}"
if ! command -v "$NODE_BIN" >/dev/null 2>&1; then
  printf '%s\n' "node was not found. Install Node.js or run with NODE=/path/to/node." >&2
  exit 2
fi
"$NODE_BIN" scripts/douyin_companion/test-media-rules.mjs

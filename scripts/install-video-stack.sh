#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m venv .runtime
.runtime/bin/python -m pip install --upgrade pip
.runtime/bin/python -m pip install --no-cache-dir -r scripts/requirements-video.txt

if ! command -v ffmpeg >/dev/null 2>&1; then
  printf '%s\n' "warning: ffmpeg was not found on PATH. Install FFmpeg before transcribing media." >&2
fi

printf '%s\n' "video stack installed in .runtime"

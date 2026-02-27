#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PORT="${1:-8765}"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  :
else
  nohup python3 -m http.server "$PORT" >/tmp/daily-brief-http-${PORT}.log 2>&1 &
  echo $! > "/tmp/daily-brief-http-${PORT}.pid"
  sleep 1
fi

URL="http://127.0.0.1:${PORT}/site/index.html"
echo "Opening: $URL"
open "$URL"

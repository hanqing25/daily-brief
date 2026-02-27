#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
latest="$(ls -1 site/*.html | rg -v 'index.html' | sort | tail -n 1)"
if [ -z "${latest:-}" ]; then
  echo "No brief HTML found in site/. Run ./run_daily.sh first."
  exit 1
fi

open "$latest"
echo "Opened $latest"

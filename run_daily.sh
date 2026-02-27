#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate
python src/daily_brief.py run --date "$(date -u +%F)"
python src/build_site.py

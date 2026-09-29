#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-fast}"
source "$ROOT/.venv/bin/activate"
python -m fra_dss.cli run-all --mode "$MODE" ${2:-}

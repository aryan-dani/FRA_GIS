#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python -m ipykernel install --user --name fra-dss --display-name "Python (fra-dss)"
echo "Setup complete. Activate: source ml/.venv/bin/activate"

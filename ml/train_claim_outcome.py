"""
Train claim-outcome model (thin wrapper around fra_dss pipeline).

Usage (from repo root, with ml/.venv active or deps installed):
  python ml/train_claim_outcome.py
  python ml/train_claim_outcome.py --mode fast
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ML_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_ROOT))
sys.path.insert(0, str(ROOT))

from fra_dss.cli import capture_baseline, run_all, train_and_export_champion  # noqa: E402
from fra_dss.data import load_claims  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["fast", "full"], default="full")
    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help="Only export LightGBM artifact without full zoo",
    )
    args = parser.parse_args()
    capture_baseline()
    if args.legacy_only:
        df = load_claims(mode=args.mode)
        path = train_and_export_champion(df, args.mode)
        print(f"Wrote {path}")
        return
    run_all(mode=args.mode, include_p1=True)


if __name__ == "__main__":
    main()

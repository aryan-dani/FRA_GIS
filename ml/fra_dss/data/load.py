"""Dataset loading helpers."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from fra_dss.config import DATA_CSV, METRICS_DIR, SEED, ensure_dirs, mode_settings


def dataset_sha256(path: Path | None = None) -> str:
    target = path or DATA_CSV
    h = hashlib.sha256()
    with target.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(DATA_CSV.parent.parent),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def load_raw_claims(path: Path | None = None) -> pd.DataFrame:
    target = path or DATA_CSV
    return pd.read_csv(target)


def load_claims(
    mode: str = "fast",
    path: Path | None = None,
    seed: int = SEED,
) -> pd.DataFrame:
    """Load claims, optionally subsampled for fast mode."""
    ensure_dirs()
    df = load_raw_claims(path)
    settings = mode_settings(mode)
    max_rows = settings.get("max_rows")
    if max_rows and len(df) > max_rows:
        parts = []
        frac = max_rows / len(df)
        for _, g in df.groupby(["status", "state"], dropna=False):
            n = max(1, int(round(len(g) * frac)))
            parts.append(g.sample(n=min(n, len(g)), random_state=seed))
        df = pd.concat(parts, ignore_index=True)
        if len(df) > max_rows:
            df = df.sample(n=max_rows, random_state=seed).reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)
    return df


def provenance(mode: str, n_rows: int) -> dict[str, Any]:
    return {
        "mode": mode,
        "n_rows": int(n_rows),
        "dataset_sha256": dataset_sha256(),
        "git_sha": git_sha(),
        "seed": SEED,
        "synthetic": True,
        "disclosure": (
            "This dataset is synthetic. Scores may reflect generator rules. "
            "Real-world performance is unknown."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def metrics_path(name: str) -> Path:
    return METRICS_DIR / name

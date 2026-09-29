"""Configuration loading and path helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ML_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ML_ROOT.parent
DATA_CSV = REPO_ROOT / "data" / "fra_synthetic_claims.csv"
CONFIGS_DIR = ML_ROOT / "configs"
REPORTS_DIR = ML_ROOT / "reports"
METRICS_DIR = REPORTS_DIR / "metrics"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
PDF_DIR = REPORTS_DIR / "pdf"
ARTIFACTS_DIR = ML_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
CACHE_DIR = ARTIFACTS_DIR / "cache"
BACKEND_MODELS = REPO_ROOT / "backend" / "models"
SEED = 42


def n_jobs() -> int:
    cpu = os.cpu_count() or 2
    return max(1, cpu - 1)


@lru_cache(maxsize=4)
def load_yaml(name: str) -> dict[str, Any]:
    path = CONFIGS_DIR / name
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def experiment_config() -> dict[str, Any]:
    return load_yaml("experiment.yaml")


def dss_weights() -> dict[str, Any]:
    return load_yaml("dss_weights.yaml")


def remediation_config() -> dict[str, Any]:
    return load_yaml("remediation.yaml")


def mode_settings(mode: str = "fast") -> dict[str, Any]:
    cfg = experiment_config()
    return dict(cfg["modes"][mode])


def ensure_dirs() -> None:
    for path in (
        METRICS_DIR,
        METRICS_DIR / "splits",
        FIGURES_DIR,
        TABLES_DIR,
        PDF_DIR,
        PDF_DIR / "notebooks_html",
        MODELS_DIR,
        CACHE_DIR,
        ARTIFACTS_DIR / "tmp",
        ARTIFACTS_DIR / "preprocessors",
    ):
        path.mkdir(parents=True, exist_ok=True)

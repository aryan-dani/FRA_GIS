"""Load auxiliary DSS models (ETA, rejection reasons)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = REPO_ROOT / "ml"
MODELS_DIR = ML_ROOT / "artifacts" / "models"

# Pipelines were trained inside the ml package; ensure unpickle can resolve fra_dss.*
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

# Keep in sync with ml/configs/experiment.yaml feature_sets.A.columns
SET_A_COLUMNS = [
    "state",
    "district",
    "claim_type",
    "applicant_type",
    "land_area_ha",
    "forest_density_class",
    "year_filed",
    "documentation_completeness",
    "gram_sabha_resolution",
]


def select_set_a_frame(payload: dict[str, Any]) -> pd.DataFrame:
    row = {col: payload.get(col, pd.NA) for col in SET_A_COLUMNS}
    return pd.DataFrame([row])[SET_A_COLUMNS]


@lru_cache(maxsize=1)
def load_eta_model():
    path = MODELS_DIR / "eta_model.joblib"
    if not path.exists():
        raise FileNotFoundError("ETA model not trained yet.")
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_rejection_bundle() -> dict[str, Any]:
    path = MODELS_DIR / "rejection_reason_model.joblib"
    if not path.exists():
        raise FileNotFoundError("Rejection-reason model not trained yet.")
    return joblib.load(path)


def predict_eta_days(payload: dict[str, Any]) -> dict[str, Any]:
    model = load_eta_model()
    X = select_set_a_frame(payload)
    days = float(np.expm1(model.predict(X)[0]))
    return {
        "eta_days_point": round(days, 1),
        "caveat": "Trained on Approved/Rejected only. Pending days may be censored.",
        "synthetic": True,
    }


def predict_rejection_reasons(payload: dict[str, Any], top_k: int = 3) -> dict[str, Any]:
    bundle = load_rejection_bundle()
    X = select_set_a_frame(payload)
    proba = bundle["model"].predict_proba(X)[0]
    classes = bundle.get("classes") or []
    order = sorted(range(len(proba)), key=lambda i: proba[i], reverse=True)[:top_k]
    reasons = [
        {"reason": str(classes[i]), "probability": round(float(proba[i]), 4)}
        for i in order
    ]
    return {"reasons": reasons, "synthetic": True}

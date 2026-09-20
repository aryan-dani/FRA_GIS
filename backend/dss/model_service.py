"""Load claim-outcome model, run predictions / SHAP, serve synthetic DSS data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from dss.scheme_rules import recommend_schemes

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
MODEL_PATH = BACKEND_DIR / "models" / "claim_outcome.joblib"
METRICS_PATH = BACKEND_DIR / "models" / "metrics.json"
PRIORITY_PATH = BACKEND_DIR / "models" / "priority_by_district.json"
# Prefer backend/data copy (ships with API); fall back to repo data/
SYNTHETIC_CSV_CANDIDATES = (
    BACKEND_DIR / "data" / "fra_synthetic_claims.csv",
    REPO_ROOT / "data" / "fra_synthetic_claims.csv",
)

# Allow importing ml.features from repo root when running from backend/
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.features import claim_to_feature_dict, prepare_features  # noqa: E402


class ModelNotReady(Exception):
    """Raised when the trained artifact is missing."""


@lru_cache(maxsize=1)
def load_artifact() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise ModelNotReady(
            "Claim-outcome model missing. From repo root run: "
            "python ml/train_claim_outcome.py"
        )
    return joblib.load(MODEL_PATH)


def model_ready() -> bool:
    return MODEL_PATH.exists()


def get_metrics() -> dict[str, Any] | None:
    if not METRICS_PATH.exists():
        return None
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


def predict_outcome(features: dict[str, Any], top_k_shap: int = 5) -> dict[str, Any]:
    artifact = load_artifact()
    prepared = prepare_features(features, district_freq=artifact["district_freq"])
    X = artifact["preprocessor"].transform(prepared)
    model = artifact["model"]
    label_encoder = artifact["label_encoder"]

    proba = model.predict_proba(X)[0]
    pred_idx = int(np.argmax(proba))
    predicted = str(label_encoder.inverse_transform([pred_idx])[0])
    probabilities = {
        str(label_encoder.classes_[i]): round(float(proba[i]), 4)
        for i in range(len(label_encoder.classes_))
    }

    shap_top: list[dict[str, Any]] = []
    try:
        import shap

        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(X)
        if isinstance(values, list):
            arr = np.asarray(values[pred_idx])
        else:
            arr = np.asarray(values)
            # Newer SHAP: (n_samples, n_features, n_classes)
            if arr.ndim == 3:
                arr = arr[:, :, pred_idx]

        if arr.ndim == 2:
            row_vals = arr[0]
        else:
            row_vals = arr.ravel()

        names = artifact["feature_names"]
        pairs = sorted(
            (
                (name, float(np.asarray(impact).reshape(-1)[0]))
                for name, impact in zip(names, row_vals)
            ),
            key=lambda t: abs(t[1]),
            reverse=True,
        )[:top_k_shap]
        shap_top = [
            {"feature": _pretty_feature(name), "impact": round(impact, 4)}
            for name, impact in pairs
        ]
    except Exception as exc:  # SHAP optional at runtime
        shap_top = [{"feature": "_shap_unavailable", "impact": 0.0, "error": str(exc)}]

    return {
        "predicted_status": predicted,
        "probabilities": probabilities,
        "shap_top": shap_top,
        "features_used": features,
    }


def predict_from_claim(claim: dict[str, Any], top_k_shap: int = 5) -> dict[str, Any]:
    features = claim_to_feature_dict(claim)
    result = predict_outcome(features, top_k_shap=top_k_shap)
    result["schemes"] = recommend_schemes(features)
    return result


def _pretty_feature(name: str) -> str:
    return (
        name.replace("cat__", "")
        .replace("num__", "")
        .replace("_", " ")
    )


@lru_cache(maxsize=1)
def _synthetic_csv_path() -> Path:
    for path in SYNTHETIC_CSV_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Missing fra_synthetic_claims.csv under backend/data/ or data/"
    )


@lru_cache(maxsize=1)
def _synthetic_frame() -> pd.DataFrame:
    return pd.read_csv(_synthetic_csv_path())


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    return value


def synthetic_row_to_claim(row: dict[str, Any]) -> dict[str, Any]:
    """Map a synthetic CSV row to the frontend claim schema."""
    claim_id = str(row.get("claim_id") or "")
    village = _clean_value(row.get("village")) or ""
    district = _clean_value(row.get("district")) or ""
    claim_type = _clean_value(row.get("claim_type")) or "IFR"
    year = _clean_value(row.get("year_filed"))
    name = village.strip() if village else f"{claim_type} claimant"
    if district and name == f"{claim_type} claimant":
        name = f"{claim_type} · {district}"

    return {
        "id": claim_id,
        "claim_id": claim_id,
        "name": name or claim_id,
        "village": village or None,
        "district": district or None,
        "state": _clean_value(row.get("state")),
        "claim_type": claim_type,
        "status": _clean_value(row.get("status")) or "Pending",
        "latitude": _clean_value(row.get("latitude")),
        "longitude": _clean_value(row.get("longitude")),
        "applicant_type": _clean_value(row.get("applicant_type")),
        "land_area_ha": _clean_value(row.get("land_area_ha")),
        "forest_density_class": _clean_value(row.get("forest_density_class")),
        "year_filed": year,
        "documentation_completeness": _clean_value(
            row.get("documentation_completeness")
        ),
        "gram_sabha_resolution": _clean_value(row.get("gram_sabha_resolution")),
        "processing_days": _clean_value(row.get("processing_days")),
        "committee_level_reached": _clean_value(row.get("committee_level_reached")),
        "adjacent_forest_area": _clean_value(row.get("adjacent_forest_area")),
        "rejection_reason": _clean_value(row.get("rejection_reason")),
        "created_at": (
            f"{int(float(year))}-01-01T00:00:00Z"
            if year not in (None, "")
            else None
        ),
        "source": "synthetic",
        "raw_text": None,
    }


def list_synthetic_claims(
    state: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Return mapped synthetic claims for the ledger / map APIs."""
    df = _synthetic_frame()
    if state:
        df = df[df["state"].astype(str).str.lower() == state.strip().lower()]
    if status:
        df = df[df["status"].astype(str).str.lower() == status.strip().lower()]
    if q:
        needle = q.strip().lower()
        mask = (
            df["claim_id"].astype(str).str.lower().str.contains(needle, na=False)
            | df["village"].astype(str).str.lower().str.contains(needle, na=False)
            | df["district"].astype(str).str.lower().str.contains(needle, na=False)
            | df["state"].astype(str).str.lower().str.contains(needle, na=False)
        )
        df = df[mask]

    total = int(len(df))
    offset = max(0, int(offset))
    if limit is None:
        sliced = df.iloc[offset:]
    else:
        limit = max(1, int(limit))
        sliced = df.iloc[offset : offset + limit]

    claims = [
        synthetic_row_to_claim(
            {k: _clean_value(v) for k, v in row.items()}
        )
        for row in sliced.to_dict(orient="records")
    ]
    return claims, total


def get_synthetic_claim(claim_id: str) -> dict[str, Any] | None:
    df = _synthetic_frame()
    match = df[df["claim_id"].astype(str) == str(claim_id)]
    if match.empty:
        return None
    row = {k: _clean_value(v) for k, v in match.iloc[0].to_dict().items()}
    return synthetic_row_to_claim(row)


def sample_synthetic_claims(
    state: str | None = None,
    limit: int = 200,
    status: str | None = None,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 5000))
    claims, _total = list_synthetic_claims(state=state, status=status, limit=limit)
    return claims[:limit]


def load_priority(state: str | None = None) -> list[dict[str, Any]]:
    if PRIORITY_PATH.exists():
        rows = json.loads(PRIORITY_PATH.read_text(encoding="utf-8"))
    else:
        rows = _priority_from_csv()

    if state:
        state_l = state.strip().lower()
        rows = [r for r in rows if str(r.get("state", "")).lower() == state_l]
    return rows


def _priority_from_csv() -> list[dict[str, Any]]:
    """Fallback district aggregates if priority JSON was not precomputed."""
    df = _synthetic_frame()
    rows: list[dict[str, Any]] = []
    for (state, district), g in df.groupby(["state", "district"], dropna=False):
        pending = int((g["status"] == "Pending").sum())
        rejected = int((g["status"] == "Rejected").sum())
        approved = int((g["status"] == "Approved").sum())
        total = int(len(g))
        mean_days = float(pd.to_numeric(g["processing_days"], errors="coerce").mean())
        reject_rate = rejected / total if total else 0.0
        pending_rate = pending / total if total else 0.0
        score = (
            0.45 * pending_rate * 100
            + 0.35 * reject_rate * 100
            + 0.20 * min(mean_days / 365.0, 1.0) * 100
        )
        lat = pd.to_numeric(g["latitude"], errors="coerce").mean()
        lon = pd.to_numeric(g["longitude"], errors="coerce").mean()
        rows.append(
            {
                "state": state,
                "district": district
                if pd.notna(district) and district != ""
                else "Unknown",
                "total_claims": total,
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "mean_processing_days": round(mean_days, 1)
                if not np.isnan(mean_days)
                else None,
                "reject_rate": round(reject_rate, 4),
                "priority_score": round(float(score), 2),
                "latitude": None if pd.isna(lat) else round(float(lat), 5),
                "longitude": None if pd.isna(lon) else round(float(lon), 5),
            }
        )
    rows.sort(key=lambda r: r["priority_score"], reverse=True)
    return rows


def dss_bundle_for_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Predict + schemes for a raw feature dict (from POST body)."""
    features = claim_to_feature_dict(payload)
    # Prefer explicit fields from payload when present
    for key in (
        "state",
        "district",
        "village",
        "claim_type",
        "applicant_type",
        "land_area_ha",
        "forest_density_class",
        "year_filed",
        "documentation_completeness",
        "gram_sabha_resolution",
        "processing_days",
        "committee_level_reached",
        "status",
    ):
        if payload.get(key) is not None and payload.get(key) != "":
            features[key] = payload[key]

    prediction = predict_outcome(features)
    schemes = recommend_schemes(features)
    return {**prediction, "schemes": schemes}

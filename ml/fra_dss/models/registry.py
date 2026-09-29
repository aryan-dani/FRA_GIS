"""Artifact registry and contract export for the Flask backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from fra_dss.config import BACKEND_MODELS, MODELS_DIR, SEED, ensure_dirs

STATUS_LABELS = ["Approved", "Pending", "Rejected"]

# Must match ml.features.prepare_features output (backend contract).
CONTRACT_CATEGORICAL = [
    "state",
    "claim_type",
    "applicant_type",
    "forest_density_class",
    "documentation_completeness",
    "gram_sabha_resolution",
    "committee_level_reached",
]
CONTRACT_NUMERIC = [
    "land_area_ha",
    "year_filed",
    "processing_days",
    "district_freq",
]


def build_contract_preprocessor() -> ColumnTransformer:
    """Preprocessor that consumes ml.features.prepare_features frames."""
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CONTRACT_CATEGORICAL,
            ),
            ("num", "passthrough", CONTRACT_NUMERIC),
        ]
    )


def export_contract_artifact(
    model: Any,
    preprocessor: Any,
    label_encoder: LabelEncoder,
    district_freq: dict[str, float],
    metrics: dict[str, Any],
    priority_rows: list[dict[str, Any]],
) -> Path:
    """Write backend/models/claim_outcome.joblib matching model_service contract."""
    ensure_dirs()
    BACKEND_MODELS.mkdir(parents=True, exist_ok=True)

    try:
        feature_names = list(preprocessor.get_feature_names_out())
    except Exception:
        feature_names = [f"f{i}" for i in range(100)]

    artifact = {
        "preprocessor": preprocessor,
        "model": model,
        "label_encoder": label_encoder,
        "district_freq": district_freq,
        "feature_names": feature_names,
        "classes": list(label_encoder.classes_),
        "status_labels": STATUS_LABELS,
        "feature_set": "A_contract",
        "note": (
            "Contract artifact uses prepare_features columns for Flask compatibility. "
            "Benchmark Set A pipelines live under ml/artifacts."
        ),
        "synthetic": True,
    }
    path = BACKEND_MODELS / "claim_outcome.joblib"
    joblib.dump(artifact, path, compress=3)
    (BACKEND_MODELS / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    (BACKEND_MODELS / "priority_by_district.json").write_text(
        json.dumps(priority_rows, indent=2), encoding="utf-8"
    )
    joblib.dump(artifact, MODELS_DIR / "champion_set_a_lgbm.joblib", compress=3)
    return path


def compute_district_freq(series: pd.Series) -> dict[str, float]:
    counts = series.fillna("Unknown").astype(str).value_counts()
    return {str(k): float(v) for k, v in counts.items()}


def aggregate_priority(df: pd.DataFrame, extra: dict[str, dict] | None = None) -> list[dict]:
    rows = []
    grouped = df.groupby(["state", "district"], dropna=False)
    for (state, district), g in grouped:
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
        row = {
            "state": state,
            "district": district if pd.notna(district) and district != "" else "Unknown",
            "total_claims": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "mean_processing_days": round(mean_days, 1) if not np.isnan(mean_days) else None,
            "reject_rate": round(reject_rate, 4),
            "priority_score": round(float(score), 2),
            "latitude": None if pd.isna(lat) else round(float(lat), 5),
            "longitude": None if pd.isna(lon) else round(float(lon), 5),
        }
        if extra and row["district"] in extra:
            row.update(extra[row["district"]])
        rows.append(row)
    rows.sort(key=lambda r: r["priority_score"], reverse=True)
    return rows

"""Shared feature prep for claim-outcome training and inference."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "state",
    "district",
    "claim_type",
    "applicant_type",
    "land_area_ha",
    "forest_density_class",
    "year_filed",
    "documentation_completeness",
    "gram_sabha_resolution",
    "processing_days",
    "committee_level_reached",
]

CATEGORICAL_COLUMNS = [
    "state",
    "claim_type",
    "applicant_type",
    "forest_density_class",
    "documentation_completeness",
    "gram_sabha_resolution",
    "committee_level_reached",
]

NUMERIC_COLUMNS = [
    "land_area_ha",
    "year_filed",
    "processing_days",
    "district_freq",
]

STATUS_LABELS = ["Approved", "Pending", "Rejected"]


def _as_frame(payload: dict[str, Any] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(payload, pd.DataFrame):
        return payload.copy()
    return pd.DataFrame([payload])


def prepare_features(
    payload: dict[str, Any] | pd.DataFrame,
    district_freq: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Normalize raw claim fields into model feature columns."""
    df = _as_frame(payload)

    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    df["state"] = df["state"].fillna("Unknown").astype(str).str.strip()
    df["district"] = df["district"].fillna("Unknown").astype(str).str.strip()
    df["claim_type"] = df["claim_type"].fillna("IFR").astype(str).str.strip()
    df["applicant_type"] = df["applicant_type"].fillna("ST").astype(str).str.strip()
    df["forest_density_class"] = (
        df["forest_density_class"].fillna("Open").astype(str).str.strip()
    )
    df["documentation_completeness"] = (
        df["documentation_completeness"].fillna("Incomplete").astype(str).str.strip()
    )
    df["gram_sabha_resolution"] = (
        df["gram_sabha_resolution"].fillna("Pending").astype(str).str.strip()
    )
    df["committee_level_reached"] = (
        df["committee_level_reached"].fillna("FRC").astype(str).str.strip()
    )

    df["land_area_ha"] = pd.to_numeric(df["land_area_ha"], errors="coerce").fillna(1.0)
    df["year_filed"] = pd.to_numeric(df["year_filed"], errors="coerce").fillna(2015)
    df["processing_days"] = pd.to_numeric(
        df["processing_days"], errors="coerce"
    ).fillna(180)

    freq = district_freq or {}
    default_freq = float(np.median(list(freq.values()))) if freq else 1.0
    df["district_freq"] = df["district"].map(freq).fillna(default_freq).astype(float)

    return df[CATEGORICAL_COLUMNS + NUMERIC_COLUMNS]


def claim_to_feature_dict(claim: dict[str, Any]) -> dict[str, Any]:
    """Map Firestore / API claim fields onto synthetic-schema feature names."""
    return {
        "state": claim.get("state") or "Unknown",
        "district": claim.get("district") or "Unknown",
        "claim_type": claim.get("claim_type") or "IFR",
        "applicant_type": claim.get("applicant_type") or claim.get("category") or "ST",
        "land_area_ha": claim.get("land_area_ha") or claim.get("land_area") or 1.0,
        "forest_density_class": claim.get("forest_density_class") or "Open",
        "year_filed": claim.get("year_filed")
        or (
            int(str(claim.get("created_at", "2015"))[:4])
            if claim.get("created_at")
            else 2015
        ),
        "documentation_completeness": claim.get("documentation_completeness")
        or ("Complete" if claim.get("raw_text") else "Incomplete"),
        "gram_sabha_resolution": claim.get("gram_sabha_resolution") or "Pending",
        "processing_days": claim.get("processing_days") or 180,
        "committee_level_reached": claim.get("committee_level_reached") or "FRC",
        "village": claim.get("village") or "",
        "status": claim.get("status") or "Pending",
        "latitude": claim.get("latitude"),
        "longitude": claim.get("longitude"),
    }

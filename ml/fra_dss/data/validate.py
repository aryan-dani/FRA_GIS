"""Pandera schema validation for the synthetic FRA claims CSV."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema

STATUS_VALUES = {"Approved", "Pending", "Rejected"}
STATE_VALUES = {"Madhya Pradesh", "Odisha", "Telangana", "Tripura"}
APPLICANT_TYPES = {"ST", "OTFD"}


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["claim_id"] = cleaned["claim_id"].astype(str)
    cleaned["state"] = cleaned["state"].astype(str)
    cleaned["district"] = cleaned["district"].astype(str)
    cleaned["status"] = cleaned["status"].astype(str)
    cleaned["applicant_type"] = cleaned["applicant_type"].astype(str)
    cleaned["land_area_ha"] = pd.to_numeric(cleaned["land_area_ha"], errors="coerce")
    cleaned["year_filed"] = pd.to_numeric(cleaned["year_filed"], errors="coerce").astype("Int64")
    cleaned["processing_days"] = pd.to_numeric(cleaned["processing_days"], errors="coerce")
    cleaned["latitude"] = pd.to_numeric(cleaned["latitude"], errors="coerce")
    cleaned["longitude"] = pd.to_numeric(cleaned["longitude"], errors="coerce")
    if "rejection_reason" in cleaned.columns:
        cleaned["rejection_reason"] = cleaned["rejection_reason"].where(
            cleaned["rejection_reason"].notna(), None
        )
        cleaned["rejection_reason"] = cleaned["rejection_reason"].apply(
            lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
        )
    if "village" in cleaned.columns:
        cleaned["village"] = cleaned["village"].where(cleaned["village"].notna(), None)
        cleaned["village"] = cleaned["village"].apply(
            lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
        )
    if "adjacent_forest_area" in cleaned.columns:
        cleaned["adjacent_forest_area"] = pd.to_numeric(
            cleaned["adjacent_forest_area"], errors="coerce"
        )
    return cleaned


CLAIMS_SCHEMA = DataFrameSchema(
    {
        "claim_id": Column(str, nullable=False),
        "state": Column(str, Check.isin(STATE_VALUES), nullable=False),
        "district": Column(str, nullable=False),
        "village": Column(str, nullable=True),
        "adjacent_forest_area": Column(float, nullable=True, coerce=True),
        "latitude": Column(float, nullable=True, coerce=True),
        "longitude": Column(float, nullable=True, coerce=True),
        "claim_type": Column(str, nullable=False),
        "applicant_type": Column(str, Check.isin(APPLICANT_TYPES), nullable=False),
        "land_area_ha": Column(float, Check.ge(0), nullable=False, coerce=True),
        "forest_density_class": Column(str, nullable=False),
        "year_filed": Column(int, Check.in_range(2008, 2025), nullable=False, coerce=True),
        "documentation_completeness": Column(str, nullable=False),
        "gram_sabha_resolution": Column(str, nullable=False),
        "processing_days": Column(float, Check.ge(0), nullable=False, coerce=True),
        "committee_level_reached": Column(str, nullable=False),
        "status": Column(str, Check.isin(STATUS_VALUES), nullable=False),
        "rejection_reason": Column(str, nullable=True),
    },
    coerce=True,
    strict=False,
)


def validate_claims(df: pd.DataFrame) -> dict[str, Any]:
    """Validate and return a profile summary. Raises on hard schema failures."""
    cleaned = _prepare(df)
    CLAIMS_SCHEMA.validate(cleaned, lazy=True)

    missing = cleaned.isna().sum().to_dict()
    status_counts = cleaned["status"].value_counts().to_dict()
    return {
        "n_rows": int(len(cleaned)),
        "n_cols": int(cleaned.shape[1]),
        "missing": {k: int(v) for k, v in missing.items() if v},
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "n_districts": int(cleaned["district"].nunique()),
        "n_villages": int(cleaned["village"].nunique(dropna=True)),
        "land_area_ha": {
            "median": float(cleaned["land_area_ha"].median()),
            "p99": float(cleaned["land_area_ha"].quantile(0.99)),
            "max": float(cleaned["land_area_ha"].max()),
        },
        "valid": True,
        "synthetic": True,
    }

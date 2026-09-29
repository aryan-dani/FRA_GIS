"""Pydantic schemas for DSS recommendations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ShapDriver(BaseModel):
    feature: str
    impact: float
    sentence: str


class RejectionReason(BaseModel):
    reason: str
    probability: float
    advice: str


class WhatIfChange(BaseModel):
    field: str
    from_value: Any
    to_value: Any
    approval_lift: float


class DSSRecommendation(BaseModel):
    predicted_status: str
    probabilities: dict[str, float]
    confidence: float
    human_review: bool
    shap_drivers: list[ShapDriver] = Field(default_factory=list)
    rejection_reasons: list[RejectionReason] = Field(default_factory=list)
    what_if: list[WhatIfChange] = Field(default_factory=list)
    eta_days_p50: float | None = None
    eta_days_point: float | None = None
    schemes: list[dict[str, Any]] = Field(default_factory=list)
    audit_flags: list[str] = Field(default_factory=list)
    synthetic_disclosure: str = (
        "Synthetic demo data. Not for real claim decisions."
    )

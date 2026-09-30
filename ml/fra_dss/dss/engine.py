"""Core DSS recommendation engine."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import joblib
import numpy as np

from fra_dss.config import BACKEND_MODELS, MODELS_DIR, REPO_ROOT, dss_weights, remediation_config
from fra_dss.dss.schemas import DSSRecommendation, RejectionReason, ShapDriver, WhatIfChange
from fra_dss.dss.what_if import search_what_if


def _import_scheme_rules():
    backend = REPO_ROOT / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    from dss.scheme_rules import recommend_schemes  # type: ignore

    return recommend_schemes


@lru_cache(maxsize=1)
def load_shipped_artifact() -> dict[str, Any]:
    path = BACKEND_MODELS / "claim_outcome.joblib"
    if not path.exists():
        alt = MODELS_DIR / "champion_set_a_lgbm.joblib"
        if alt.exists():
            return joblib.load(alt)
        raise FileNotFoundError("No claim_outcome.joblib found. Train first.")
    return joblib.load(path)


def _shap_sentences(shap_top: list[dict[str, Any]]) -> list[ShapDriver]:
    drivers = []
    for item in shap_top:
        feat = str(item.get("feature", ""))
        impact = float(item.get("impact", 0.0))
        direction = "raises" if impact > 0 else "lowers"
        sentence = f"{feat} {direction} the predicted class score (impact {impact:+.3f})."
        drivers.append(ShapDriver(feature=feat, impact=impact, sentence=sentence))
    return drivers


def recommend(
    claim: dict[str, Any],
    predict_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    eta_model=None,
    reason_model=None,
    reason_labels: list[str] | None = None,
) -> DSSRecommendation:
    """
    Combine calibrated probabilities, SHAP, schemes, ETA, and optional reasons/what-if.
    Order: outcome probs -> SHAP -> rejection reasons -> what-if -> ETA -> schemes -> flags.
    """
    if predict_fn is None:
        # Lazy import to avoid circular deps with backend
        sys.path.insert(0, str(REPO_ROOT / "backend"))
        from dss.model_service import predict_from_claim  # type: ignore

        raw = predict_from_claim(claim)
    else:
        raw = predict_fn(claim)

    probs = {k: float(v) for k, v in (raw.get("probabilities") or {}).items()}
    conf = max(probs.values()) if probs else 0.0
    review_thresh = float(dss_weights().get("human_review_max_confidence", 0.55))
    human_review = conf < review_thresh

    shap_drivers = _shap_sentences(raw.get("shap_top") or [])

    reasons: list[RejectionReason] = []
    rem = remediation_config()
    if reason_model is not None and probs.get("Rejected", 0) >= 0.35:
        try:
            import pandas as pd
            from fra_dss.preprocessing.pipelines import select_frame

            X = select_frame(pd.DataFrame([claim]), "A")
            proba = reason_model.predict_proba(X)[0]
            top = np.argsort(proba)[::-1][:3]
            labels = reason_labels or [str(i) for i in range(len(proba))]
            for i in top:
                reason = labels[int(i)]
                advice = rem.get("reasons", {}).get(reason, {}).get(
                    "advice", rem.get("disclaimer", "")
                )
                reasons.append(
                    RejectionReason(
                        reason=reason, probability=round(float(proba[i]), 4), advice=advice
                    )
                )
        except Exception:
            pass

    def _predict_only(c: dict[str, Any]) -> dict[str, Any]:
        if predict_fn:
            return predict_fn(c)
        sys.path.insert(0, str(REPO_ROOT / "backend"))
        from dss.model_service import predict_outcome  # type: ignore
        from ml.features import claim_to_feature_dict

        return predict_outcome(claim_to_feature_dict(c))

    what_ifs = []
    try:
        for item in search_what_if(_predict_only, claim, target_lift=0.03):
            what_ifs.append(WhatIfChange(**item))
    except Exception:
        pass

    eta_point = None
    if eta_model is not None:
        try:
            import pandas as pd
            from fra_dss.preprocessing.pipelines import select_frame

            X = select_frame(pd.DataFrame([claim]), "A")
            eta_point = float(np.expm1(eta_model.predict(X)[0]))
        except Exception:
            pass

    schemes = raw.get("schemes")
    if schemes is None:
        try:
            recommend_schemes = _import_scheme_rules()
            schemes = recommend_schemes(claim)
        except Exception:
            schemes = []

    flags = []
    land = claim.get("land_area_ha")
    try:
        if land is not None and float(land) > 74:
            flags.append("land_area_ha above synthetic 99th percentile")
    except Exception:
        pass

    return DSSRecommendation(
        predicted_status=str(raw.get("predicted_status", "Pending")),
        probabilities=probs,
        confidence=round(conf, 4),
        human_review=human_review,
        shap_drivers=shap_drivers,
        rejection_reasons=reasons,
        what_if=what_ifs,
        eta_days_point=None if eta_point is None else round(eta_point, 1),
        eta_days_p50=None if eta_point is None else round(eta_point, 1),
        schemes=schemes or [],
        audit_flags=flags,
    )

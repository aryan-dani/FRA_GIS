"""DSS package: scheme rules + claim-outcome model service."""

from dss.scheme_rules import recommend_schemes, scheme_catalog
from dss.model_service import (
    ModelNotReady,
    dss_bundle_for_payload,
    get_metrics,
    get_synthetic_claim,
    list_synthetic_claims,
    load_priority,
    model_ready,
    predict_from_claim,
    sample_synthetic_claims,
)

__all__ = [
    "ModelNotReady",
    "dss_bundle_for_payload",
    "get_metrics",
    "get_synthetic_claim",
    "list_synthetic_claims",
    "load_priority",
    "model_ready",
    "predict_from_claim",
    "recommend_schemes",
    "sample_synthetic_claims",
    "scheme_catalog",
]

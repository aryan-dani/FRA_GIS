"""Actionable-field what-if search (backend copy; no ml/.venv required)."""

from __future__ import annotations

import copy
from typing import Any, Callable

ACTIONABLE = {
    "documentation_completeness": ["Incomplete", "Partial", "Complete"],
    "gram_sabha_resolution": ["Pending", "Disputed", "Passed"],
    "claim_type": ["IFR", "CFR", "CR"],
}


def search_what_if(
    predict_fn: Callable[[dict[str, Any]], dict[str, Any]],
    claim: dict[str, Any],
    target_lift: float = 0.05,
) -> list[dict[str, Any]]:
    """Find smallest single-field changes that raise P(Approved)."""
    base = predict_fn(claim)
    base_p = float(base.get("probabilities", {}).get("Approved", 0.0))
    candidates: list[dict[str, Any]] = []
    for field, values in ACTIONABLE.items():
        current = claim.get(field)
        for value in values:
            if value == current:
                continue
            trial = copy.deepcopy(claim)
            trial[field] = value
            out = predict_fn(trial)
            p = float(out.get("probabilities", {}).get("Approved", 0.0))
            lift = p - base_p
            if lift >= target_lift:
                candidates.append(
                    {
                        "field": field,
                        "from_value": current,
                        "to_value": value,
                        "approval_lift": round(lift, 4),
                    }
                )
    candidates.sort(key=lambda row: (-row["approval_lift"], row["field"]))
    return candidates[:5]

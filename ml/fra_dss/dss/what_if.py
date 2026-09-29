"""What-if search over actionable fields only."""

from __future__ import annotations

from typing import Any

import copy

ACTIONABLE = {
    "documentation_completeness": ["Incomplete", "Partial", "Complete"],
    "gram_sabha_resolution": ["Pending", "Disputed", "Passed"],
    "claim_type": ["IFR", "CFR", "CR"],
}


def search_what_if(
    predict_fn,
    claim: dict[str, Any],
    target_lift: float = 0.05,
) -> list[dict[str, Any]]:
    """Find smallest single-field changes that raise P(Approved)."""
    base = predict_fn(claim)
    base_p = float(base.get("probabilities", {}).get("Approved", 0.0))
    candidates = []
    for field, values in ACTIONABLE.items():
        current = claim.get(field)
        for v in values:
            if v == current:
                continue
            trial = copy.deepcopy(claim)
            trial[field] = v
            out = predict_fn(trial)
            p = float(out.get("probabilities", {}).get("Approved", 0.0))
            lift = p - base_p
            if lift >= target_lift:
                candidates.append(
                    {
                        "field": field,
                        "from_value": current,
                        "to_value": v,
                        "approval_lift": round(lift, 4),
                    }
                )
    candidates.sort(key=lambda r: (-r["approval_lift"], r["field"]))
    return candidates[:5]

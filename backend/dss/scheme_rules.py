"""
Rule-based CSS scheme eligibility for the FRA DSS demo.

These heuristics are transparent stand-ins for production MoTA / DAJGUA
eligibility criteria. Replace with official rule tables when available.
"""

from __future__ import annotations

from typing import Any


SCHEMES = [
    {
        "scheme_id": "pm_kisan",
        "name": "PM-KISAN",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Income support for landholding farmer families.",
    },
    {
        "scheme_id": "jjm",
        "name": "Jal Jeevan Mission",
        "ministry": "Ministry of Jal Shakti",
        "description": "Functional household tap water connections.",
    },
    {
        "scheme_id": "mgnrega",
        "name": "MGNREGA",
        "ministry": "Ministry of Rural Development",
        "description": "Wage employment and rural asset creation.",
    },
    {
        "scheme_id": "dajgua",
        "name": "DAJGUA",
        "ministry": "Multi-ministry (Tribal Affairs convergence)",
        "description": "Layered Central Sector Schemes for FRA patta holders.",
    },
]


def _norm(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def recommend_schemes(features: dict[str, Any]) -> list[dict[str, Any]]:
    """Return scheme eligibility + priority for a single claim/village context."""
    claim_type = _norm(features.get("claim_type"), "IFR").upper()
    status = _norm(features.get("status"), "Pending")
    forest = _norm(features.get("forest_density_class"), "Open")
    docs = _norm(features.get("documentation_completeness"), "Incomplete")
    land_ha = _num(features.get("land_area_ha"), 1.0)
    processing_days = _num(features.get("processing_days"), 180)
    applicant = _norm(features.get("applicant_type"), "ST").upper()

    is_ifr = claim_type in {"IFR", "INDIVIDUAL"}
    is_cfr = claim_type in {"CFR", "CR", "COMMUNITY"}
    is_titled = status.lower() in {"approved", "title distributed", "titled"}
    is_pending = status.lower() == "pending"
    dense_or_open = forest.lower() in {"open", "moderately dense", "dense", "scrub"}

    results: list[dict[str, Any]] = []

    # PM-KISAN — IFR agricultural landholders
    pm_reasons: list[str] = []
    pm_eligible = False
    pm_priority = "Low"
    if is_ifr and land_ha > 0:
        pm_reasons.append(f"IFR claim with {land_ha:.2f} ha recorded land")
        if is_titled or is_pending:
            pm_eligible = True
            pm_priority = "High" if is_titled else "Medium"
            pm_reasons.append(f"Status {status} — eligible for farmer income support layering")
        else:
            pm_reasons.append("Rejected claims are not queued for PM-KISAN in this demo")
        if docs.lower() == "complete":
            pm_reasons.append("Documentation marked complete")
    else:
        pm_reasons.append("PM-KISAN demo rule targets IFR landholders")
    results.append(_pack("pm_kisan", pm_eligible, pm_priority, pm_reasons))

    # Jal Jeevan Mission — water stress proxy via open/scrub forest + backlog
    jjm_reasons: list[str] = []
    jjm_eligible = False
    jjm_priority = "Low"
    water_stress = forest.lower() in {"open", "scrub"} or processing_days > 240
    if water_stress:
        jjm_eligible = True
        jjm_priority = "High" if processing_days > 300 or forest.lower() == "open" else "Medium"
        jjm_reasons.append(
            f"Water-stress proxy: forest class '{forest}', processing_days={int(processing_days)}"
        )
        jjm_reasons.append("Prioritize functional household tap connections (JJM)")
    else:
        jjm_reasons.append("No strong water-stress signal from demo proxies")
    if dense_or_open:
        jjm_reasons.append("Village is forest-adjacent — JJM often layered with FRA habitation")
    results.append(_pack("jjm", jjm_eligible, jjm_priority, jjm_reasons))

    # MGNREGA — pending backlog / community claims
    mgn_reasons: list[str] = []
    mgn_eligible = False
    mgn_priority = "Low"
    if is_pending or is_cfr:
        mgn_eligible = True
        mgn_priority = "High" if is_pending and processing_days > 200 else "Medium"
        if is_pending:
            mgn_reasons.append("Pending claim — wage employment can bridge processing delay")
        if is_cfr:
            mgn_reasons.append("Community / CFR claim — rural works and CFR assets fit MGNREGA")
    else:
        mgn_reasons.append("No pending backlog or community claim trigger")
    if applicant in {"ST", "OTFD"}:
        mgn_reasons.append(f"Applicant type {applicant} aligns with tribal / forest-dweller focus")
    results.append(_pack("mgnrega", mgn_eligible, mgn_priority, mgn_reasons))

    # DAJGUA — convergence for titled IFR/CFR holders
    daj_reasons: list[str] = []
    daj_eligible = False
    daj_priority = "Low"
    if is_titled and (is_ifr or is_cfr):
        daj_eligible = True
        daj_priority = "High"
        daj_reasons.append(
            "Approved IFR/CFR holder — prioritize multi-ministry DAJGUA convergence"
        )
        daj_reasons.append("Layer agriculture, water, livelihood, and forest schemes together")
    elif is_pending and (is_ifr or is_cfr):
        daj_eligible = True
        daj_priority = "Medium"
        daj_reasons.append("Pending IFR/CFR — pre-position DAJGUA package for post-title delivery")
    else:
        daj_reasons.append("DAJGUA demo rule focuses on IFR/CFR titled or near-title holders")
    results.append(_pack("dajgua", daj_eligible, daj_priority, daj_reasons))

    return results


def _pack(
    scheme_id: str, eligible: bool, priority: str, reasons: list[str]
) -> dict[str, Any]:
    meta = next(s for s in SCHEMES if s["scheme_id"] == scheme_id)
    return {
        **meta,
        "eligible": eligible,
        "priority": priority,
        "reasons": reasons,
    }


def scheme_catalog() -> list[dict[str, Any]]:
    return list(SCHEMES)

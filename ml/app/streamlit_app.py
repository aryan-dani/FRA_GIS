"""Standalone FRA DSS Streamlit demo (no Firebase required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ML_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ML_ROOT.parent
sys.path.insert(0, str(ML_ROOT))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from fra_dss.config import METRICS_DIR, FIGURES_DIR
from fra_dss.data import load_claims
from fra_dss.dss.engine import recommend

DISCLOSURE = (
    "**Synthetic data.** This demo uses generated FRA claims. "
    "It must not drive real claim decisions."
)


def _load_json(name: str):
    path = METRICS_DIR / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


st.set_page_config(page_title="FRA DSS Demo", layout="wide")
st.title("FRA Atlas Decision Support System")
st.warning(DISCLOSURE)

page = st.sidebar.radio(
    "Pages",
    [
        "Overview",
        "Claim Risk Simulator",
        "Rejection Root Cause",
        "Backlog Triage Queue",
        "District Priority",
        "Model Benchmark",
        "Explainability",
        "About",
    ],
)

if page == "Overview":
    champ = _load_json("champion.json")
    base = _load_json("baseline_existing.json")
    c1, c2, c3 = st.columns(3)
    c1.metric("Champion model", champ.get("model", "n/a"))
    c2.metric("S1 macro-F1", f"{champ.get('s1_macro_f1_mean', float('nan')):.3f}" if champ.get("s1_macro_f1_mean") else "n/a")
    c3.metric("Baseline macro-F1", str(base.get("macro_f1", "n/a")))
    fig = FIGURES_DIR / "10_leaderboard_set_a.png"
    if fig.exists():
        st.image(str(fig), caption="Leaderboard Set A")

elif page == "Claim Risk Simulator":
    with st.form("claim"):
        state = st.selectbox("State", ["Madhya Pradesh", "Odisha", "Telangana", "Tripura"])
        district = st.text_input("District", "Demo District")
        claim_type = st.selectbox("Claim type", ["IFR", "CFR", "CR"])
        applicant_type = st.selectbox("Applicant type", ["ST", "OTFD"])
        land_area_ha = st.number_input("Land area (ha)", 0.1, 100.0, 1.5)
        forest_density_class = st.selectbox(
            "Forest density", ["Open", "Moderately Dense", "Very Dense", "Scrub"]
        )
        year_filed = st.number_input("Year filed", 2008, 2024, 2018)
        documentation_completeness = st.selectbox(
            "Documentation", ["Complete", "Partial", "Incomplete"]
        )
        gram_sabha_resolution = st.selectbox(
            "Gram Sabha", ["Passed", "Pending", "Disputed", "Rejected"]
        )
        submitted = st.form_submit_button("Score claim")
    if submitted:
        claim = {
            "state": state,
            "district": district,
            "claim_type": claim_type,
            "applicant_type": applicant_type,
            "land_area_ha": land_area_ha,
            "forest_density_class": forest_density_class,
            "year_filed": int(year_filed),
            "documentation_completeness": documentation_completeness,
            "gram_sabha_resolution": gram_sabha_resolution,
            "processing_days": 180,
            "committee_level_reached": "FRC",
        }
        try:
            rec = recommend(claim)
            st.subheader(f"Predicted: {rec.predicted_status}")
            st.json(rec.probabilities)
            st.write(f"Confidence {rec.confidence}, human review: {rec.human_review}")
            for d in rec.shap_drivers:
                st.write(f"- {d.sentence}")
            if rec.what_if:
                st.subheader("What-if (actionable fields only)")
                st.table([w.model_dump() for w in rec.what_if])
            if rec.eta_days_point:
                st.write(f"ETA (point): {rec.eta_days_point} days")
            st.subheader("Schemes")
            st.json(rec.schemes)
        except Exception as exc:
            st.error(f"Model not ready: {exc}")

elif page == "Rejection Root Cause":
    metrics = _load_json("rejection_reason_metrics.json")
    st.write(metrics.get("note", ""))
    st.json(metrics.get("metrics", {}))
    rem = json.loads((ML_ROOT / "configs" / "remediation.yaml").read_text(encoding="utf-8")) if False else {}
    st.caption("Remediation texts are demo guidance only.")

elif page == "Backlog Triage Queue":
    st.write(
        "Triage score = 0.45*P(reject) + 0.35*delay_norm + 0.20*age_norm "
        "(weights in configs/dss_weights.yaml)."
    )
    try:
        df = load_claims(mode="fast")
        pending = df[df["status"] == "Pending"].head(50)
        st.dataframe(pending[["state", "district", "claim_type", "processing_days", "year_filed"]])
    except Exception as exc:
        st.error(str(exc))

elif page == "District Priority":
    prio_path = REPO_ROOT / "backend" / "models" / "priority_by_district.json"
    if prio_path.exists():
        rows = json.loads(prio_path.read_text(encoding="utf-8"))
        st.dataframe(pd.DataFrame(rows).head(30))
        html = FIGURES_DIR / "30_district_priority_map.html"
        if html.exists():
            st.components.v1.html(html.read_text(encoding="utf-8"), height=400)
    else:
        st.info("Run training to generate priority_by_district.json")

elif page == "Model Benchmark":
    csv_path = METRICS_DIR / "benchmark_master.csv"
    if csv_path.exists():
        bench = pd.read_csv(csv_path)
        st.dataframe(bench.sort_values("s1_macro_f1_mean", ascending=False))
        fig = FIGURES_DIR / "10_leaderboard_set_a.png"
        if fig.exists():
            st.image(str(fig))
        gap = FIGURES_DIR / "11_feature_set_gap.png"
        if gap.exists():
            st.image(str(gap))
    else:
        st.info("Run the benchmark first.")

elif page == "Explainability":
    fig = FIGURES_DIR / "20_shap_bar.png"
    if fig.exists():
        st.image(str(fig))
    else:
        st.info("SHAP bar figure appears after a scored claim / training run.")
    st.write("Surrogate and PDP metrics live under reports/metrics/.")

else:
    st.markdown(
        """
### About
Team Evonex, SIH 2025, SIH12508 (Ministry of Tribal Affairs).

This package trains on **synthetic** FRA claims. See `ml/DATA_CARD.md` and `ml/MODEL_CARD.md`.

Intended use: academic mini-project demo and officer-facing prototyping.
"""
    )
    st.warning(DISCLOSURE)

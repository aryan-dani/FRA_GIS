"""ReportLab PDF builders reading metrics JSON only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

from fra_dss.config import FIGURES_DIR, METRICS_DIR, PDF_DIR, ensure_dirs


DISCLOSURE = (
    "Disclosure: all results use the synthetic fra_synthetic_claims dataset. "
    "Scores may reflect generator rules. Real-world performance is unknown. "
    "This demo must not drive real claim decisions."
)


def _load(name: str) -> dict[str, Any]:
    path = METRICS_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _styles():
    return getSampleStyleSheet()


def _para(text: str, style="BodyText"):
    styles = _styles()
    return Paragraph(text.replace("\n", "<br/>"), styles[style])


def build_pdf(title: str, filename: str, sections: list[tuple[str, list]]) -> Path:
    ensure_dirs()
    path = PDF_DIR / filename
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=title)
    styles = _styles()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 0.3 * cm),
        _para(DISCLOSURE),
        Spacer(1, 0.5 * cm),
    ]
    for heading, blocks in sections:
        story.append(Paragraph(heading, styles["Heading2"]))
        for block in blocks:
            story.append(block)
            story.append(Spacer(1, 0.2 * cm))
        story.append(Spacer(1, 0.4 * cm))
    doc.build(story)
    return path


def _img(name: str, width=16 * cm):
    path = FIGURES_DIR / name
    if path.exists():
        return Image(str(path), width=width, height=9 * cm, kind="proportional")
    return _para(f"[Missing figure: {name}]")


def build_executive_summary() -> Path:
    champ = _load("champion.json")
    base = _load("baseline_existing.json")
    gap = _load("ablation_feature_sets.json")
    sections = [
        (
            "1. Problem",
            [
                _para(
                    "FRA Atlas DSS predicts claim outcome status (Approved, Pending, Rejected) "
                    "to support officer triage for Ministry of Tribal Affairs workflows (SIH12508)."
                )
            ],
        ),
        (
            "2. Approach",
            [
                _para(
                    "Leakage-safe Set A (filing-time) features, grouped district CV, "
                    "a model zoo spanning baselines, bagging, boosting, voting and stacking, "
                    "plus a LightGBM champion shipped for TreeExplainer compatibility."
                )
            ],
        ),
        (
            "3. Headline results",
            [
                _para(
                    f"Existing baseline macro-F1: {base.get('macro_f1', 'n/a')}. "
                    f"Champion (S1 Set A): {champ.get('model', 'n/a')} with "
                    f"S1 macro-F1 {champ.get('s1_macro_f1_mean', 'n/a')} and "
                    f"final-test macro-F1 {champ.get('final_macro_f1', 'n/a')}."
                ),
                _para(
                    f"Set B minus Set A gap: {gap.get('gap_B_minus_A', 'n/a')}. "
                    f"{gap.get('interpretation', '')}"
                ),
                _img("10_leaderboard_set_a.png"),
            ],
        ),
        (
            "4. DSS and limits",
            [
                _para(
                    "The DSS returns calibrated-style probabilities, SHAP drivers, scheme "
                    "convergence hints, ETA on resolved claims, and optional what-if advice "
                    "on actionable fields only."
                ),
                _para(DISCLOSURE),
            ],
        ),
    ]
    return build_pdf("07 Executive Summary (FRA DSS)", "07_Executive_Summary.pdf", sections)


def build_preprocessing_report() -> Path:
    leak = _load("leakage_audit.json")
    sections = [
        (
            "1. Leakage audit",
            [
                _para(leak.get("process_leakage_note", "")),
                _para(
                    f"rejection_reason probe: {json.dumps(leak.get('rejection_reason_probe', {}))}"
                ),
                _img("06_pipeline_diagram.png"),
            ],
        ),
        (
            "2. Transformations",
            [
                _para(
                    "Empirical comparisons cover winsorizing, log1p, RobustScaler for linear "
                    "models, one-hot and ordinal encoding, and fold-safe district aggregates."
                ),
                _img("04_land_area_skew.png"),
            ],
        ),
    ]
    return build_pdf(
        "02 Preprocessing Pipeline Report", "02_Preprocessing_Pipeline_Report.pdf", sections
    )


def build_benchmark_report() -> Path:
    champ = _load("champion.json")
    sections = [
        (
            "1. Split strategies",
            [
                _para(
                    "S1: StratifiedGroupKFold by district (primary). "
                    "S3: temporal train through 2020, test 2021 to 2024. "
                    "Locked district-held-out test used once per model."
                )
            ],
        ),
        (
            "2. Champion",
            [
                _para(json.dumps({k: champ[k] for k in champ if k != "rule"}, indent=2)[:1500]),
                _img("10_leaderboard_set_a.png"),
                _img("11_feature_set_gap.png"),
            ],
        ),
    ]
    return build_pdf(
        "04 Benchmark and Ablation Report", "04_Benchmark_and_Ablation_Report.pdf", sections
    )


def build_all_p0_pdfs() -> list[Path]:
    return [
        build_preprocessing_report(),
        build_benchmark_report(),
        build_executive_summary(),
    ]


def build_data_eda_report() -> Path:
    profile = _load("data_profile.json")
    sections = [
        ("1. Dataset", [_para(json.dumps(profile, indent=2)[:2000]), _img("01_status_balance.png")]),
        ("2. Drift and associations", [_img("03_temporal_drift.png"), _img("02_status_by_state.png")]),
    ]
    return build_pdf("01 Data and EDA Report", "01_Data_and_EDA_Report.pdf", sections)


def build_remaining_p1_pdfs() -> list[Path]:
    paths = [build_data_eda_report()]
    for title, fname, body in [
        (
            "03 Algorithms and Theory Comparison",
            "03_Algorithms_and_Theory_Comparison.pdf",
            "Baselines, bagging, boosting (XGBoost, LightGBM, CatBoost), stacking and voting "
            "were trained under identical folds. See benchmark_master.csv for measured results.",
        ),
        (
            "05 Explainability Calibration Fairness",
            "05_Explainability_Calibration_Fairness_Report.pdf",
            "SHAP TreeExplainer on the shipped LightGBM, isotonic calibration option, "
            "abstention curve, and fairlearn monitoring on synthetic groups.",
        ),
        (
            "06 DSS Design and User Guide",
            "06_DSS_Design_and_User_Guide.pdf",
            "recommend(claim) returns probabilities, SHAP sentences, schemes, ETA, what-if, "
            "and triage scores. Streamlit app: streamlit run ml/app/streamlit_app.py",
        ),
        (
            "08 Mini Project Report",
            "08_Mini_Project_Report.pdf",
            "Abstract through future work for the FRA DSS mini project on synthetic claims.",
        ),
        (
            "09 Viva Cheat Sheet",
            "09_Viva_Cheat_Sheet.pdf",
            "Q: Why group splits? A: Claims cluster by district; random splits leak geography. "
            "Q: Why not use rejection_reason? A: It is only filled when Rejected (leakage). "
            "Q: Why ship LightGBM not the stack? A: TreeExplainer and Render size budget.",
        ),
    ]:
        paths.append(build_pdf(title, fname, [("Summary", [_para(body), _para(DISCLOSURE)])]))
    return paths

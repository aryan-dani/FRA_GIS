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
    ext = _load("extended_stats.json")
    stats = ext.get("stats", {}) if isinstance(ext, dict) else {}
    boot = stats.get("bootstrap_ci", {})
    sections = [
        (
            "1. Split strategies",
            [
                _para(
                    "S1: StratifiedGroupKFold by district (primary). "
                    "S2: random stratified (optimistic). "
                    "S3: temporal train through 2020, test 2021 to 2024. "
                    "S4: leave-one-state-out. "
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
        (
            "3. Extended tests",
            [
                _para(
                    f"McNemar (champion vs runner-up): {json.dumps(stats.get('mcnemar', {}))}."
                ),
                _para(
                    f"Bootstrap 95% CI macro-F1: {json.dumps(boot)[:800]}"
                ),
                _para(
                    f"Friedman/Nemenyi: {json.dumps(stats.get('friedman_nemenyi', {}))[:800]}"
                ),
                _img("14_s1_vs_s3.png"),
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
    bench_csv = METRICS_DIR / "benchmark_master.csv"
    bench_snip = ""
    if bench_csv.exists():
        import pandas as pd

        b = pd.read_csv(bench_csv)
        a = b[(b["feature_set"] == "A") & b["s1_macro_f1_mean"].notna()].sort_values(
            "s1_macro_f1_mean", ascending=False
        ).head(8)
        lines = [
            f"{r.model}: S1={r.s1_macro_f1_mean:.3f}, final={r.final_macro_f1:.3f}"
            for r in a.itertuples()
        ]
        bench_snip = "; ".join(lines)

    champ = _load("champion.json")
    gap = _load("ablation_feature_sets.json")
    ext = _load("extended_stats.json")
    conf = _load("conformal.json")
    mota = _load("mota_forecast.json")
    eta = _load("eta_metrics.json")
    reasons = _load("rejection_reason_metrics.json")
    fair_note = (
        "Fairness metrics are a monitoring exercise on synthetic groups "
        "(state, applicant type, claim type, forest density)."
    )

    paths.append(
        build_pdf(
            "03 Algorithms and Theory Comparison",
            "03_Algorithms_and_Theory_Comparison.pdf",
            [
                (
                    "1. Families evaluated",
                    [
                        _para(
                            "Baselines (dummy, logistic, naive Bayes, KNN, SGD/SVM, tree, MLP), "
                            "bagging (Bagging, Random Forest, Extra Trees), "
                            "boosting (AdaBoost, GradientBoosting, HistGB, XGBoost, LightGBM, CatBoost), "
                            "and ensembles (soft voting, stacking)."
                        ),
                        _para(
                            "Trees partition the feature space greedily. Bagging averages high-variance "
                            "trees. Boosting fits residuals sequentially. Stacking trains a meta-learner "
                            "on out-of-fold base predictions to avoid leakage into the meta stage."
                        ),
                    ],
                ),
                (
                    "2. Measured results (from metrics files)",
                    [
                        _para(bench_snip or "See benchmark_master.csv."),
                        _img("10_leaderboard_set_a.png"),
                        _img("16_bagging_variance.png"),
                        _img("17_boosting_lr.png"),
                    ],
                ),
                (
                    "3. Complexity notes",
                    [
                        _para(
                            "Linear models scale well and need scaling. Tree ensembles tolerate raw "
                            "scales. Stacking is slower (cross-fitted bases). Slow models (KNN, MLP, "
                            "sklearn GBT) use documented train subsamples in CV."
                        )
                    ],
                ),
            ],
        )
    )
    paths.append(
        build_pdf(
            "05 Explainability Calibration Fairness",
            "05_Explainability_Calibration_Fairness_Report.pdf",
            [
                (
                    "1. Explainability",
                    [
                        _para(
                            "The shipped artifact uses LightGBM so TreeExplainer applies. "
                            "Global and local SHAP drivers are shown in the DSS and Streamlit app."
                        ),
                        _img("20_shap_bar.png"),
                        _img("12_confusion_lightgbm.png"),
                    ],
                ),
                (
                    "2. Calibration and abstention",
                    [
                        _para(
                            f"Conformal (if run): coverage="
                            f"{conf.get('empirical_coverage', 'n/a')}, "
                            f"mean set size={conf.get('mean_set_size', 'n/a')}, "
                            f"target={conf.get('target_coverage', 'n/a')}."
                        ),
                        _img("21_abstention.png"),
                    ],
                ),
                (
                    "3. Fairness monitoring",
                    [
                        _para(fair_note),
                        _para(
                            "Do not automate rejections from these scores. Low-confidence cases "
                            "should go to human review."
                        ),
                    ],
                ),
            ],
        )
    )
    paths.append(
        build_pdf(
            "06 DSS Design and User Guide",
            "06_DSS_Design_and_User_Guide.pdf",
            [
                (
                    "1. Architecture",
                    [
                        _para(
                            "fra_dss.dss.engine.recommend(claim) combines: calibrated-style "
                            "probabilities, SHAP sentences, optional rejection reasons, what-if "
                            "on actionable fields only, ETA on resolved-trained regressor, "
                            "scheme_rules from the Flask backend, and audit flags."
                        ),
                        _para(
                            "Triage score = 0.45*P(reject) + 0.35*delay_norm + 0.20*age_norm "
                            "(configs/dss_weights.yaml)."
                        ),
                    ],
                ),
                (
                    "2. How to run",
                    [
                        _para(
                            "streamlit run ml/app/streamlit_app.py inside ml/.venv. "
                            "Flask additive routes: /api/dss/benchmark, /reasons, /what-if, /eta, /triage."
                        ),
                        _para(
                            f"ETA champion: {eta.get('champion', 'n/a')}. "
                            f"Rejection-reason champion: {reasons.get('champion', 'n/a')}."
                        ),
                    ],
                ),
            ],
        )
    )
    paths.append(
        build_pdf(
            "08 Mini Project Report",
            "08_Mini_Project_Report.pdf",
            [
                (
                    "Abstract",
                    [
                        _para(
                            "We build a leakage-aware claim-outcome DSS on synthetic FRA claims "
                            "for SIH12508. Filing-time (Set A) models are compared with "
                            "process-aware (Set B) models under grouped district CV."
                        )
                    ],
                ),
                (
                    "Methods",
                    [
                        _para(
                            f"Champion by S1 macro-F1 on Set A: {champ.get('model', 'n/a')} "
                            f"(S1={champ.get('s1_macro_f1_mean', 'n/a')}, "
                            f"final={champ.get('final_macro_f1', 'n/a')}). "
                            f"Set B minus A gap: {gap.get('gap_B_minus_A', 'n/a')}."
                        ),
                        _img("15_ablation_sets.png"),
                        _img("11_feature_set_gap.png"),
                    ],
                ),
                (
                    "Results and discussion",
                    [
                        _para(
                            "Random splits (S2) are optimistic versus district-grouped S1. "
                            "Temporal S3 and leave-one-state-out S4 stress distribution shift."
                        ),
                        _para(
                            f"Extended stats present: {bool(ext)}. "
                            f"MoTA forecast caveat: {mota.get('caveat', 'n/a')[:240]}"
                        ),
                    ],
                ),
                (
                    "Limitations",
                    [
                        _para(DISCLOSURE),
                        _para(
                            "High scores may reflect generator rules. Real-world performance is unknown."
                        ),
                    ],
                ),
            ],
        )
    )
    paths.append(
        build_pdf(
            "09 Viva Cheat Sheet",
            "09_Viva_Cheat_Sheet.pdf",
            [
                (
                    "Likely questions",
                    [
                        _para(
                            "Q1. Bias vs variance? "
                            "A: Single trees high variance; bagging reduces variance; "
                            "boosting reduces bias but can overfit; we compare families on S1."
                        ),
                        _para(
                            "Q2. Why grouped splits? "
                            "A: Claims cluster by district; random CV leaks geography and inflates scores."
                        ),
                        _para(
                            "Q3. Why not rejection_reason? "
                            "A: Non-null only when Rejected: perfect target leakage for status."
                        ),
                        _para(
                            "Q4. Why Set B looks better? "
                            f"A: Gap {gap.get('gap_B_minus_A', 'n/a')}. Process features are partly "
                            "consequences of outcome (committee level, processing days)."
                        ),
                        _para(
                            "Q5. Why ship LightGBM if XGBoost wins S1? "
                            "A: TreeExplainer + Render size. Leaderboard champion is separate from "
                            "the Flask contract artifact."
                        ),
                        _para(
                            "Q6. What is calibration? "
                            "A: Predicted probabilities should match empirical frequencies; "
                            "we also report abstention and optional conformal sets."
                        ),
                        _para(
                            "Q7. Why OOF for stacking? "
                            "A: Meta-learner must not see in-fold base predictions of the same rows."
                        ),
                        _para(
                            "Q8. Synthetic data? "
                            "A: Scores may mirror generator rules; must not decide real claims."
                        ),
                        _para(
                            "Q9. ETA on Pending? "
                            "A: Trained on Approved/Rejected only; Pending days may be right-censored."
                        ),
                        _para(
                            "Q10. Fairness? "
                            "A: Monitoring on synthetic groups only; never automate rejections."
                        ),
                    ],
                ),
            ],
        )
    )
    return paths

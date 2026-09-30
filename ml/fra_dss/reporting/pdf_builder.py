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


def _link(url: str, label: str | None = None) -> Paragraph:
    text = label or url
    return _para(f'<link href="{url}" color="blue"><u>{text}</u></link>')


def _metric_table(rows: list[list[str]], col_widths: list[float] | None = None):
    table = Table(rows, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e3d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.Color(0.93, 0.95, 0.93)]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def build_academic_style_report() -> Path:
    """Single PDF: abstract through references, driven by metrics JSON/CSV and figures."""
    import pandas as pd

    champ = _load("champion.json")
    gap = _load("ablation_feature_sets.json")
    prov = _load("run_provenance.json")
    conf = _load("conformal.json")
    ext = _load("extended_stats.json")
    base = _load("baseline_existing.json")
    timing = _load("run_timing.json")

    n_rows = prov.get("n_rows", "n/a")
    mode = prov.get("mode", "n/a")
    champ_model = champ.get("model", "n/a")
    s1 = champ.get("s1_macro_f1_mean", "n/a")
    final_f1 = champ.get("final_macro_f1", "n/a")
    gap_ba = gap.get("gap_B_minus_A", "n/a")
    cov = conf.get("empirical_coverage", "n/a")
    set_sz = conf.get("mean_set_size", "n/a")

    leader_rows: list[list[str]] = [
        ["Model (Set A)", "S1 macro-F1", "Final macro-F1", "S3 macro-F1", "Latency ms/1k"]
    ]
    bench_csv = METRICS_DIR / "benchmark_master.csv"
    if bench_csv.exists():
        b = pd.read_csv(bench_csv)
        a = b[(b["feature_set"] == "A") & b["s1_macro_f1_mean"].notna()].sort_values(
            "s1_macro_f1_mean", ascending=False
        ).head(12)
        for r in a.itertuples():
            leader_rows.append(
                [
                    str(r.model),
                    f"{r.s1_macro_f1_mean:.4f}",
                    f"{r.final_macro_f1:.4f}",
                    f"{r.s3_macro_f1:.4f}",
                    f"{r.latency_ms_per_1k:.2f}",
                ]
            )

    s2_snip = "See extended_stats.json."
    s4_snip = ""
    if ext.get("s2"):
        parts = [
            f"{x['model']} S2={x['s2_macro_f1_mean']:.3f} (optimism vs S1={x.get('optimism_vs_s1', 0):+.3f})"
            for x in ext["s2"][:6]
        ]
        s2_snip = "; ".join(parts)
    if ext.get("s4"):
        parts = [f"{x['model']} S4={x['s4_macro_f1_mean']:.3f}" for x in ext["s4"][:6]]
        s4_snip = "; ".join(parts)

    # APS (American Physical Society) bibliographic style for the Adaptive Prediction Sets paper.
    aps_ref_name = "Classification with Valid and Adaptive Coverage"
    aps_cite = (
        "Y. Romano, M. Sesia, and E. J. Candès, Classification with valid and adaptive coverage, "
        "Adv. Neural Inf. Process. Syst. <b>33</b>, 3581 (2020)."
    )
    aps_url = "https://arxiv.org/abs/2006.02544"

    sections = [
        (
            "Abstract",
            [
                _para(
                    f"We present a leakage-aware decision-support system (DSS) for Forest Rights Act "
                    f"(FRA) claim-outcome triage (SIH12508). On a synthetic corpus of {n_rows} claims "
                    f"(run mode={mode}), filing-time feature Set A is compared with process-aware Set B "
                    f"under district-grouped cross-validation. The pre-declared champion rule "
                    f"(highest S1 macro-F1 on Set A) selects <b>{champ_model}</b> "
                    f"(S1 macro-F1={s1}; locked final-test macro-F1={final_f1}). "
                    f"The deployable Flask artifact remains LightGBM for TreeExplainer compatibility. "
                    f"Set B minus Set A gap is {gap_ba}, indicating circular lift from process fields. "
                    f"Split-conformal prediction sets (APS-style nonconformity) achieve empirical "
                    f"coverage {cov} with mean set size {set_sz}."
                ),
                _para(DISCLOSURE),
            ],
        ),
        (
            "1. Introduction",
            [
                _para(
                    "Ministry of Tribal Affairs workflows need early risk signals for FRA claims "
                    "(Approved, Pending, Rejected) without using post-decision leakage. Prior "
                    f"internal baselines report macro-F1 about {base.get('macro_f1', 'n/a')}. "
                    "This work (i) audits leakage via Set A/B/C ablations, (ii) benchmarks a broad "
                    "model zoo with grouped CV, (iii) ships a calibrated DSS with SHAP drivers, "
                    "scheme hints, ETA, and conformal abstention sets, and (iv) documents results "
                    "from metrics files only."
                ),
                _para(
                    "Repository and live metrics: "
                    '<link href="https://github.com/aryan-dani/FRA_GIS/tree/feat/ml-dss" color="blue">'
                    "<u>github.com/aryan-dani/FRA_GIS (feat/ml-dss)</u></link>. "
                    "Raw tables live under ml/reports/metrics/; figures under ml/reports/figures/."
                ),
            ],
        ),
        (
            "2. Mathematical formulation",
            [
                _para(
                    "<b>Multiclass status.</b> Labels y ∈ {Approved, Pending, Rejected}. "
                    "For class c, precision P_c = TP_c / (TP_c + FP_c), recall R_c = TP_c / (TP_c + FN_c), "
                    "and F1_c = 2 P_c R_c / (P_c + R_c). Macro-F1 = (1/C) Σ_c F1_c with C=3."
                ),
                _para(
                    "<b>Log loss.</b> L = −(1/n) Σ_i Σ_c 1[y_i=c] log p̂_i(c)."
                ),
                _para(
                    "<b>Soft voting.</b> For base models m=1..M with probabilities p̂^(m), "
                    "p̂_ens(c|x) = (1/M) Σ_m p̂^(m)(c|x)."
                ),
                _para(
                    "<b>Triage score (DSS).</b> "
                    "S = 0.45 P̂(Rejected) + 0.35 delay_norm + 0.20 age_norm, "
                    "with delay_norm and age_norm capped per configs/dss_weights.yaml."
                ),
                _para(
                    "<b>Split-conformal / APS-style scores.</b> Nonconformity s(x,y) = 1 − p̂(y|x). "
                    "On a calibration set of size n_cal, q̂ is the "
                    "ceil((n_cal+1)(1−α)) / n_cal empirical quantile of s(x_i, y_i). "
                    f"Prediction set C(x) = {{ y : s(x,y) ≤ q̂ }} with α={conf.get('alpha', 0.1)} "
                    f"(target coverage {conf.get('target_coverage', 0.9)}). "
                    f"Observed coverage={cov}, mean |C|={set_sz}, q̂={conf.get('qhat', 'n/a')}."
                ),
                _para(
                    "This conformal construction follows the Adaptive Prediction Sets (APS) line of work; "
                    f"canonical reference title: <b>{aps_ref_name}</b> (see References, APS style)."
                ),
            ],
        ),
        (
            "3. Methodology diagram",
            [
                _para(
                    "Pipeline: synthetic load → schema/leakage audit → Set A/B feature matrices → "
                    "locked district holdout → S1 grouped CV zoo (cached OOF) → champion by S1 Set A → "
                    "ship LightGBM contract artifact → auxiliary ETA/reasons → conformal + DSS → PDFs."
                ),
                _img("06_pipeline_diagram.png"),
                _para(
                    f"Full-run wall time: {timing.get('wall_seconds', 'n/a')} s "
                    f"(mode={timing.get('mode', mode)})."
                ),
            ],
        ),
        (
            "4. Experimental setup",
            [
                _para(
                    f"n={n_rows}, seed={prov.get('seed', 42)}, synthetic={prov.get('synthetic', True)}. "
                    f"Dataset SHA-256 prefix: {str(prov.get('dataset_sha256', ''))[:16]}…. "
                    "S1: GroupKFold by district. S2: stratified random (optimism check). "
                    "S3: temporal. S4: leave-one-state-out. Final metrics use the locked district holdout."
                ),
                _para(
                    "Hyperlinks to metric artifacts (local paths in the repo):"
                ),
                _link(
                    "https://github.com/aryan-dani/FRA_GIS/blob/feat/ml-dss/ml/reports/metrics/benchmark_master.csv",
                    "benchmark_master.csv (all model scores)",
                ),
                _link(
                    "https://github.com/aryan-dani/FRA_GIS/blob/feat/ml-dss/ml/reports/metrics/champion.json",
                    "champion.json (S1 selection)",
                ),
                _link(
                    "https://github.com/aryan-dani/FRA_GIS/blob/feat/ml-dss/ml/reports/metrics/extended_stats.json",
                    "extended_stats.json (S2/S4, McNemar, bootstrap)",
                ),
                _link(
                    "https://github.com/aryan-dani/FRA_GIS/blob/feat/ml-dss/ml/reports/metrics/conformal.json",
                    "conformal.json (APS-style coverage)",
                ),
            ],
        ),
        (
            "5. Experimental results",
            [
                _para(
                    f"Champion (rule: S1 macro-F1 on Set A): <b>{champ_model}</b>. "
                    f"S1={s1} ± {champ.get('s1_macro_f1_std', 'n/a')}; "
                    f"final macro-F1={final_f1}; final accuracy={champ.get('final_accuracy', 'n/a')}; "
                    f"S3 macro-F1={champ.get('s3_macro_f1', 'n/a')}."
                ),
                _metric_table(leader_rows, col_widths=[3.2 * cm, 2.8 * cm, 3.0 * cm, 2.8 * cm, 2.8 * cm]),
                _img("10_leaderboard_set_a.png"),
                _img("11_feature_set_gap.png"),
                _para(
                    f"Ablation: Set A macro-F1≈{gap.get('A', {}).get('macro_f1', 'n/a')}; "
                    f"Set B≈{gap.get('B', {}).get('macro_f1', 'n/a')}; gap B−A={gap_ba}. "
                    f"{gap.get('interpretation', '')}"
                ),
                _img("15_ablation_sets.png"),
            ],
        ),
        (
            "6. Performance analysis",
            [
                _para(
                    f"<b>Random vs grouped CV.</b> {s2_snip} "
                    "Positive optimism_vs_s1 means random S2 overstates deployable accuracy."
                ),
                _para(f"<b>State shift (S4).</b> {s4_snip or 'See s4_leave_one_state.csv.'}"),
                _para(
                    "<b>Latency–accuracy.</b> Boosting models are typically faster per 1k rows than "
                    "bagging/stacking; see Pareto figure. Shipped LightGBM balances explainability "
                    "and size even when bagging wins the S1 selection rule on full data."
                ),
                _img("13_pareto_latency.png"),
                _img("14_s1_vs_s3.png"),
                _img("12_confusion_lightgbm.png"),
                _para(
                    f"<b>Uncertainty.</b> Conformal coverage {cov} (target "
                    f"{conf.get('target_coverage', 0.9)}); mean set size {set_sz}. "
                    "Larger sets flag cases for human review."
                ),
                _img("21_abstention.png"),
                _img("20_shap_bar.png"),
            ],
        ),
        (
            "7. References (APS style)",
            [
                _para(
                    f"[1] {aps_cite} "
                    f'Reference paper name: <b>"{aps_ref_name}"</b>. '
                    f'Link: <link href="{aps_url}" color="blue"><u>{aps_url}</u></link>.'
                ),
                _para(
                    "[2] G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu, "
                    "LightGBM: A highly efficient gradient boosting decision tree, "
                    "Adv. Neural Inf. Process. Syst. <b>30</b>, 3146 (2017). "
                    '<link href="https://papers.nips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html" '
                    'color="blue"><u>NeurIPS 2017</u></link>.'
                ),
                _para(
                    "[3] T. Chen and C. Guestrin, XGBoost: A scalable tree boosting system, "
                    "in Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge "
                    "Discovery and Data Mining (ACM, New York, 2016), p. 785."
                ),
                _para(
                    "[4] V. Vovk, A. Gammerman, and G. Shafer, Algorithmic Learning in a Random World "
                    "(Springer, New York, 2005)."
                ),
                _para(
                    "[5] A. N. Angelopoulos and S. Bates, A gentle introduction to conformal prediction "
                    "and distribution-free uncertainty quantification, arXiv:2107.07511."
                ),
                _para(DISCLOSURE),
            ],
        ),
    ]
    return build_pdf(
        "10 Academic Style Report (FRA DSS ML)",
        "10_Academic_Style_Report.pdf",
        sections,
    )


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
    paths = [build_data_eda_report(), build_academic_style_report()]
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

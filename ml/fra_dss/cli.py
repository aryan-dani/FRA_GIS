"""CLI: python -m fra_dss.cli run-all --mode fast|full."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from fra_dss.config import METRICS_DIR, MODELS_DIR, SEED, ensure_dirs
from fra_dss.data import (
    audit_leakage,
    load_claims,
    load_raw_claims,
    provenance,
    validate_claims,
    write_json,
)
from fra_dss.data.load import dataset_sha256, git_sha
from fra_dss.evaluation.ablation import feature_set_ablation
from fra_dss.evaluation.cv import run_benchmark
from fra_dss.models.reasons import train_rejection_reasons, train_resolved_binary
from fra_dss.models.regression import train_eta_models
from fra_dss.models.registry import (
    STATUS_LABELS,
    aggregate_priority,
    compute_district_freq,
    export_contract_artifact,
)
from fra_dss.models.tuning import tune_lightgbm
from fra_dss.models.zoo import build_estimator
from fra_dss.preprocessing.pipelines import build_preprocessor, pipeline_diagram_steps, select_frame
from fra_dss.reporting.pdf_builder import build_all_p0_pdfs, build_remaining_p1_pdfs
from fra_dss.reporting.tables import write_markdown_table
from fra_dss.unsupervised.segmentation import claim_anomalies, segment_districts
from fra_dss.viz.eda import (
    save_docs_reject,
    save_land_skew,
    save_status_by_state,
    save_target_balance,
    save_temporal_drift,
)
from fra_dss.viz.model_plots import save_feature_set_gap, save_leaderboard, save_pipeline_diagram
from fra_dss.viz.maps import save_priority_map_html


def capture_baseline() -> dict:
    """Record existing trainer metrics if backend metrics exist; else recompute lightly."""
    ensure_dirs()
    backend_metrics = Path(__file__).resolve().parents[2] / "backend" / "models" / "metrics.json"
    # parents: fra_dss -> ml -> repo, so parents[2] is wrong. ML_ROOT parent is repo.
    from fra_dss.config import REPO_ROOT

    backend_metrics = REPO_ROOT / "backend" / "models" / "metrics.json"
    payload = {
        "source": "backend/models/metrics.json" if backend_metrics.exists() else "pending",
        "dataset_sha256": dataset_sha256(),
        "git_sha": git_sha(),
        "synthetic": True,
    }
    if backend_metrics.exists():
        existing = json.loads(backend_metrics.read_text(encoding="utf-8"))
        payload.update(
            {
                "accuracy": existing.get("accuracy"),
                "macro_f1": existing.get("macro_f1"),
                "per_class_recall": existing.get("per_class_recall"),
                "model": existing.get("model", "LGBMClassifier"),
                "holdout": existing.get("holdout"),
            }
        )
    write_json(METRICS_DIR / "baseline_existing.json", payload)
    return payload


def train_and_export_champion(df: pd.DataFrame, mode: str) -> Path:
    """Train LightGBM on prepare_features frame so Flask contract stays intact."""
    import sys
    from fra_dss.config import REPO_ROOT

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from ml.features import prepare_features
    from fra_dss.models.registry import build_contract_preprocessor

    le = LabelEncoder()
    le.fit(STATUS_LABELS)
    y = le.transform(df["status"].astype(str))
    district_freq = compute_district_freq(df["district"])
    X = prepare_features(df, district_freq=district_freq)
    preprocessor = build_contract_preprocessor()
    model = build_estimator("lightgbm", mode)
    Xt = preprocessor.fit_transform(X, y)
    model.fit(Xt, y)
    metrics = {
        "n_rows": int(len(df)),
        "mode": mode,
        "accuracy": None,
        "macro_f1": None,
        "model": "LGBMClassifier",
        "feature_set": "A_contract",
        "synthetic": True,
        "dataset_sha256": dataset_sha256(),
        "git_sha": git_sha(),
        "holdout": "See ml/reports/metrics for grouped CV; artifact refit on run sample",
    }
    champ_path = METRICS_DIR / "champion.json"
    if champ_path.exists():
        champ = json.loads(champ_path.read_text(encoding="utf-8"))
        metrics["macro_f1"] = champ.get("final_macro_f1")
        metrics["accuracy"] = champ.get("final_accuracy")
        metrics["s1_macro_f1"] = champ.get("s1_macro_f1_mean")

    priority = aggregate_priority(df)
    path = export_contract_artifact(
        model=model,
        preprocessor=preprocessor,
        label_encoder=le,
        district_freq=district_freq,
        metrics=metrics,
        priority_rows=priority,
    )
    save_priority_map_html(priority)
    return path


def run_all(mode: str = "fast", include_p1: bool = True) -> None:
    t0 = time.perf_counter()
    ensure_dirs()
    print(f"=== FRA DSS run-all mode={mode} ===")
    capture_baseline()

    raw = load_raw_claims()
    profile = validate_claims(raw)
    write_json(METRICS_DIR / "data_profile.json", profile)

    df = load_claims(mode=mode)
    write_json(METRICS_DIR / "run_provenance.json", provenance(mode, len(df)))

    print("Leakage audit...")
    audit_leakage(df)

    print("EDA figures...")
    save_target_balance(df)
    save_status_by_state(df)
    save_temporal_drift(df)
    save_land_skew(df)
    save_docs_reject(df)
    save_pipeline_diagram(pipeline_diagram_steps("A"))

    print("Ablation...")
    le = LabelEncoder()
    le.fit(STATUS_LABELS)
    y = le.transform(df["status"].astype(str))
    abl = feature_set_ablation(df, y, mode=mode)
    write_json(METRICS_DIR / "ablation_feature_sets.json", abl)

    print("Benchmark zoo...")
    bench = run_benchmark(mode=mode, include_p1=include_p1, feature_sets=["A", "B"])
    if len(bench):
        save_leaderboard(bench)
        save_feature_set_gap(bench)
        write_markdown_table(
            bench.sort_values("s1_macro_f1_mean", ascending=False).head(20),
            "leaderboard_top20.md",
        )

    print("Train shipped LightGBM artifact...")
    train_and_export_champion(df, mode)

    print("Auxiliary tasks...")
    eta = train_eta_models(df, mode=mode)
    write_json(
        METRICS_DIR / "eta_metrics.json",
        {k: v for k, v in eta.items() if k != "model"},
    )
    if eta.get("model") is not None:
        joblib.dump(eta["model"], MODELS_DIR / "eta_model.joblib")

    reasons = train_rejection_reasons(df, mode=mode)
    write_json(
        METRICS_DIR / "rejection_reason_metrics.json",
        {k: v for k, v in reasons.items() if k not in {"model", "label_encoder"}},
    )
    if reasons.get("model") is not None:
        joblib.dump(
            {"model": reasons["model"], "classes": reasons["classes"]},
            MODELS_DIR / "rejection_reason_model.joblib",
        )

    resolved = train_resolved_binary(df, mode=mode)
    write_json(
        METRICS_DIR / "resolved_binary_metrics.json",
        {k: v for k, v in resolved.items() if k != "model"},
    )
    if resolved.get("model") is not None:
        joblib.dump(resolved["model"], MODELS_DIR / "resolved_binary_model.joblib")

    print("Unsupervised...")
    seg = segment_districts(df)
    write_json(METRICS_DIR / "district_segmentation.json", seg["metrics"])
    write_json(METRICS_DIR / "anomaly_flags.json", claim_anomalies(df))

    # Optional Optuna
    try:
        X = build_preprocessor("A").fit_transform(select_frame(df, "A"), y)
        groups = df["district"].astype(str).to_numpy()
        study = tune_lightgbm(X, y, groups, mode=mode)
        write_json(METRICS_DIR / "optuna_lightgbm.json", study)
    except Exception as exc:
        write_json(METRICS_DIR / "optuna_lightgbm.json", {"error": str(exc)})

    print("PDFs...")
    build_all_p0_pdfs()
    if include_p1:
        build_remaining_p1_pdfs()

    elapsed = time.perf_counter() - t0
    write_json(
        METRICS_DIR / "run_timing.json",
        {"mode": mode, "wall_seconds": elapsed, "include_p1": include_p1},
    )
    print(f"=== Done in {elapsed / 60:.1f} min ===")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="fra-dss")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run-all")
    run.add_argument("--mode", choices=["fast", "full"], default="fast")
    run.add_argument("--p0-only", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "run-all":
        run_all(mode=args.mode, include_p1=not args.p0_only)


if __name__ == "__main__":
    main()

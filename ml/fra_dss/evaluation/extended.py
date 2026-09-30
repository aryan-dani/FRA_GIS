"""Extended splits (S2, S4), statistical tests, and bootstrap CIs."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from fra_dss.config import METRICS_DIR, SEED, ensure_dirs, mode_settings
from fra_dss.data.load import load_claims, write_json
from fra_dss.data.splits import iter_s2, leave_one_state_out, lock_splits
from fra_dss.evaluation.cv import _fit_eval_fold, _get_model
from fra_dss.evaluation.stats_tests import (
    bootstrap_ci,
    friedman_nemenyi,
    mcnemar_from_preds,
    paired_wilcoxon,
)
from fra_dss.preprocessing.pipelines import build_preprocessor, select_frame

STATUS_LABELS = ["Approved", "Pending", "Rejected"]

# Core models for extended stats (keep runtime tractable)
CORE_MODELS = [
    "lightgbm",
    "xgboost",
    "random_forest",
    "hist_gradient_boosting",
    "catboost",
    "soft_voting",
    "logistic_l2",
    "bagging",
]


def run_extended_evaluation(mode: str = "fast", feature_set: str = "A") -> dict[str, Any]:
    """S2, S4, Friedman/Nemenyi, Wilcoxon, McNemar, bootstrap on champion/runner-up."""
    ensure_dirs()
    df = load_claims(mode=mode)
    le = LabelEncoder()
    le.fit(STATUS_LABELS)
    y = le.transform(df["status"].astype(str))
    labels = STATUS_LABELS

    splits = lock_splits(df)
    train_idx, test_idx = splits["train"], splits["test"]
    df_train = df.iloc[train_idx].reset_index(drop=True)
    y_train = y[train_idx]
    df_test = df.iloc[test_idx].reset_index(drop=True)
    y_test = y[test_idx]
    X_train = select_frame(df_train, feature_set)
    X_test = select_frame(df_test, feature_set)

    # Load S1 fold scores from registry if available
    registry_path = METRICS_DIR / "benchmark_registry.json"
    registry = {}
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

    s2_rows: list[dict[str, Any]] = []
    s4_rows: list[dict[str, Any]] = []
    fold_matrix: list[list[float]] = []
    model_names: list[str] = []
    final_preds: dict[str, np.ndarray] = {}

    n_boot = int(mode_settings(mode).get("bootstrap_resamples", 200))

    for name in CORE_MODELS:
        print(f"[extended] {name} ...")
        try:
            # S2 random stratified
            s2_scores = []
            for tr, va in iter_s2(y_train, n_splits=5):
                m = _fit_eval_fold(
                    name, mode, feature_set,
                    X_train.iloc[tr], y_train[tr],
                    X_train.iloc[va], y_train[va],
                    labels,
                )
                s2_scores.append(m["macro_f1"])
            s2_rows.append(
                {
                    "model": name,
                    "feature_set": feature_set,
                    "s2_macro_f1_mean": float(np.mean(s2_scores)),
                    "s2_macro_f1_std": float(np.std(s2_scores)),
                    "optimism_vs_s1": None,
                }
            )

            # S4 leave-one-state-out on full loaded frame
            s4_scores = []
            X_full = select_frame(df, feature_set)
            for state, tr, te in leave_one_state_out(df):
                m = _fit_eval_fold(
                    name, mode, feature_set,
                    X_full.iloc[tr], y[tr],
                    X_full.iloc[te], y[te],
                    labels,
                )
                s4_scores.append({"state": state, "macro_f1": m["macro_f1"]})
            s4_rows.append(
                {
                    "model": name,
                    "feature_set": feature_set,
                    "s4_macro_f1_mean": float(np.mean([r["macro_f1"] for r in s4_scores])),
                    "s4_per_state": s4_scores,
                }
            )

            # Final preds for McNemar
            pipe = Pipeline(
                [
                    (
                        "pre",
                        build_preprocessor(
                            feature_set,
                            for_trees=name
                            not in {
                                "logistic_l2",
                                "logistic_elasticnet",
                                "knn",
                                "sgd_svm",
                                "mlp",
                                "naive_bayes",
                            },
                        ),
                    ),
                    ("model", _get_model(name, mode)),
                ]
            )
            pipe.fit(X_train, y_train)
            final_preds[name] = pipe.predict(X_test)

            # S1 folds from registry for Friedman
            cache_key = f"{mode}_{feature_set}_{name}"
            folds = (
                registry.get("models", {}).get(cache_key, {}).get("fold_macro_f1")
            )
            if folds and len(folds) >= 3:
                model_names.append(name)
                fold_matrix.append(folds)

            print(
                f"  S2={np.mean(s2_scores):.4f} S4={np.mean([r['macro_f1'] for r in s4_scores]):.4f}"
            )
        except Exception as exc:
            print(f"  [fail] {name}: {exc}")
            s2_rows.append({"model": name, "feature_set": feature_set, "error": str(exc)})

    # Optimism: S2 mean minus S1 mean from master bench
    bench_path = METRICS_DIR / "benchmark_master.csv"
    if bench_path.exists():
        bench = pd.read_csv(bench_path)
        for row in s2_rows:
            if "error" in row:
                continue
            match = bench[
                (bench["model"] == row["model"]) & (bench["feature_set"] == feature_set)
            ]
            if len(match) and pd.notna(match.iloc[0].get("s1_macro_f1_mean")):
                row["optimism_vs_s1"] = float(
                    row["s2_macro_f1_mean"] - match.iloc[0]["s1_macro_f1_mean"]
                )

    stats: dict[str, Any] = {"synthetic": True, "mode": mode, "feature_set": feature_set}

    if len(fold_matrix) >= 3:
        mat = np.array(fold_matrix).T  # folds x models
        # Align fold lengths
        min_folds = min(len(r) for r in fold_matrix)
        mat = np.array([r[:min_folds] for r in fold_matrix]).T
        stats["friedman_nemenyi"] = friedman_nemenyi(mat, model_names)

        if len(model_names) >= 2:
            a_idx, b_idx = 0, 1
            stats["wilcoxon_top_pair"] = {
                "a": model_names[a_idx],
                "b": model_names[b_idx],
                **paired_wilcoxon(
                    np.array(fold_matrix[a_idx][:min_folds]),
                    np.array(fold_matrix[b_idx][:min_folds]),
                ),
            }

    # McNemar + bootstrap on champion and runner-up from champion.json / bench
    champ = {}
    champ_path = METRICS_DIR / "champion.json"
    if champ_path.exists():
        champ = json.loads(champ_path.read_text(encoding="utf-8"))
    champ_name = champ.get("model", "xgboost")
    runner = "lightgbm" if champ_name != "lightgbm" else "xgboost"
    if champ_name in final_preds and runner in final_preds:
        stats["mcnemar"] = {
            "a": champ_name,
            "b": runner,
            **mcnemar_from_preds(y_test, final_preds[champ_name], final_preds[runner]),
        }
        stats["bootstrap_ci"] = {
            champ_name: bootstrap_ci(
                y_test,
                final_preds[champ_name],
                lambda yt, yp: f1_score(yt, yp, average="macro"),
                n_boot=n_boot,
                seed=SEED,
            ),
            runner: bootstrap_ci(
                y_test,
                final_preds[runner],
                lambda yt, yp: f1_score(yt, yp, average="macro"),
                n_boot=n_boot,
                seed=SEED,
            ),
            "n_boot": n_boot,
        }

    report = {
        "s2": s2_rows,
        "s4": s4_rows,
        "stats": stats,
        "disclosure": (
            "Synthetic data. S2 random splits are optimistic versus S1 grouped splits."
        ),
    }
    write_json(METRICS_DIR / "extended_stats.json", report)
    pd.DataFrame(
        [{k: v for k, v in r.items() if k != "s4_per_state"} for r in s4_rows if "error" not in r]
    ).to_csv(METRICS_DIR / "s4_leave_one_state.csv", index=False)
    pd.DataFrame([r for r in s2_rows if "error" not in r]).to_csv(
        METRICS_DIR / "s2_random_stratified.csv", index=False
    )
    print(f"Wrote {METRICS_DIR / 'extended_stats.json'}")
    return report


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="fast")
    p.add_argument("--feature-set", default="A")
    args = p.parse_args()
    run_extended_evaluation(mode=args.mode, feature_set=args.feature_set)

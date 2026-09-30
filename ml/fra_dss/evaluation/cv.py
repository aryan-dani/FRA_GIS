"""Cross-validation runner and master benchmark."""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from fra_dss.config import CACHE_DIR, METRICS_DIR, SEED, TABLES_DIR, ensure_dirs, mode_settings
from fra_dss.data.load import load_claims, provenance, write_json
from fra_dss.data.splits import iter_s1, lock_splits, temporal_mask, leave_one_state_out, iter_s2
from fra_dss.evaluation.metrics import evaluate_classifier, timed_predict_proba
from fra_dss.models.ensembles import soft_voting, stacking_logistic, stacking_lgbm
from fra_dss.models.zoo import P0_MODELS, P1_MODELS, SLOW_MODELS, build_estimator
from fra_dss.preprocessing.pipelines import build_preprocessor, select_frame


def _get_model(name: str, mode: str):
    if name == "soft_voting":
        return soft_voting(mode)
    if name == "stacking_logistic":
        return stacking_logistic(mode)
    if name == "stacking_lgbm":
        return stacking_lgbm(mode)
    if name == "weighted_voting":
        return soft_voting(mode)
    if name == "blending":
        return soft_voting(mode)
    return build_estimator(name, mode)


def _fit_eval_fold(
    name: str,
    mode: str,
    feature_set: str,
    X_tr: pd.DataFrame,
    y_tr: np.ndarray,
    X_te: pd.DataFrame,
    y_te: np.ndarray,
    labels: list[str],
) -> dict[str, Any]:
    pipe = Pipeline(
        [
            ("pre", build_preprocessor(feature_set, for_trees=name not in {"logistic_l2", "logistic_elasticnet", "knn", "sgd_svm", "mlp", "naive_bayes"})),
            ("model", _get_model(name, mode)),
        ]
    )
    # Slow models: subsample train
    if name in SLOW_MODELS and len(X_tr) > 8000:
        rng = np.random.default_rng(SEED)
        idx = rng.choice(len(X_tr), size=8000, replace=False)
        X_fit, y_fit = X_tr.iloc[idx], y_tr[idx]
    else:
        X_fit, y_fit = X_tr, y_tr

    t0 = time.perf_counter()
    pipe.fit(X_fit, y_fit)
    train_s = time.perf_counter() - t0
    proba, lat = timed_predict_proba(pipe, X_te)
    pred = np.argmax(proba, axis=1)
    metrics = evaluate_classifier(
        y_te, pred, proba, labels, train_seconds=train_s, infer_ms_per_1k=lat
    )
    return metrics


def run_benchmark(
    mode: str = "fast",
    include_p1: bool = True,
    feature_sets: list[str] | None = None,
) -> pd.DataFrame:
    ensure_dirs()
    df = load_claims(mode=mode)
    labels = ["Approved", "Pending", "Rejected"]
    le = LabelEncoder()
    le.fit(labels)
    y = le.transform(df["status"].astype(str))
    groups = df["district"].fillna("Unknown").astype(str).to_numpy()

    splits = lock_splits(df)
    train_idx, test_idx = splits["train"], splits["test"]
    df_train = df.iloc[train_idx].reset_index(drop=True)
    y_train = y[train_idx]
    groups_train = groups[train_idx]
    df_test = df.iloc[test_idx].reset_index(drop=True)
    y_test = y[test_idx]

    models = list(P0_MODELS) + ["soft_voting", "stacking_logistic"]
    if include_p1:
        models = models + list(P1_MODELS) + ["stacking_lgbm"]

    feature_sets = feature_sets or ["A", "B"]
    rows = []
    registry: dict[str, Any] = {"provenance": provenance(mode, len(df)), "models": {}}

    for fs in feature_sets:
        X_all_train = select_frame(df_train, fs)
        X_all_test = select_frame(df_test, fs)

        for name in models:
            cache_key = f"{mode}_{fs}_{name}"
            cache_file = CACHE_DIR / f"{cache_key}.json"
            try:
                # S1 CV
                fold_scores = []
                fold_logloss = []
                for fold_i, (tr, va) in enumerate(iter_s1(df_train, y_train, groups_train)):
                    m = _fit_eval_fold(
                        name,
                        mode,
                        fs,
                        X_all_train.iloc[tr],
                        y_train[tr],
                        X_all_train.iloc[va],
                        y_train[va],
                        labels,
                    )
                    fold_scores.append(m["macro_f1"])
                    if m.get("log_loss") is not None:
                        fold_logloss.append(m["log_loss"])

                # S3 temporal on full loaded df
                tr_t, te_t = temporal_mask(df)
                # Restrict to indices present; temporal on full df then intersect train? Use full df.
                X_full = select_frame(df, fs)
                m_s3 = _fit_eval_fold(
                    name, mode, fs, X_full.iloc[tr_t], y[tr_t], X_full.iloc[te_t], y[te_t], labels
                )

                # Locked final test (once)
                m_final = _fit_eval_fold(
                    name, mode, fs, X_all_train, y_train, X_all_test, y_test, labels
                )

                row = {
                    "model": name,
                    "feature_set": fs,
                    "s1_macro_f1_mean": float(np.mean(fold_scores)),
                    "s1_macro_f1_std": float(np.std(fold_scores)),
                    "s1_log_loss_mean": float(np.mean(fold_logloss)) if fold_logloss else None,
                    "s3_macro_f1": m_s3["macro_f1"],
                    "s3_accuracy": m_s3["accuracy"],
                    "final_macro_f1": m_final["macro_f1"],
                    "final_accuracy": m_final["accuracy"],
                    "final_log_loss": m_final.get("log_loss"),
                    "latency_ms_per_1k": m_final.get("latency_ms_per_1k"),
                    "train_seconds": m_final.get("train_seconds"),
                }
                rows.append(row)
                registry["models"][cache_key] = {
                    "fold_macro_f1": fold_scores,
                    "final": m_final,
                    "s3": m_s3,
                }
                write_json(cache_file, row)
                print(f"[ok] {cache_key} S1={row['s1_macro_f1_mean']:.4f} final={row['final_macro_f1']:.4f}")
            except Exception as exc:
                err = {"model": name, "feature_set": fs, "error": str(exc), "trace": traceback.format_exc()[-500:]}
                rows.append({"model": name, "feature_set": fs, "s1_macro_f1_mean": None, "error": str(exc)})
                write_json(CACHE_DIR / f"{cache_key}_error.json", err)
                print(f"[fail] {cache_key}: {exc}")

    bench = pd.DataFrame(rows)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = METRICS_DIR / "benchmark_master.csv"
    bench.to_csv(out_csv, index=False)
    write_json(METRICS_DIR / "benchmark_registry.json", registry)

    # Champion by pre-declared rule on Set A
    a = bench[(bench["feature_set"] == "A") & bench["s1_macro_f1_mean"].notna()].copy()
    if len(a):
        a = a.sort_values(
            ["s1_macro_f1_mean", "s1_log_loss_mean", "latency_ms_per_1k"],
            ascending=[False, True, True],
        )
        champion = a.iloc[0].to_dict()
        write_json(METRICS_DIR / "champion.json", {"rule": "S1 macro_f1 on Set A", **champion})
    return bench

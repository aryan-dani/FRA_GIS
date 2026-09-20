"""
Train a compact LightGBM claim-outcome classifier on fra_synthetic_claims.csv.

Usage (from repo root):
  pip install lightgbm scikit-learn pandas joblib shap
  python ml/train_claim_outcome.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml.features import (  # noqa: E402
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    STATUS_LABELS,
    prepare_features,
)

CSV_PATH = ROOT / "data" / "fra_synthetic_claims.csv"
MODEL_DIR = ROOT / "backend" / "models"
MODEL_PATH = MODEL_DIR / "claim_outcome.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
PRIORITY_PATH = MODEL_DIR / "priority_by_district.json"


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_COLUMNS,
            ),
            ("num", "passthrough", NUMERIC_COLUMNS),
        ]
    )


def compute_district_freq(series: pd.Series) -> dict[str, float]:
    counts = series.fillna("Unknown").astype(str).value_counts()
    return {str(k): float(v) for k, v in counts.items()}


def aggregate_priority(df: pd.DataFrame) -> list[dict]:
    """District-level priority scores for the DSS map/table."""
    rows = []
    grouped = df.groupby(["state", "district"], dropna=False)
    for (state, district), g in grouped:
        pending = int((g["status"] == "Pending").sum())
        rejected = int((g["status"] == "Rejected").sum())
        approved = int((g["status"] == "Approved").sum())
        total = int(len(g))
        mean_days = float(pd.to_numeric(g["processing_days"], errors="coerce").mean())
        reject_rate = rejected / total if total else 0.0
        pending_rate = pending / total if total else 0.0
        # Higher = more urgent for officers
        score = (
            0.45 * pending_rate * 100
            + 0.35 * reject_rate * 100
            + 0.20 * min(mean_days / 365.0, 1.0) * 100
        )
        lat = pd.to_numeric(g["latitude"], errors="coerce").mean()
        lon = pd.to_numeric(g["longitude"], errors="coerce").mean()
        rows.append(
            {
                "state": state,
                "district": district if pd.notna(district) and district != "" else "Unknown",
                "total_claims": total,
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "mean_processing_days": round(mean_days, 1) if not np.isnan(mean_days) else None,
                "reject_rate": round(reject_rate, 4),
                "priority_score": round(float(score), 2),
                "latitude": None if pd.isna(lat) else round(float(lat), 5),
                "longitude": None if pd.isna(lon) else round(float(lon), 5),
            }
        )
    rows.sort(key=lambda r: r["priority_score"], reverse=True)
    return rows


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing dataset: {CSV_PATH}")

    print(f"Loading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH)
    df = df[df["status"].isin(STATUS_LABELS)].copy()
    print(f"Rows: {len(df):,}")

    district_freq = compute_district_freq(df["district"])
    X = prepare_features(df, district_freq=district_freq)
    y_raw = df["status"].astype(str)
    groups = df["district"].fillna("Unknown").astype(str)

    label_encoder = LabelEncoder()
    label_encoder.fit(STATUS_LABELS)
    y = label_encoder.transform(y_raw)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    model = LGBMClassifier(
        n_estimators=120,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )
    print("Training LightGBM ...")
    model.fit(X_train_t, y_train)

    y_pred = model.predict(X_test_t)
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    per_class_recall = recall_score(y_test, y_pred, average=None, labels=range(len(STATUS_LABELS)))
    report = classification_report(
        y_test,
        y_pred,
        target_names=list(label_encoder.classes_),
        output_dict=True,
    )

    metrics = {
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class_recall": {
            label_encoder.classes_[i]: round(float(per_class_recall[i]), 4)
            for i in range(len(label_encoder.classes_))
        },
        "classification_report": report,
        "holdout": "GroupShuffleSplit by district (20% test)",
        "model": "LGBMClassifier",
    }
    print(json.dumps({k: metrics[k] for k in ("accuracy", "macro_f1", "per_class_recall")}, indent=2))

    feature_names = list(preprocessor.get_feature_names_out())
    artifact = {
        "preprocessor": preprocessor,
        "model": model,
        "label_encoder": label_encoder,
        "district_freq": district_freq,
        "feature_names": feature_names,
        "classes": list(label_encoder.classes_),
        "status_labels": STATUS_LABELS,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, MODEL_PATH, compress=3)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    priority = aggregate_priority(df)
    PRIORITY_PATH.write_text(json.dumps(priority, indent=2), encoding="utf-8")

    print(f"Wrote {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1024:.1f} KB)")
    print(f"Wrote {METRICS_PATH}")
    print(f"Wrote {PRIORITY_PATH} ({len(priority)} districts)")


if __name__ == "__main__":
    main()

"""Core pytest suite for FRA DSS."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ML_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ML_ROOT.parent
sys.path.insert(0, str(ML_ROOT))
sys.path.insert(0, str(REPO_ROOT))

from fra_dss.config import METRICS_DIR, experiment_config
from fra_dss.data import audit_leakage, load_claims, lock_splits, validate_claims
from fra_dss.data.load import load_raw_claims
from fra_dss.preprocessing.pipelines import build_preprocessor, feature_columns, select_frame


def test_schema_validation():
    df = load_raw_claims()
    profile = validate_claims(df)
    assert profile["valid"] is True
    assert profile["n_rows"] == 125000


def test_locked_split_no_district_overlap():
    df = load_claims(mode="fast")
    splits = lock_splits(df)
    train_d = set(df.iloc[splits["train"]]["district"].astype(str))
    test_d = set(df.iloc[splits["test"]]["district"].astype(str))
    assert train_d.isdisjoint(test_d)


def test_set_a_forbids_leakage_columns():
    cols = set(feature_columns("A"))
    forbidden = set(experiment_config()["forbidden_for_status"])
    assert cols.isdisjoint(forbidden)
    assert "rejection_reason" not in cols
    assert "processing_days" not in cols
    assert "committee_level_reached" not in cols


def test_preprocessor_fit_transform_shapes():
    df = load_claims(mode="fast").head(500)
    y = (df["status"] == "Approved").astype(int).to_numpy()
    X = select_frame(df, "A")
    pre = build_preprocessor("A")
    Xt = pre.fit_transform(X, y)
    assert Xt.shape[0] == len(X)
    assert Xt.shape[1] > 5


def test_leakage_audit_flags_rejection_reason():
    df = load_claims(mode="fast")
    report = audit_leakage(df)
    assert report["rejection_reason_probe"]["allowed_in_set_A"] is False
    assert report["feature_set_checks"]["A"]["pass"] is True


def test_artifact_contract_if_present():
    path = REPO_ROOT / "backend" / "models" / "claim_outcome.joblib"
    if not path.exists():
        pytest.skip("artifact not trained yet")
    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from dss.model_service import predict_outcome

    out = predict_outcome(
        {
            "state": "Madhya Pradesh",
            "district": "Test",
            "claim_type": "IFR",
            "applicant_type": "ST",
            "land_area_ha": 1.2,
            "forest_density_class": "Open",
            "year_filed": 2018,
            "documentation_completeness": "Complete",
            "gram_sabha_resolution": "Passed",
            "processing_days": 100,
            "committee_level_reached": "FRC",
        }
    )
    assert "predicted_status" in out
    assert "probabilities" in out
    assert set(out["probabilities"]) >= {"Approved", "Pending", "Rejected"}


def test_dss_recommend_schema_if_artifact():
    path = REPO_ROOT / "backend" / "models" / "claim_outcome.joblib"
    if not path.exists():
        pytest.skip("artifact not trained yet")
    from fra_dss.dss import recommend

    rec = recommend(
        {
            "state": "Odisha",
            "district": "Demo",
            "claim_type": "IFR",
            "applicant_type": "ST",
            "land_area_ha": 2.0,
            "forest_density_class": "Open",
            "year_filed": 2016,
            "documentation_completeness": "Incomplete",
            "gram_sabha_resolution": "Disputed",
            "processing_days": 200,
            "committee_level_reached": "SDLC",
        }
    )
    assert rec.predicted_status in {"Approved", "Pending", "Rejected"}
    assert "Synthetic" in rec.synthetic_disclosure or "synthetic" in rec.synthetic_disclosure.lower()

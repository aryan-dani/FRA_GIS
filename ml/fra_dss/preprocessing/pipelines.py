"""Sklearn pipelines per feature set."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, RobustScaler

from fra_dss.config import experiment_config
from fra_dss.preprocessing.cleaners import ColumnCleaner, RareLevelGrouper, Winsorizer
from fra_dss.preprocessing.transformers import FeatureEngineer

# Ordered categories
FOREST_ORDER = ["Scrub", "Open", "Moderately Dense", "Very Dense"]
COMMITTEE_ORDER = ["Gram Sabha", "FRC", "SDLC", "DLC", "SLMC"]
DOC_ORDER = ["Incomplete", "Partial", "Complete"]
GS_ORDER = ["Rejected", "Disputed", "Pending", "Passed"]


def feature_columns(feature_set: str = "A") -> list[str]:
    cfg = experiment_config()
    return list(cfg["feature_sets"][feature_set]["columns"])


def select_frame(df: pd.DataFrame, feature_set: str = "A") -> pd.DataFrame:
    cols = feature_columns(feature_set)
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = pd.NA
    return out[cols]


def build_preprocessor(
    feature_set: str = "A",
    for_trees: bool = False,
    group_rare: bool = True,
) -> Pipeline:
    """
    Build a Pipeline: clean -> engineer -> (optional rare group) -> ColumnTransformer.

    Tree models still use one-hot for the shipped artifact so SHAP feature names stay stable.
    """
    base_cols = feature_columns(feature_set)
    eng = FeatureEngineer(include_district_stats=True)

    cat_onehot = [
        c
        for c in (
            "state",
            "district",
            "claim_type",
            "applicant_type",
            "land_bin",
        )
        if c in base_cols or c == "land_bin"
    ]
    # ordinals
    ordinal_specs = []
    if "forest_density_class" in base_cols:
        ordinal_specs.append(("forest_density_class", FOREST_ORDER))
    if "documentation_completeness" in base_cols:
        ordinal_specs.append(("documentation_completeness", DOC_ORDER))
    if "gram_sabha_resolution" in base_cols:
        ordinal_specs.append(("gram_sabha_resolution", GS_ORDER))
    if "committee_level_reached" in base_cols:
        ordinal_specs.append(("committee_level_reached", COMMITTEE_ORDER))

    numeric = [
        c
        for c in (
            "land_area_ha",
            "year_filed",
            "processing_days",
            "latitude",
            "longitude",
            "claim_age",
            "log_land_area",
            "pre_2019_flag",
            "is_rare_claim_type",
            "docs_x_gramsabha",
            "district_oof_approval",
            "district_mean_land",
            "state_year_backlog",
        )
        if c in base_cols
        or c
        in {
            "claim_age",
            "log_land_area",
            "pre_2019_flag",
            "is_rare_claim_type",
            "docs_x_gramsabha",
            "district_oof_approval",
            "district_mean_land",
            "state_year_backlog",
        }
    ]
    # drop process numerics for set A
    if feature_set == "A":
        numeric = [c for c in numeric if c not in {"processing_days"}]
        cat_onehot = [c for c in cat_onehot if c != "committee_level_reached"]

    transformers: list[tuple[str, Any, list[str]]] = [
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            cat_onehot,
        ),
        (
            "num",
            Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("scale", RobustScaler() if not for_trees else "passthrough"),
                ]
            ),
            numeric,
        ),
    ]
    for col, order in ordinal_specs:
        transformers.append(
            (
                f"ord_{col}",
                OrdinalEncoder(
                    categories=[order],
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
                [col],
            )
        )

    steps: list[tuple[str, Any]] = [
        ("clean", ColumnCleaner(feature_set=feature_set)),
        ("engineer", eng),
    ]
    if group_rare:
        steps.append(("rare", RareLevelGrouper(column="claim_type", min_count=300)))
    steps.append(("winsor", Winsorizer(columns=["land_area_ha"])))
    steps.append(("encode", ColumnTransformer(transformers=transformers, remainder="drop")))

    return Pipeline(steps)


def pipeline_diagram_steps(feature_set: str = "A") -> list[str]:
    return [
        "Raw CSV row",
        "ColumnCleaner",
        "FeatureEngineer",
        "RareLevelGrouper (claim_type)",
        "Winsorizer (land_area_ha)",
        f"ColumnTransformer (Set {feature_set})",
        "Estimator",
    ]

"""Model zoo constructors for status classification."""

from __future__ import annotations

from typing import Any, Callable

from sklearn.ensemble import (
    AdaBoostClassifier,
    BaggingClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier
from sklearn.calibration import CalibratedClassifierCV

from fra_dss.config import SEED, n_jobs, mode_settings


def _cap(mode: str) -> int:
    return int(mode_settings(mode).get("n_estimators_cap", 120))


def build_estimator(name: str, mode: str = "fast") -> Any:
    cap = _cap(mode)
    nj = n_jobs()
    rs = SEED

    if name == "dummy_prior":
        return DummyClassifier(strategy="prior", random_state=rs)
    if name == "dummy_stratified":
        return DummyClassifier(strategy="stratified", random_state=rs)
    if name == "logistic_l2":
        return LogisticRegression(
            max_iter=800, class_weight="balanced", random_state=rs
        )
    if name == "logistic_elasticnet":
        return LogisticRegression(
            solver="saga",
            l1_ratio=0.5,
            C=1.0,
            max_iter=800,
            class_weight="balanced",
            random_state=rs,
        )
    if name == "naive_bayes":
        return GaussianNB()
    if name == "knn":
        return KNeighborsClassifier(n_neighbors=15, n_jobs=nj)
    if name == "sgd_svm":
        base = SGDClassifier(
            loss="hinge",
            class_weight="balanced",
            random_state=rs,
            max_iter=500,
        )
        return CalibratedClassifierCV(base, cv=3)
    if name == "decision_tree":
        return DecisionTreeClassifier(
            max_depth=8, class_weight="balanced", random_state=rs
        )
    if name == "mlp":
        return MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=80 if mode == "fast" else 150,
            random_state=rs,
        )
    if name == "bagging":
        return BaggingClassifier(
            estimator=DecisionTreeClassifier(max_depth=8, random_state=rs),
            n_estimators=min(50, cap),
            random_state=rs,
            n_jobs=nj,
        )
    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=min(150, cap),
            max_depth=12,
            class_weight="balanced_subsample",
            random_state=rs,
            n_jobs=nj,
        )
    if name == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=min(150, cap),
            max_depth=12,
            class_weight="balanced",
            random_state=rs,
            n_jobs=nj,
        )
    if name == "adaboost":
        return AdaBoostClassifier(
            n_estimators=min(80, cap), learning_rate=0.5, random_state=rs
        )
    if name == "gradient_boosting":
        return GradientBoostingClassifier(
            n_estimators=min(80, cap),
            max_depth=3,
            learning_rate=0.08,
            subsample=0.8,
            random_state=rs,
        )
    if name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(
            max_iter=min(120, cap),
            learning_rate=0.08,
            max_depth=6,
            random_state=rs,
        )
    if name == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=min(120, cap),
            max_depth=6,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            eval_metric="mlogloss",
            tree_method="hist",
            random_state=rs,
            n_jobs=nj,
        )
    if name == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(
            n_estimators=min(120, cap),
            max_depth=6,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            class_weight="balanced",
            random_state=rs,
            n_jobs=nj,
            verbose=-1,
        )
    if name == "catboost":
        from catboost import CatBoostClassifier

        return CatBoostClassifier(
            iterations=min(120, cap),
            depth=6,
            learning_rate=0.08,
            loss_function="MultiClass",
            random_seed=rs,
            verbose=False,
            thread_count=nj,
        )
    raise KeyError(f"Unknown model: {name}")


P0_MODELS = [
    "dummy_prior",
    "dummy_stratified",
    "logistic_l2",
    "logistic_elasticnet",
    "decision_tree",
    "random_forest",
    "bagging",
    "gradient_boosting",
    "hist_gradient_boosting",
    "xgboost",
    "lightgbm",
]

P1_MODELS = [
    "naive_bayes",
    "knn",
    "sgd_svm",
    "mlp",
    "extra_trees",
    "adaboost",
    "catboost",
]

SLOW_MODELS = {"knn", "mlp", "sgd_svm", "gradient_boosting"}

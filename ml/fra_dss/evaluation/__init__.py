"""Evaluation package."""

from fra_dss.evaluation.cv import run_benchmark
from fra_dss.evaluation.metrics import evaluate_classifier
from fra_dss.evaluation.ablation import feature_set_ablation

__all__ = ["run_benchmark", "evaluate_classifier", "feature_set_ablation"]

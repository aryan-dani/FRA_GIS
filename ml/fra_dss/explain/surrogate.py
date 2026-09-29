"""Shallow surrogate decision tree for human-readable rules."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier, export_text


def fit_surrogate(
    X: np.ndarray, soft_labels: np.ndarray, feature_names: list[str], max_depth: int = 3
) -> dict[str, Any]:
    y = soft_labels if soft_labels.ndim == 1 else soft_labels.argmax(axis=1)
    tree = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    tree.fit(X, y)
    pred = tree.predict(X)
    fidelity = float(accuracy_score(y, pred))
    text = export_text(tree, feature_names=[str(f) for f in feature_names[: X.shape[1]]])
    return {"fidelity": fidelity, "rules": text, "model": tree}

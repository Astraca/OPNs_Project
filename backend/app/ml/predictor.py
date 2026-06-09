"""Prediction helpers for loading models and running inference."""

import joblib
import pandas as pd
from pathlib import Path

from app.ml.opns_transformer import OPNsTransformer


def load_transformer(model_dir: str) -> OPNsTransformer | None:
    """Load OPNsTransformer from model directory if it exists."""
    transformer_path = Path(model_dir) / "opns_transformer.pkl"
    if transformer_path.exists():
        return joblib.load(transformer_path)
    return None


def load_pipeline(model_dir: str, filename: str = "regressor.pkl"):
    """Load a sklearn Pipeline from model directory."""
    pipeline_path = Path(model_dir) / filename
    if not pipeline_path.exists():
        raise FileNotFoundError(f"Model file not found: {pipeline_path}")
    return joblib.load(pipeline_path)


def load_classifiers(model_dir: str, target_columns: list[str]) -> dict[str, object]:
    """Load per-target classifiers from model directory."""
    classifiers: dict[str, object] = {}
    for target in target_columns:
        classifier_path = Path(model_dir) / f"{target}_classifier.pkl"
        if classifier_path.exists():
            classifiers[target] = joblib.load(classifier_path)
    return classifiers


def apply_transformer(
    transformer: OPNsTransformer | None,
    feature_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Apply OPNsTransformer if provided, otherwise return input as-is."""
    if transformer is not None:
        return transformer.transform(feature_frame)
    return feature_frame


def predict_classification(
    classifiers: dict[str, object],
    feature_frame: pd.DataFrame,
    target_columns: list[str],
    as_list: bool = False,
) -> dict | list[dict]:
    """Run classification prediction using per-target classifiers.

    Returns:
        Single prediction dict or list of dicts keyed by target name.
    """
    per_target: dict[str, list[dict]] = {}
    for target in target_columns:
        if target not in classifiers:
            continue
        clf = classifiers[target]
        labels = clf.predict(feature_frame)
        probs = _get_probabilities(clf, feature_frame, labels)
        per_target[target] = [
            {"label": str(label), "probability": prob}
            for label, prob in zip(labels, probs)
        ]

    rows: list[dict] = []
    for row_idx in range(len(feature_frame)):
        rows.append({
            target: per_target[target][row_idx]
            for target in target_columns if target in per_target
        })
    return rows if as_list else rows[0]


def predict_regression(
    regressor: object,
    feature_frame: pd.DataFrame,
    as_list: bool = False,
) -> float | list[float]:
    """Run regression prediction.

    Returns:
        Single float or list of floats.
    """
    predictions = regressor.predict(feature_frame)
    values = [round(float(v), 4) for v in predictions]
    return values if as_list else values[0]


def _get_probabilities(classifier, feature_frame, labels) -> list[float | None]:
    """Extract prediction probabilities from a classifier."""
    if not hasattr(classifier, "predict_proba"):
        return [None for _ in labels]
    proba_matrix = classifier.predict_proba(feature_frame)
    classes = list(classifier.classes_)
    result: list[float | None] = []
    for label, row in zip(labels, proba_matrix):
        try:
            result.append(round(float(row[classes.index(label)]), 4))
        except (ValueError, IndexError):
            result.append(None)
    return result

"""Evaluation helpers for classification and regression models."""

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline


def compute_confusion_matrix(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> tuple[list[str], list[list[int]]]:
    """Return (labels, matrix) for a confusion matrix."""
    labels = sorted(set(str(v) for v in pd.concat([y_true, pd.Series(y_pred)])))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return labels, cm.tolist()


def compute_roc_data(
    y_true: pd.Series,
    proba: np.ndarray,
    classes: list[str],
) -> list[dict]:
    """Compute ROC curve data for all classes.

    For binary classification (2 classes), returns a single curve.
    For multi-class, returns one-vs-rest curves for each class.

    Returns list of dicts with fpr, tpr, auc keys.
    """
    curves: list[dict] = []

    if len(classes) == 2:
        fpr, tpr, _ = roc_curve(
            y_true.map({classes[0]: 0, classes[1]: 1}),
            proba[:, 1],
        )
        auc_val = float(roc_auc_score(
            y_true.map({classes[0]: 0, classes[1]: 1}),
            proba[:, 1],
        ))
        curves.append({"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": auc_val})
    elif len(classes) > 2:
        for idx, label in enumerate(classes):
            binary_true = (y_true == label).astype(int)
            fpr, tpr, _ = roc_curve(binary_true, proba[:, idx])
            auc_val = float(roc_auc_score(binary_true, proba[:, idx]))
            curves.append({"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": auc_val})

    return curves


def compute_predicted_vs_actual(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
) -> tuple[list[float], list[float]]:
    """Return (actual_values, predicted_values) for scatter plotting."""
    return (
        [round(float(v), 4) for v in np.asarray(y_true)],
        [round(float(v), 4) for v in y_pred],
    )


def compute_residuals(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
) -> tuple[list[float], list[float]]:
    """Return (residuals, predicted_values)."""
    residuals = np.asarray(y_true) - y_pred
    return (
        [round(float(v), 4) for v in residuals],
        [round(float(v), 4) for v in y_pred],
    )


def has_predict_proba(pipeline: Pipeline) -> bool:
    return hasattr(pipeline, "predict_proba")

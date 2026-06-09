"""ML training helpers for classification and regression."""

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR

from app.ml.opns_transformer import OPNsTransformer


def split_data(
    X: pd.DataFrame,
    y: pd.DataFrame | pd.Series,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split data into train/test sets with optional stratification."""
    try:
        return train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=stratify,
        )
    except ValueError:
        return train_test_split(
            X, y, test_size=test_size, random_state=random_state,
        )


def build_opns_transformer(
    pairing_method: str,
    random_state: int,
) -> OPNsTransformer:
    return OPNsTransformer(pairing_method=pairing_method, random_state=random_state)


def build_svc_pipeline(random_state: int = 42) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("svc", SVC(kernel="rbf", probability=True, random_state=random_state)),
    ])


def build_svr_pipeline() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("svr", SVR(kernel="rbf")),
    ])


def compute_classification_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def compute_regression_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float | None]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    mape: float | None = None
    yt = np.asarray(y_true)
    if (yt != 0).any():
        mape = float(np.mean(np.abs((yt - y_pred) / np.where(yt != 0, yt, np.nan))) * 100)
    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}

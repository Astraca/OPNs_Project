from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, status
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models.dataset import Dataset
from app.db_models.ml_model import MLModel, ModelMetric
from app.db_models.user import User
from app.ml.evaluator import (
    compute_confusion_matrix,
    compute_predicted_vs_actual,
    compute_residuals,
    compute_roc_data,
    has_predict_proba,
)
from app.ml.predictor import apply_transformer, load_classifiers, load_pipeline, load_transformer
from app.schemas.evaluation_schema import (
    ClassificationMetricItem,
    ConfusionMatrixResponse,
    PredictedVsActualResponse,
    RegressionMetricItem,
    ResidualsResponse,
    RocCurveResponse,
    RocCurveItem,
)
from app.services.dataset_service import read_dataset_file
from app.services.training_service import get_model
from app.utils.igan_fields import display_target_name


def _get_test_data(
    db: Session,
    model: MLModel,
) -> tuple[pd.DataFrame, pd.DataFrame | pd.Series, pd.DataFrame | pd.Series, pd.DataFrame]:
    """Load dataset and re-split to retrieve the same test fold."""
    dataset = db.get(Dataset, model.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    dataframe = read_dataset_file(dataset)
    numeric_features = dataframe[model.feature_columns].apply(pd.to_numeric, errors="coerce")
    y = dataframe[model.target_columns]
    if model.task_type == "regression":
        y = pd.to_numeric(y.iloc[:, 0], errors="coerce")
        valid_mask = y.notna()
        numeric_features = numeric_features.loc[valid_mask]
        y = y.loc[valid_mask]
    else:
        y = y.astype(str)

    test_size = model.hyperparameters.get("test_size", 0.2)
    random_state = model.hyperparameters.get("random_state", 42)

    stratify_target = None
    if model.task_type != "regression" and y.iloc[:, 0].nunique() > 1:
        stratify_target = y.iloc[:, 0]

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            numeric_features, y, test_size=test_size, random_state=random_state,
            stratify=stratify_target,
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            numeric_features, y, test_size=test_size, random_state=random_state,
        )

    return X_train, X_test, y_train, y_test


def _load_model_pipeline(model: MLModel) -> tuple[object | None, dict[str, Pipeline] | Pipeline]:
    """Return (transformer, classifiers|regressor) from disk."""
    if model.model_file_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model files are missing")

    transformer = load_transformer(model.model_file_path) if model.opns_enabled else None

    if model.task_type == "regression":
        return transformer, load_pipeline(model.model_file_path, "regressor.pkl")

    classifiers = load_classifiers(model.model_file_path, model.target_columns)
    return transformer, classifiers


# ── Classification evaluation ──────────────────────────────────────────────────

def build_classification_metrics(
    db: Session,
    current_user: User,
    model_id: int,
) -> dict[str, Any]:
    model = get_model(db, current_user, model_id)
    if model.task_type not in {"classification", "multi_output_classification"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not a classification model",
        )

    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    rows = list(db.scalars(statement).all())

    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        target = display_target_name(row.target_name or "overall")
        grouped.setdefault(target, {})[row.metric_name] = round(row.metric_value, 4)

    metrics = [
        ClassificationMetricItem(
            target_name=target,
            accuracy=values.get("accuracy", 0),
            precision=values.get("precision", 0),
            recall=values.get("recall", 0),
            f1=values.get("f1", 0),
        )
        for target, values in grouped.items()
    ]

    return {
        "model_id": model.id,
        "algorithm": model.algorithm,
        "metrics": metrics,
    }


def build_confusion_matrices(
    db: Session,
    current_user: User,
    model_id: int,
) -> list[ConfusionMatrixResponse]:
    model = get_model(db, current_user, model_id)
    if model.task_type not in {"classification", "multi_output_classification"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a classification model")

    _, X_test, _, y_test = _get_test_data(db, model)
    transformer, classifiers = _load_model_pipeline(model)
    if not isinstance(classifiers, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unexpected model format")

    X_transformed = apply_transformer(transformer, X_test)

    result: list[ConfusionMatrixResponse] = []
    for target in model.target_columns:
        if target not in classifiers:
            continue
        clf = classifiers[target]
        y_pred = clf.predict(X_transformed)
        y_true = y_test[target]
        labels, matrix = compute_confusion_matrix(y_true, y_pred)
        result.append(
            ConfusionMatrixResponse(
                target_name=display_target_name(target),
                labels=labels,
                matrix=matrix,
            ),
        )
    return result


def build_roc_curves(
    db: Session,
    current_user: User,
    model_id: int,
) -> list[RocCurveResponse]:
    model = get_model(db, current_user, model_id)
    if model.task_type not in {"classification", "multi_output_classification"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a classification model")

    _, X_test, _, y_test = _get_test_data(db, model)
    transformer, classifiers = _load_model_pipeline(model)
    if not isinstance(classifiers, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unexpected model format")

    X_transformed = apply_transformer(transformer, X_test)

    result: list[RocCurveResponse] = []
    for target in model.target_columns:
        if target not in classifiers:
            continue
        clf = classifiers[target]
        y_true = y_test[target]
        unique_classes = sorted(y_true.unique())

        curves: list[RocCurveItem] = []
        if has_predict_proba(clf):
            proba = clf.predict_proba(X_transformed)
            curve_data = compute_roc_data(y_true, proba, unique_classes)
            curves = [
                RocCurveItem(fpr=c["fpr"], tpr=c["tpr"], auc=c["auc"])
                for c in curve_data
            ]

        result.append(RocCurveResponse(target_name=display_target_name(target), curves=curves))
    return result


# ── Regression evaluation ──────────────────────────────────────────────────────

def build_regression_metrics(
    db: Session,
    current_user: User,
    model_id: int,
) -> dict[str, Any]:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not a regression model",
        )

    target_name = display_target_name(model.target_columns[0]) if model.target_columns else "target"

    _, X_test, _, y_test = _get_test_data(db, model)
    transformer, regressor = _load_model_pipeline(model)
    X_transformed = apply_transformer(transformer, X_test)
    predictions = regressor.predict(X_transformed)

    from app.ml.trainer import compute_regression_metrics
    metrics_dict = compute_regression_metrics(y_test, predictions)
    metric = RegressionMetricItem(
        target_name=target_name,
        mae=round(metrics_dict["mae"], 4),
        rmse=round(metrics_dict["rmse"], 4),
        r2=round(metrics_dict["r2"], 4),
        mape=round(metrics_dict["mape"], 4) if metrics_dict["mape"] is not None else None,
    )
    return {"model_id": model.id, "algorithm": model.algorithm, "metrics": metric}


def build_predicted_vs_actual(
    db: Session,
    current_user: User,
    model_id: int,
) -> PredictedVsActualResponse:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a regression model")

    target_name = display_target_name(model.target_columns[0]) if model.target_columns else "target"
    _, X_test, _, y_test = _get_test_data(db, model)
    transformer, regressor = _load_model_pipeline(model)
    X_transformed = apply_transformer(transformer, X_test)
    predictions = regressor.predict(X_transformed)

    actual, predicted = compute_predicted_vs_actual(y_test, predictions)
    return PredictedVsActualResponse(target_name=target_name, actual=actual, predicted=predicted)


def build_residuals(
    db: Session,
    current_user: User,
    model_id: int,
) -> ResidualsResponse:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a regression model")

    target_name = display_target_name(model.target_columns[0]) if model.target_columns else "target"
    _, X_test, _, y_test = _get_test_data(db, model)
    transformer, regressor = _load_model_pipeline(model)
    X_transformed = apply_transformer(transformer, X_test)
    predictions = regressor.predict(X_transformed)

    res, pred = compute_residuals(y_test, predictions)
    return ResidualsResponse(target_name=target_name, residuals=res, predicted=pred)

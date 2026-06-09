from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException, status
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models.ml_model import MLModel, ModelMetric
from app.db_models.user import User
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
    model: MLModel,
) -> tuple[pd.DataFrame, pd.DataFrame | pd.Series, pd.DataFrame | pd.Series, pd.DataFrame]:
    """Load dataset and re-split to retrieve the same test fold."""
    dataframe = read_dataset_file(model)
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


def _load_model_pipeline(model: MLModel) -> tuple[Any | None, dict[str, Pipeline] | Pipeline]:
    """Return (transformer, classifiers|regressor) from disk."""
    if model.model_file_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model files are missing")

    model_path = Path(model.model_file_path)
    transformer_path = model_path / "opns_transformer.pkl"
    transformer = joblib.load(transformer_path) if transformer_path.exists() else None

    if model.task_type == "regression":
        regressor_path = model_path / "regressor.pkl"
        if not regressor_path.exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Regressor file is missing")
        return transformer, joblib.load(regressor_path)

    classifiers: dict[str, Pipeline] = {}
    for target in model.target_columns:
        classifier_path = model_path / f"{target}_classifier.pkl"
        if classifier_path.exists():
            classifiers[target] = joblib.load(classifier_path)
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

    _, X_test, _, y_test = _get_test_data(model)
    transformer, classifiers = _load_model_pipeline(model)
    if not isinstance(classifiers, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unexpected model format")

    X_transformed = transformer.transform(X_test) if transformer is not None else X_test

    result: list[ConfusionMatrixResponse] = []
    for target in model.target_columns:
        if target not in classifiers:
            continue
        clf = classifiers[target]
        y_pred = clf.predict(X_transformed)
        y_true = y_test[target]
        labels = sorted(set(str(v) for v in pd.concat([y_true, pd.Series(y_pred)])))
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        result.append(
            ConfusionMatrixResponse(
                target_name=display_target_name(target),
                labels=labels,
                matrix=cm.tolist(),
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

    _, X_test, _, y_test = _get_test_data(model)
    transformer, classifiers = _load_model_pipeline(model)
    if not isinstance(classifiers, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unexpected model format")

    X_transformed = transformer.transform(X_test) if transformer is not None else X_test

    result: list[RocCurveResponse] = []
    for target in model.target_columns:
        if target not in classifiers:
            continue
        clf = classifiers[target]
        y_true = y_test[target]
        unique_classes = sorted(y_true.unique())

        curves: list[RocCurveItem] = []
        if len(unique_classes) == 2 and hasattr(clf, "predict_proba"):
            proba = clf.predict_proba(X_transformed)[:, 1]
            fpr, tpr, _ = roc_curve(
                y_true.map({unique_classes[0]: 0, unique_classes[1]: 1}),
                proba,
            )
            auc = float(roc_auc_score(
                y_true.map({unique_classes[0]: 0, unique_classes[1]: 1}),
                proba,
            ))
            curves.append(RocCurveItem(fpr=fpr.tolist(), tpr=tpr.tolist(), auc=auc))
        elif len(unique_classes) > 2 and hasattr(clf, "predict_proba"):
            proba = clf.predict_proba(X_transformed)
            for idx, label in enumerate(unique_classes):
                binary_true = (y_true == label).astype(int)
                fpr, tpr, _ = roc_curve(binary_true, proba[:, idx])
                auc = float(roc_auc_score(binary_true, proba[:, idx]))
                curves.append(RocCurveItem(fpr=fpr.tolist(), tpr=tpr.tolist(), auc=auc))

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

    _, X_test, _, y_test = _get_test_data(model)
    transformer, regressor = _load_model_pipeline(model)
    X_transformed = transformer.transform(X_test) if transformer is not None else X_test
    predictions = regressor.predict(X_transformed)

    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
    r2 = float(r2_score(y_test, predictions))
    mape_val: float | None = None
    if (y_test != 0).any():
        mape_val = float(np.mean(np.abs((y_test - predictions) / np.where(y_test != 0, y_test, np.nan))) * 100)

    target_name = display_target_name(model.target_columns[0]) if model.target_columns else "target"
    metric = RegressionMetricItem(
        target_name=target_name,
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        r2=round(r2, 4),
        mape=round(mape_val, 4) if mape_val is not None else None,
    )

    return {
        "model_id": model.id,
        "algorithm": model.algorithm,
        "metrics": metric,
    }


def build_predicted_vs_actual(
    db: Session,
    current_user: User,
    model_id: int,
) -> PredictedVsActualResponse:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a regression model")

    _, X_test, _, y_test = _get_test_data(model)
    transformer, regressor = _load_model_pipeline(model)
    X_transformed = transformer.transform(X_test) if transformer is not None else X_test
    predictions = regressor.predict(X_transformed)

    target_name = display_target_name(model.target_columns[0]) if model.target_columns else "target"
    return PredictedVsActualResponse(
        target_name=target_name,
        actual=[round(float(v), 4) for v in y_test.values],  # type: ignore[arg-type]
        predicted=[round(float(v), 4) for v in predictions],
    )


def build_residuals(
    db: Session,
    current_user: User,
    model_id: int,
) -> ResidualsResponse:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a regression model")

    _, X_test, _, y_test = _get_test_data(model)
    transformer, regressor = _load_model_pipeline(model)
    X_transformed = transformer.transform(X_test) if transformer is not None else X_test
    predictions = regressor.predict(X_transformed)

    residuals = y_test.values - predictions  # type: ignore[operator]
    target_name = display_target_name(model.target_columns[0]) if model.target_columns else "target"
    return ResidualsResponse(
        target_name=target_name,
        residuals=[round(float(v), 4) for v in residuals],
        predicted=[round(float(v), 4) for v in predictions],
    )

import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from fastapi import HTTPException, status
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db_models.ml_model import MLModel, ModelMetric, TrainingRun
from app.db_models.user import User
from app.ml.opns_transformer import OPNsTransformer
from app.ml.trainer import build_pipeline, compute_classification_metrics, compute_regression_metrics
from app.schemas.model_schema import ModelTrainRequest, RegressionTrainRequest
from app.services.dataset_service import get_dataset, get_dataset_columns, read_dataset_file
from app.utils.igan_fields import get_default_feature_columns, get_mestc_target_columns


MODEL_STORAGE_DIR = Path("storage/models")


def train_classification_model(db: Session, current_user: User, payload: ModelTrainRequest) -> MLModel:
    _check_duplicate_model_name(db, current_user, payload.model_name, "classification")
    dataset = get_dataset(db, current_user, payload.dataset_id)
    dataframe = read_dataset_file(dataset)
    requested_targets = payload.target_columns or get_mestc_target_columns([str(column) for column in dataframe.columns])
    target_columns = [target for target in requested_targets if target in dataframe.columns]
    if not target_columns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No target columns found in dataset")

    dataset_columns = get_dataset_columns(db, current_user, dataset.id)
    role_feature_columns = [column.column_name for column in dataset_columns if column.role == "feature"]
    feature_columns = payload.feature_columns or role_feature_columns or get_default_feature_columns(
        [str(column) for column in dataframe.columns],
        target_columns,
    )
    numeric_features = dataframe[feature_columns].apply(pd.to_numeric, errors="coerce")
    usable_features = [column for column in numeric_features.columns if not numeric_features[column].isna().all()]
    if len(usable_features) < 2 and payload.algorithm == "OPNs-SVM":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OPNs-SVM requires at least two numeric features")
    if not usable_features:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No numeric feature columns found")

    X = numeric_features[usable_features]
    y = dataframe[target_columns].astype(str)
    stratify_target = y[target_columns[0]] if y[target_columns[0]].nunique() > 1 else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=payload.test_size,
            random_state=payload.random_state,
            stratify=stratify_target,
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=payload.test_size,
            random_state=payload.random_state,
        )

    model = MLModel(
        user_id=current_user.id,
        dataset_id=dataset.id,
        model_name=payload.model_name,
        task_type="multi_output_classification",
        algorithm=payload.algorithm,
        target_columns=target_columns,
        feature_columns=usable_features,
        opns_enabled=payload.algorithm == "OPNs-SVM",
        pairing_method=payload.pairing_method if payload.algorithm == "OPNs-SVM" else None,
        mapping_config={},
        hyperparameters={"test_size": payload.test_size, "random_state": payload.random_state, "kernel": "rbf"},
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    run = TrainingRun(
        model_id=model.id,
        train_size=len(X_train),
        test_size=len(X_test),
        random_state=payload.random_state,
        status="running",
    )
    db.add(run)
    db.commit()

    model_dir = MODEL_STORAGE_DIR / f"model_{model.id:03d}"
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        transformer = None
        if payload.algorithm == "OPNs-SVM":
            transformer = OPNsTransformer(pairing_method=payload.pairing_method, random_state=payload.random_state)
            X_train_model = transformer.fit_transform(X_train, y_train)
            X_test_model = transformer.transform(X_test)
        else:
            X_train_model = X_train
            X_test_model = X_test

        classifiers: dict[str, Pipeline] = {}
        metrics: list[ModelMetric] = []
        for target in target_columns:
            classifier = build_pipeline(payload.algorithm, payload.random_state, "classification")
            classifier.fit(X_train_model, y_train[target])
            predictions = classifier.predict(X_test_model)
            classifiers[target] = classifier
            cls_metrics = compute_classification_metrics(y_test[target], predictions)
            for metric_name, metric_value in cls_metrics.items():
                metrics.append(
                    ModelMetric(model_id=model.id, target_name=target, metric_name=metric_name, metric_value=metric_value),
                )
            joblib.dump(classifier, model_dir / f"{target}_classifier.pkl")

        if transformer is not None:
            joblib.dump(transformer, model_dir / "opns_transformer.pkl")

        metadata = {
            "model_id": model.id,
            "algorithm": model.algorithm,
            "target_columns": target_columns,
            "feature_columns": usable_features,
            "opns_enabled": model.opns_enabled,
            "pairing_method": model.pairing_method,
            "created_at": datetime.utcnow().isoformat(),
        }
        metadata_path = model_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        db.execute(delete(ModelMetric).where(ModelMetric.model_id == model.id))
        db.add_all(metrics)
        model.model_file_path = str(model_dir)
        model.metadata_file_path = str(metadata_path)
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(model)
        return model
    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.error_message = str(exc)
        db.commit()
        raise


def list_models(db: Session, current_user: User) -> list[MLModel]:
    statement = select(MLModel).where(MLModel.user_id == current_user.id).order_by(MLModel.created_at.desc())
    return list(db.scalars(statement).all())


def _check_duplicate_model_name(db: Session, current_user: User, name: str, task_type: str) -> None:
    existing = db.scalar(
        select(MLModel).where(
            MLModel.user_id == current_user.id,
            MLModel.task_type == task_type,
            MLModel.model_name == name,
        ),
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"模型名称 '{name}' 在当前任务类型下已存在，请使用其他名称",
        )


def get_model(db: Session, current_user: User, model_id: int) -> MLModel:
    model = db.get(MLModel, model_id)
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


def delete_model(db: Session, current_user: User, model_id: int) -> None:
    model = get_model(db, current_user, model_id)
    db.execute(delete(ModelMetric).where(ModelMetric.model_id == model.id))
    db.execute(delete(TrainingRun).where(TrainingRun.model_id == model.id))
    db.delete(model)
    db.commit()


def get_model_metrics(db: Session, current_user: User, model_id: int) -> list[ModelMetric]:
    model = get_model(db, current_user, model_id)
    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    return list(db.scalars(statement).all())


def get_model_metadata(db: Session, current_user: User, model_id: int) -> dict:
    model = get_model(db, current_user, model_id)
    metadata_path = model.metadata_file_path
    if metadata_path and Path(metadata_path).exists():
        return json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    return {
        "model_id": model.id,
        "algorithm": model.algorithm,
        "task_type": model.task_type,
        "target_columns": model.target_columns,
        "feature_columns": model.feature_columns,
        "opns_enabled": model.opns_enabled,
        "pairing_method": model.pairing_method,
        "hyperparameters": model.hyperparameters,
    }


def train_regression_model(db: Session, current_user: User, payload: RegressionTrainRequest) -> MLModel:
    _check_duplicate_model_name(db, current_user, payload.model_name, "regression")
    dataset = get_dataset(db, current_user, payload.dataset_id)
    dataframe = read_dataset_file(dataset)

    target_column = payload.target_column
    if target_column not in dataframe.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target column '{target_column}' not found in dataset",
        )

    dataset_columns = get_dataset_columns(db, current_user, dataset.id)
    role_feature_columns = [column.column_name for column in dataset_columns if column.role == "feature"]
    feature_columns = payload.feature_columns or role_feature_columns or get_default_feature_columns(
        [str(column) for column in dataframe.columns],
        [target_column],
    )
    numeric_features = dataframe[feature_columns].apply(pd.to_numeric, errors="coerce")
    usable_features = [column for column in numeric_features.columns if not numeric_features[column].isna().all()]
    if len(usable_features) < 2 and payload.algorithm == "OPNs-SVR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OPNs-SVR requires at least two numeric features",
        )
    if not usable_features:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No numeric feature columns found")

    X = numeric_features[usable_features]
    y = pd.to_numeric(dataframe[target_column], errors="coerce")
    valid_mask = y.notna()
    X = X.loc[valid_mask]
    y = y.loc[valid_mask]
    if len(X) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough valid samples for regression training",
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=payload.test_size, random_state=payload.random_state,
    )

    model = MLModel(
        user_id=current_user.id,
        dataset_id=dataset.id,
        model_name=payload.model_name,
        task_type="regression",
        algorithm=payload.algorithm,
        target_columns=[target_column],
        feature_columns=usable_features,
        opns_enabled=payload.algorithm == "OPNs-SVR",
        pairing_method=payload.pairing_method if payload.algorithm == "OPNs-SVR" else None,
        mapping_config={},
        hyperparameters={
            "test_size": payload.test_size,
            "random_state": payload.random_state,
            "kernel": "rbf",
        },
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    run = TrainingRun(
        model_id=model.id,
        train_size=len(X_train),
        test_size=len(X_test),
        random_state=payload.random_state,
        status="running",
    )
    db.add(run)
    db.commit()

    model_dir = MODEL_STORAGE_DIR / f"model_{model.id:03d}"
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        transformer = None
        if payload.algorithm == "OPNs-SVR":
            transformer = OPNsTransformer(
                pairing_method=payload.pairing_method,
                random_state=payload.random_state,
            )
            X_train_model = transformer.fit_transform(X_train, y_train)
            X_test_model = transformer.transform(X_test)
        else:
            X_train_model = X_train
            X_test_model = X_test

        regressor = build_pipeline(payload.algorithm, payload.random_state, "regression")
        regressor.fit(X_train_model, y_train)
        predictions = regressor.predict(X_test_model)

        reg_metrics = compute_regression_metrics(y_test, predictions)
        metrics = []
        for metric_name, metric_value in reg_metrics.items():
            if metric_value is not None:
                metrics.append(
                    ModelMetric(model_id=model.id, target_name=target_column, metric_name=metric_name, metric_value=metric_value),
                )

        joblib.dump(regressor, model_dir / "regressor.pkl")
        if transformer is not None:
            joblib.dump(transformer, model_dir / "opns_transformer.pkl")

        metadata = {
            "model_id": model.id,
            "algorithm": model.algorithm,
            "task_type": "regression",
            "target_column": target_column,
            "feature_columns": usable_features,
            "opns_enabled": model.opns_enabled,
            "pairing_method": model.pairing_method,
            "created_at": datetime.utcnow().isoformat(),
        }
        metadata_path = model_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        db.execute(delete(ModelMetric).where(ModelMetric.model_id == model.id))
        db.add_all(metrics)
        model.model_file_path = str(model_dir)
        model.metadata_file_path = str(metadata_path)
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(model)
        return model
    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.error_message = str(exc)
        db.commit()
        raise

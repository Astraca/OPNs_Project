import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from fastapi import HTTPException, status
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db_models.ml_model import MLModel, ModelMetric, TrainingRun
from app.db_models.user import User
from app.ml.opns_transformer import OPNsTransformer
from app.schemas.model_schema import ModelTrainRequest
from app.services.dataset_service import get_dataset, read_dataset_file


MODEL_STORAGE_DIR = Path("storage/models")
DEFAULT_TARGETS = ["M", "E", "S", "T", "C"]


def train_classification_model(db: Session, current_user: User, payload: ModelTrainRequest) -> MLModel:
    dataset = get_dataset(db, current_user, payload.dataset_id)
    dataframe = read_dataset_file(dataset)
    target_columns = [target for target in payload.target_columns if target in dataframe.columns]
    if not target_columns:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No target columns found in dataset")

    feature_columns = payload.feature_columns or [
        column for column in dataframe.columns if column not in target_columns and column not in DEFAULT_TARGETS
    ]
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
            classifier = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("svc", SVC(kernel="rbf", probability=True, random_state=payload.random_state)),
                ]
            )
            classifier.fit(X_train_model, y_train[target])
            predictions = classifier.predict(X_test_model)
            classifiers[target] = classifier
            metrics.extend(
                [
                    ModelMetric(model_id=model.id, target_name=target, metric_name="accuracy", metric_value=float(accuracy_score(y_test[target], predictions))),
                    ModelMetric(model_id=model.id, target_name=target, metric_name="precision", metric_value=float(precision_score(y_test[target], predictions, average="weighted", zero_division=0))),
                    ModelMetric(model_id=model.id, target_name=target, metric_name="recall", metric_value=float(recall_score(y_test[target], predictions, average="weighted", zero_division=0))),
                    ModelMetric(model_id=model.id, target_name=target, metric_name="f1", metric_value=float(f1_score(y_test[target], predictions, average="weighted", zero_division=0))),
                ]
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


def get_model(db: Session, current_user: User, model_id: int) -> MLModel:
    model = db.get(MLModel, model_id)
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


def get_model_metrics(db: Session, current_user: User, model_id: int) -> list[ModelMetric]:
    model = get_model(db, current_user, model_id)
    statement = select(ModelMetric).where(ModelMetric.model_id == model.id)
    return list(db.scalars(statement).all())

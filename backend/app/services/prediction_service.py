from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from fastapi.responses import FileResponse

from app.db_models.prediction import PredictionJob, PredictionResult
from app.db_models.user import User
from app.schemas.prediction_schema import RESEARCH_DISCLAIMER
from app.services.training_service import get_model
from app.utils.file_utils import ALLOWED_SUFFIXES, read_dataframe
from app.utils.igan_fields import display_target_name, format_prediction_label


PREDICTION_STORAGE_DIR = Path("storage/predictions")


def run_single_prediction(db: Session, current_user: User, model_id: int, input_data: dict[str, Any]) -> dict[str, Any]:
    model = get_model(db, current_user, model_id)
    feature_frame = build_feature_frame(model.feature_columns, [input_data])
    prediction = predict_frame(
        model.model_file_path, model.target_columns, feature_frame,
        opns_enabled=bool(model.opns_enabled),
    )
    job = save_prediction_job(db, current_user, model.id, "single", [input_data], [prediction])
    return {
        "job_id": job.id,
        "task": "igan_mestc",
        "result": prediction,
        "disclaimer": RESEARCH_DISCLAIMER,
    }


async def run_batch_prediction(db: Session, current_user: User, model_id: int, file: UploadFile) -> dict[str, Any]:
    model = get_model(db, current_user, model_id)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )

    PREDICTION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    input_path = PREDICTION_STORAGE_DIR / f"prediction_input_{uuid4().hex}{suffix}"
    input_path.write_bytes(await file.read())

    dataframe = read_dataframe(input_path)
    feature_frame = build_feature_frame(model.feature_columns, dataframe.to_dict(orient="records"))
    predictions = predict_frame(
        model.model_file_path, model.target_columns, feature_frame,
        as_list=True, opns_enabled=bool(model.opns_enabled),
    )
    rows: list[dict[str, Any]] = []
    for index, prediction in enumerate(predictions):
        row = dataframe.iloc[index].astype(object).where(pd.notnull(dataframe.iloc[index]), None).to_dict()
        for target, result in prediction.items():
            row[f"pred_{target}"] = result["label"]
            row[f"prob_{target}"] = result["probability"]
        rows.append(row)

    output_path = PREDICTION_STORAGE_DIR / f"prediction_output_{uuid4().hex}.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False)
    job = save_prediction_job(
        db,
        current_user,
        model.id,
        "batch",
        dataframe.to_dict(orient="records"),
        predictions,
        input_file_path=str(input_path),
        output_file_path=str(output_path),
    )
    return {"job_id": job.id, "rows": rows, "disclaimer": RESEARCH_DISCLAIMER}


def list_prediction_jobs(db: Session, current_user: User) -> list[PredictionJob]:
    statement = (
        select(PredictionJob)
        .where(PredictionJob.user_id == current_user.id)
        .order_by(PredictionJob.created_at.desc())
    )
    return list(db.scalars(statement).all())


# ── Regression prediction ──────────────────────────────────────────────────────


def run_single_regression_prediction(
    db: Session,
    current_user: User,
    model_id: int,
    input_data: dict[str, Any],
) -> dict[str, Any]:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not a regression model",
        )
    feature_frame = build_feature_frame(model.feature_columns, [input_data])
    predicted_value = predict_regression_frame(
        model.model_file_path, feature_frame,
        opns_enabled=bool(model.opns_enabled),
    )
    job = save_prediction_job(
        db, current_user, model.id, "regression_single",
        [input_data], [{"predicted_value": predicted_value}],
    )
    return {
        "job_id": job.id,
        "task": "regression",
        "target": model.target_columns[0] if model.target_columns else "target",
        "predicted_value": predicted_value,
        "disclaimer": RESEARCH_DISCLAIMER,
    }


async def run_batch_regression_prediction(
    db: Session,
    current_user: User,
    model_id: int,
    file: UploadFile,
) -> dict[str, Any]:
    model = get_model(db, current_user, model_id)
    if model.task_type != "regression":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not a regression model",
        )
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )

    PREDICTION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    input_path = PREDICTION_STORAGE_DIR / f"regression_input_{uuid4().hex}{suffix}"
    input_path.write_bytes(await file.read())

    dataframe = read_dataframe(input_path)
    feature_frame = build_feature_frame(model.feature_columns, dataframe.to_dict(orient="records"))
    predicted_values = predict_regression_frame(
        model.model_file_path, feature_frame,
        as_list=True, opns_enabled=bool(model.opns_enabled),
    )

    target_name = model.target_columns[0] if model.target_columns else "target"
    rows: list[dict[str, Any]] = []
    for index, pred_value in enumerate(predicted_values):
        row = dataframe.iloc[index].astype(object).where(pd.notnull(dataframe.iloc[index]), None).to_dict()
        row[f"pred_{target_name}"] = pred_value
        rows.append(row)

    output_path = PREDICTION_STORAGE_DIR / f"regression_output_{uuid4().hex}.csv"
    pd.DataFrame(rows).to_csv(output_path, index=False)
    predictions = [{"predicted_value": v} for v in predicted_values]
    job = save_prediction_job(
        db, current_user, model.id, "regression_batch",
        dataframe.to_dict(orient="records"), predictions,
        input_file_path=str(input_path), output_file_path=str(output_path),
    )
    return {"job_id": job.id, "rows": rows, "disclaimer": RESEARCH_DISCLAIMER}


def predict_regression_frame(
    model_dir: str | None,
    feature_frame: pd.DataFrame,
    as_list: bool = False,
    opns_enabled: bool = False,
) -> float | list[float]:
    if model_dir is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model files are missing")

    model_path = Path(model_dir)
    transformer_path = model_path / "opns_transformer.pkl"
    transformed = feature_frame
    if opns_enabled:
        if not transformer_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OPNs transformer file is missing for this model",
            )
        transformer = joblib.load(transformer_path)
        transformed = transformer.transform(feature_frame)

    regressor_path = model_path / "regressor.pkl"
    if not regressor_path.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Regressor file is missing")
    regressor = joblib.load(regressor_path)
    predictions = regressor.predict(transformed)
    values = [round(float(v), 4) for v in predictions]
    return values if as_list else values[0]


def build_feature_frame(feature_columns: list[str], records: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    for column in feature_columns:
        if column not in frame.columns:
            frame[column] = None
    return frame[feature_columns].apply(pd.to_numeric, errors="coerce")


def predict_frame(
    model_dir: str | None,
    target_columns: list[str],
    feature_frame: pd.DataFrame,
    as_list: bool = False,
    opns_enabled: bool = False,
) -> dict[str, Any] | list[dict[str, Any]]:
    if model_dir is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model files are missing")

    model_path = Path(model_dir)
    transformer_path = model_path / "opns_transformer.pkl"
    transformed = feature_frame
    if opns_enabled:
        if not transformer_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OPNs transformer file is missing for this model",
            )
        transformer = joblib.load(transformer_path)
        transformed = transformer.transform(feature_frame)

    per_target_predictions: dict[str, list[dict[str, Any]]] = {}
    for target in target_columns:
        classifier_path = model_path / f"{target}_classifier.pkl"
        if not classifier_path.exists():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Classifier for {target} is missing")
        classifier = joblib.load(classifier_path)
        labels = classifier.predict(transformed)
        probabilities = get_prediction_probabilities(classifier, transformed, labels)
        per_target_predictions[target] = [
            {
                "label": format_prediction_label(target, label),
                "probability": probability,
            }
            for label, probability in zip(labels, probabilities, strict=False)
        ]

    rows: list[dict[str, Any]] = []
    for row_index in range(len(feature_frame)):
        rows.append(
            {
                display_target_name(target): per_target_predictions[target][row_index]
                for target in target_columns
            }
        )
    return rows if as_list else rows[0]


def get_prediction_probabilities(classifier, transformed: pd.DataFrame, labels) -> list[float | None]:
    if not hasattr(classifier, "predict_proba"):
        return [None for _ in labels]
    probabilities = classifier.predict_proba(transformed)
    classes = list(classifier.classes_)
    result: list[float | None] = []
    for label, row in zip(labels, probabilities, strict=False):
        try:
            result.append(round(float(row[classes.index(label)]), 4))
        except ValueError:
            result.append(None)
    return result


def save_prediction_job(
    db: Session,
    current_user: User,
    model_id: int,
    job_type: str,
    inputs: list[dict[str, Any]],
    predictions: list[dict[str, Any]] | dict[str, Any],
    input_file_path: str | None = None,
    output_file_path: str | None = None,
) -> PredictionJob:
    job = PredictionJob(
        user_id=current_user.id,
        model_id=model_id,
        job_type=job_type,
        input_file_path=input_file_path,
        output_file_path=output_file_path,
        status="completed",
        finished_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    prediction_rows = predictions if isinstance(predictions, list) else [predictions]
    db.add_all(
        [
            PredictionResult(
                job_id=job.id,
                sample_index=index,
                input_json=inputs[index],
                prediction_json=prediction,
            )
            for index, prediction in enumerate(prediction_rows)
        ]
    )
    db.commit()
    db.refresh(job)
    return job


def get_prediction_detail(db: Session, current_user: User, job_id: int) -> dict:
    job = db.get(PredictionJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")

    statement = (
        select(PredictionResult)
        .where(PredictionResult.job_id == job.id)
        .order_by(PredictionResult.sample_index)
    )
    results = list(db.scalars(statement).all())

    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "model_id": job.model_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "sample_count": len(results),
        "results": [
            {
                "sample_index": r.sample_index,
                "input": r.input_json,
                "prediction": r.prediction_json,
            }
            for r in results
        ],
        "disclaimer": RESEARCH_DISCLAIMER,
    }


def delete_prediction(db: Session, current_user: User, job_id: int) -> None:
    job = db.get(PredictionJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")
    db.execute(delete(PredictionResult).where(PredictionResult.job_id == job.id))
    db.delete(job)
    db.commit()


def download_prediction_result(db: Session, current_user: User, job_id: int) -> FileResponse:
    job = db.get(PredictionJob, job_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction job not found")
    if job.output_file_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No output file for this job")
    output_path = Path(job.output_file_path)
    if not output_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not found on disk")
    return FileResponse(
        path=str(output_path),
        filename=f"prediction_results_{job.id}.csv",
        media_type="text/csv",
    )

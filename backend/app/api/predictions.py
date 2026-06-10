from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.prediction_schema import (
    BatchPredictionResponse,
    PredictionJobResponse,
    RegressionSinglePredictionResponse,
    RegressionSingleRequest,
    SinglePredictionRequest,
    SinglePredictionResponse,
)
from app.services import prediction_service


router = APIRouter(prefix="/api/predictions", tags=["predictions"])


# ── IgAN classification ──────────────────────────────────────────────────────

@router.post("/igan/single", response_model=SinglePredictionResponse)
def predict_single_igan(
    payload: SinglePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return prediction_service.run_single_prediction(db, current_user, payload.model_id, payload.input_data)


@router.post("/batch/run/{model_id}", response_model=BatchPredictionResponse)
async def predict_batch(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await prediction_service.run_batch_prediction(db, current_user, model_id, file)


# ── Regression ────────────────────────────────────────────────────────────────

@router.post("/regression/single", response_model=RegressionSinglePredictionResponse)
def predict_single_regression(
    payload: RegressionSingleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return prediction_service.run_single_regression_prediction(
        db, current_user, payload.model_id, payload.input_data,
    )


@router.post("/regression/batch/{model_id}", response_model=BatchPredictionResponse)
async def predict_batch_regression(
    model_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await prediction_service.run_batch_regression_prediction(
        db, current_user, model_id, file,
    )


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history", response_model=list[PredictionJobResponse])
def prediction_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return prediction_service.list_prediction_jobs(db, current_user)


@router.get("/{prediction_id}")
def get_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return prediction_service.get_prediction_detail(db, current_user, prediction_id)


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    prediction_service.delete_prediction(db, current_user, prediction_id)


@router.get("/batch/{job_id}/download")
def download_batch_prediction(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return prediction_service.download_prediction_result(db, current_user, job_id)

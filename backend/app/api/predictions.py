from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.prediction_schema import BatchPredictionResponse, PredictionJobResponse, SinglePredictionRequest, SinglePredictionResponse
from app.services import prediction_service


router = APIRouter(prefix="/api/predictions", tags=["predictions"])


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


@router.get("/history", response_model=list[PredictionJobResponse])
def prediction_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return prediction_service.list_prediction_jobs(db, current_user)

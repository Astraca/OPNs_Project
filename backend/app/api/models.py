from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.model_schema import ModelMetricResponse, ModelResponse, ModelTrainRequest
from app.services import training_service


router = APIRouter(prefix="/api/models", tags=["models"])


@router.post("/train", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def train_model(
    payload: ModelTrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return training_service.train_classification_model(db, current_user, payload)


@router.get("", response_model=list[ModelResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return training_service.list_models(db, current_user)


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return training_service.get_model(db, current_user, model_id)


@router.get("/{model_id}/metrics", response_model=list[ModelMetricResponse])
def get_model_metrics(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return training_service.get_model_metrics(db, current_user, model_id)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.evaluation_schema import (
    ClassificationMetricsResponse,
    ConfusionMatrixResponse,
    PredictedVsActualResponse,
    RegressionMetricsResponse,
    ResidualsResponse,
    RocCurveResponse,
)
from app.services import evaluation_service


router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


# ── Classification ─────────────────────────────────────────────────────────────

@router.get("/classification/{model_id}", response_model=ClassificationMetricsResponse)
def get_classification_metrics(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return evaluation_service.build_classification_metrics(db, current_user, model_id)


@router.get("/confusion-matrix/{model_id}", response_model=list[ConfusionMatrixResponse])
def get_confusion_matrix(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return evaluation_service.build_confusion_matrices(db, current_user, model_id)


@router.get("/roc/{model_id}", response_model=list[RocCurveResponse])
def get_roc_curves(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return evaluation_service.build_roc_curves(db, current_user, model_id)


# ── Regression ─────────────────────────────────────────────────────────────────

@router.get("/regression/{model_id}", response_model=RegressionMetricsResponse)
def get_regression_metrics(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return evaluation_service.build_regression_metrics(db, current_user, model_id)


@router.get("/residuals/{model_id}", response_model=ResidualsResponse)
def get_residuals(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return evaluation_service.build_residuals(db, current_user, model_id)


@router.get("/predicted-vs-actual/{model_id}", response_model=PredictedVsActualResponse)
def get_predicted_vs_actual(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return evaluation_service.build_predicted_vs_actual(db, current_user, model_id)

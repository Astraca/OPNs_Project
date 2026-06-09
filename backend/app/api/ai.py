from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.ai_schema import AIAnalysisReportResponse
from app.services import ai_analysis_service


router = APIRouter(prefix="/api/ai", tags=["ai"])


# ── Dataset analysis ──────────────────────────────────────────────────────────

@router.post("/dataset-analysis/{dataset_id}", response_model=AIAnalysisReportResponse)
async def generate_dataset_analysis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_dataset_analysis(db, current_user, dataset_id)


@router.get("/dataset-analysis/{dataset_id}", response_model=AIAnalysisReportResponse)
def get_dataset_analysis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ai_analysis_service.get_latest_dataset_analysis(db, current_user, dataset_id)


# ── Model analysis ────────────────────────────────────────────────────────────

@router.post("/model-analysis/{model_id}", response_model=AIAnalysisReportResponse)
async def generate_model_analysis(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_model_analysis(db, current_user, model_id)


@router.get("/model-analysis/{model_id}", response_model=AIAnalysisReportResponse)
def get_model_analysis(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ai_analysis_service.get_latest_model_analysis(db, current_user, model_id)


# ── Prediction explanation ────────────────────────────────────────────────────

@router.post("/prediction-explanation/{prediction_job_id}", response_model=AIAnalysisReportResponse)
async def generate_prediction_explanation(
    prediction_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_prediction_explanation(db, current_user, prediction_job_id)

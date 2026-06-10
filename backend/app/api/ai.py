from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import HTTPException, status as http_status

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.ai_schema import AIAnalysisReportResponse
from app.services import ai_analysis_service, dataset_service


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


@router.post("/dataset-role-suggestions/{dataset_id}", response_model=AIAnalysisReportResponse)
async def generate_dataset_role_suggestions(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_dataset_role_suggestions(db, current_user, dataset_id)


@router.post("/training-suggestions/{dataset_id}", response_model=AIAnalysisReportResponse)
async def generate_training_suggestions(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_training_suggestions(db, current_user, dataset_id)


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


# ── Training config suggestion ────────────────────────────────────────────────


@router.post("/training-config-suggestion/{dataset_id}", response_model=AIAnalysisReportResponse)
async def generate_training_config_suggestion(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_training_config_suggestion(db, current_user, dataset_id)


@router.get("/training-config-suggestion/{dataset_id}", response_model=AIAnalysisReportResponse)
def get_training_config_suggestion(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ai_analysis_service.get_latest_training_config_suggestion(db, current_user, dataset_id)


# ── Field analysis ────────────────────────────────────────────────────────────


@router.post("/field-analysis/{dataset_id}", response_model=AIAnalysisReportResponse)
async def generate_field_analysis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_field_analysis(db, current_user, dataset_id)


@router.get("/field-analysis/{dataset_id}", response_model=AIAnalysisReportResponse)
def get_field_analysis(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ai_analysis_service.get_latest_field_analysis(db, current_user, dataset_id)


@router.get("/field-analysis/{dataset_id}/recommendations")
def list_field_recommendations(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    return ai_analysis_service.get_field_recommendations(db, current_user, dataset_id)


# ── Privacy scan ──────────────────────────────────────────────────────────────


@router.post("/privacy-scan/{dataset_id}")
async def run_privacy_scan(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.ai.privacy_guard import scan_dataset
    from app.db_models.ai_privacy import AIPrivacyConfirmation

    dataset = dataset_service.get_dataset(db, current_user, dataset_id)
    columns = dataset_service.get_dataset_columns(db, current_user, dataset_id)
    result = scan_dataset(columns, dataset.sample_count)

    # Save confirmation record
    confirmation = AIPrivacyConfirmation(
        user_id=current_user.id,
        dataset_id=dataset_id,
        privacy_scan_result=result,
        has_privacy_risks=result["has_direct_identifiers"],
    )
    db.add(confirmation)
    db.commit()

    return {**result, "scan_id": confirmation.id, "confirmed": False}


@router.get("/privacy-scan/{dataset_id}")
def get_privacy_scan(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.db_models.ai_privacy import AIPrivacyConfirmation
    from sqlalchemy import select

    row = db.scalar(
        select(AIPrivacyConfirmation)
        .where(
            AIPrivacyConfirmation.dataset_id == dataset_id,
            AIPrivacyConfirmation.user_id == current_user.id,
        )
        .order_by(AIPrivacyConfirmation.created_at.desc())
        .limit(1)
    )
    if row is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No privacy scan found. Run POST first.",
        )
    return {
        **row.privacy_scan_result,
        "scan_id": row.id,
        "confirmed": row.confirmed_by_user,
    }


# ── Batch prediction analysis ────────────────────────────────────────────────


@router.post("/batch-prediction-analysis/{prediction_job_id}", response_model=AIAnalysisReportResponse)
async def generate_batch_prediction_analysis(
    prediction_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_batch_prediction_analysis(
        db, current_user, prediction_job_id,
    )


@router.get("/batch-prediction-analysis/{prediction_job_id}", response_model=AIAnalysisReportResponse)
def get_batch_prediction_analysis(
    prediction_job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.db_models.ai_report import AIAnalysisReport as AIReport

    report = db.scalar(
        select(AIReport)
        .where(
            AIReport.user_id == current_user.id,
            AIReport.prediction_job_id == prediction_job_id,
            AIReport.analysis_type == "batch_prediction_analysis",
        )
        .order_by(AIReport.created_at.desc())
        .limit(1)
    )
    if report is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No batch prediction analysis found. Generate one via POST first.",
        )
    return report


# ── OPNs pairing analysis ────────────────────────────────────────────────────


@router.post("/opns-pairing-analysis/{model_id}", response_model=AIAnalysisReportResponse)
async def generate_opns_pairing_analysis(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_opns_pairing_analysis(db, current_user, model_id)


@router.get("/opns-pairing-analysis/{model_id}", response_model=AIAnalysisReportResponse)
def get_opns_pairing_analysis(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    from app.db_models.ai_report import AIAnalysisReport as AIReport

    report = db.scalar(
        select(AIReport)
        .where(
            AIReport.user_id == current_user.id,
            AIReport.model_id == model_id,
            AIReport.analysis_type == "opns_pairing_analysis",
        )
        .order_by(AIReport.created_at.desc())
        .limit(1)
    )
    if report is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No OPNs pairing analysis found. Generate one via POST first.",
        )
    return report


# ── Chart interpretation ─────────────────────────────────────────────────────


@router.post("/chart-interpretation", response_model=AIAnalysisReportResponse)
async def interpret_chart(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ai_analysis_service.generate_chart_interpretation(db, current_user, payload)

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.report_schema import ReportGenerateRequest, ReportResponse
from app.services import report_service


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate/{model_id}", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    model_id: int,
    payload: ReportGenerateRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = payload.title if payload else None
    return report_service.generate_experiment_report(db, current_user, model_id, title)


@router.get("", response_model=list[ReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return report_service.list_reports(db, current_user)


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return report_service.get_report(db, current_user, report_id)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    report_service.delete_report(db, current_user, report_id)

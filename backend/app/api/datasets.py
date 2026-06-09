from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.db_models.user import User
from app.dependencies import get_current_user
from app.schemas.dataset_schema import (
    CorrelationMatrixResponse,
    DatasetColumnResponse,
    DatasetCreateRequest,
    DatasetPreviewResponse,
    DatasetProfileResponse,
    DatasetResponse,
    LabelDistributionResponse,
    MissingValuesChartResponse,
    NumericStatisticsResponse,
)
from app.services import dataset_service


router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.create_dataset(db, current_user, payload)


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.list_datasets(db, current_user)


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_dataset(db, current_user, dataset_id)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    dataset_service.delete_dataset(db, current_user, dataset_id)


@router.post("/{dataset_id}/upload", response_model=DatasetResponse)
async def upload_dataset_file(
    dataset_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await dataset_service.save_upload_file(db, current_user, dataset_id, file)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_preview(db, current_user, dataset_id)


@router.get("/{dataset_id}/columns", response_model=list[DatasetColumnResponse])
def get_dataset_columns(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_dataset_columns(db, current_user, dataset_id)


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
def get_dataset_profile(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_profile(db, current_user, dataset_id)


@router.get("/{dataset_id}/charts/missing-values", response_model=MissingValuesChartResponse)
def get_missing_values_chart(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_missing_values_chart(db, current_user, dataset_id)


@router.get("/{dataset_id}/charts/label-distribution", response_model=LabelDistributionResponse)
def get_label_distribution_chart(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_label_distribution_chart(db, current_user, dataset_id)


@router.get("/{dataset_id}/charts/numeric-statistics", response_model=NumericStatisticsResponse)
def get_numeric_statistics_chart(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_numeric_statistics_chart(db, current_user, dataset_id)


@router.get("/{dataset_id}/charts/correlation", response_model=CorrelationMatrixResponse)
def get_correlation_matrix_chart(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dataset_service.get_correlation_matrix_chart(db, current_user, dataset_id)

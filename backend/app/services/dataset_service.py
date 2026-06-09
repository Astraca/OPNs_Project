from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db_models.dataset import Dataset, DatasetColumn
from app.db_models.user import User
from app.schemas.dataset_schema import DatasetCreateRequest


STORAGE_DIR = Path("storage/datasets")
ALLOWED_SUFFIXES = {".csv", ".xlsx"}
IGAN_TARGET_COLUMNS = {"M", "E", "S", "T", "C"}


def create_dataset(db: Session, current_user: User, payload: DatasetCreateRequest) -> Dataset:
    dataset = Dataset(
        user_id=current_user.id,
        name=payload.name,
        task_type=payload.task_type,
        description=payload.description,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def list_datasets(db: Session, current_user: User) -> list[Dataset]:
    statement = select(Dataset).where(Dataset.user_id == current_user.id).order_by(Dataset.created_at.desc())
    return list(db.scalars(statement).all())


def get_dataset(db: Session, current_user: User, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or dataset.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


def delete_dataset(db: Session, current_user: User, dataset_id: int) -> None:
    dataset = get_dataset(db, current_user, dataset_id)
    db.execute(delete(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id))
    db.delete(dataset)
    db.commit()


async def save_upload_file(db: Session, current_user: User, dataset_id: int, file: UploadFile) -> Dataset:
    dataset = get_dataset(db, current_user, dataset_id)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and XLSX files are supported",
        )

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"dataset_{dataset.id}_{uuid4().hex}{suffix}"
    file_path = STORAGE_DIR / stored_name
    file_path.write_bytes(await file.read())

    dataframe = read_dataframe(file_path)
    target_columns = [column for column in dataframe.columns if column in IGAN_TARGET_COLUMNS]

    dataset.file_path = str(file_path)
    dataset.file_type = suffix.lstrip(".")
    dataset.sample_count = int(len(dataframe))
    dataset.feature_count = int(len(dataframe.columns))
    dataset.target_columns = target_columns

    db.execute(delete(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id))
    db.add_all(build_column_summaries(dataset.id, dataframe, target_columns))
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_columns(db: Session, current_user: User, dataset_id: int) -> list[DatasetColumn]:
    dataset = get_dataset(db, current_user, dataset_id)
    statement = select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id)
    return list(db.scalars(statement).all())


def get_preview(db: Session, current_user: User, dataset_id: int, limit: int = 50) -> dict[str, Any]:
    dataset = get_dataset(db, current_user, dataset_id)
    dataframe = read_dataset_file(dataset)
    preview = dataframe.head(limit)
    return {
        "columns": list(preview.columns),
        "rows": dataframe_to_records(preview),
        "total_rows": int(len(dataframe)),
    }


def get_profile(db: Session, current_user: User, dataset_id: int) -> dict[str, Any]:
    dataset = get_dataset(db, current_user, dataset_id)
    columns = get_dataset_columns(db, current_user, dataset_id)
    dataframe = read_dataset_file(dataset)
    target_distribution: dict[str, dict[str, int]] = {}
    for target in dataset.target_columns:
        if target in dataframe.columns:
            counts = dataframe[target].astype(str).value_counts(dropna=False).to_dict()
            target_distribution[target] = {str(key): int(value) for key, value in counts.items()}

    return {
        "dataset": dataset,
        "columns": columns,
        "missing_values": {column.column_name: column.missing_count for column in columns},
        "target_distribution": target_distribution,
    }


def read_dataset_file(dataset: Dataset) -> pd.DataFrame:
    if dataset.file_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset file has not been uploaded")
    return read_dataframe(Path(dataset.file_path))


def read_dataframe(file_path: Path) -> pd.DataFrame:
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)
    if file_path.suffix.lower() == ".xlsx":
        return pd.read_excel(file_path)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported dataset file type")


def build_column_summaries(
    dataset_id: int,
    dataframe: pd.DataFrame,
    target_columns: list[str],
) -> list[DatasetColumn]:
    summaries: list[DatasetColumn] = []
    for column_name in dataframe.columns:
        series = dataframe[column_name]
        numeric_series = pd.to_numeric(series, errors="coerce")
        has_numeric_values = numeric_series.notna().any()
        summaries.append(
            DatasetColumn(
                dataset_id=dataset_id,
                column_name=str(column_name),
                data_type=str(series.dtype),
                role="target" if column_name in target_columns else "feature",
                missing_count=int(series.isna().sum()),
                unique_count=int(series.nunique(dropna=True)),
                mean=float(numeric_series.mean()) if has_numeric_values else None,
                std=float(numeric_series.std()) if has_numeric_values else None,
                min_value=float(numeric_series.min()) if has_numeric_values else None,
                max_value=float(numeric_series.max()) if has_numeric_values else None,
            )
        )
    return summaries


def dataframe_to_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    clean = dataframe.astype(object).where(pd.notnull(dataframe), None)
    return clean.to_dict(orient="records")

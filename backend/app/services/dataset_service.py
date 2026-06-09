from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db_models.dataset import Dataset, DatasetColumn
from app.db_models.user import User
from app.schemas.dataset_schema import DatasetColumnRolesUpdateRequest, DatasetCreateRequest
from app.utils.file_utils import ALLOWED_SUFFIXES, read_dataframe
from app.utils.igan_fields import (
    get_default_feature_columns,
    get_mestc_target_columns,
    get_output_columns,
    infer_column_role,
    suggest_target_columns,
)


STORAGE_DIR = Path("storage/datasets")


def create_dataset(db: Session, current_user: User, payload: DatasetCreateRequest) -> Dataset:
    # Check for duplicate name under the same user + task type
    existing = db.scalar(
        select(Dataset).where(
            Dataset.user_id == current_user.id,
            Dataset.task_type == payload.task_type,
            Dataset.name == payload.name,
        ),
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"数据集名称 '{payload.name}' 在当前任务类型下已存在，请使用其他名称",
        )

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


def update_dataset_column_roles(
    db: Session,
    current_user: User,
    dataset_id: int,
    payload: DatasetColumnRolesUpdateRequest,
) -> list[DatasetColumn]:
    dataset = get_dataset(db, current_user, dataset_id)
    columns = get_dataset_columns(db, current_user, dataset.id)
    columns_by_name = {column.column_name: column for column in columns}
    for update in payload.columns:
        if update.column_name in columns_by_name:
            columns_by_name[update.column_name].role = update.role

    dataset.target_columns = [
        column.column_name
        for column in columns
        if column.role == "target"
    ]
    db.commit()
    return get_dataset_columns(db, current_user, dataset.id)


def update_dataset(db: Session, current_user: User, dataset_id: int, payload: DatasetCreateRequest) -> Dataset:
    dataset = get_dataset(db, current_user, dataset_id)

    # Check for duplicate name under same user + new task type
    if payload.name != dataset.name or payload.task_type != dataset.task_type:
        existing = db.scalar(
            select(Dataset).where(
                Dataset.user_id == current_user.id,
                Dataset.task_type == payload.task_type,
                Dataset.name == payload.name,
                Dataset.id != dataset_id,
            ),
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"数据集名称 '{payload.name}' 在当前任务类型下已存在",
            )

    dataset.name = payload.name
    dataset.task_type = payload.task_type
    dataset.description = payload.description
    db.commit()
    db.refresh(dataset)
    return dataset


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


# 10 MB max file size
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


async def save_upload_file(db: Session, current_user: User, dataset_id: int, file: UploadFile) -> Dataset:
    dataset = get_dataset(db, current_user, dataset_id)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )

    # Read and validate file size
    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({len(raw_bytes)} bytes). Maximum is {MAX_UPLOAD_BYTES} bytes (10 MB).",
        )

    # ── Clean up old file before saving new one ───────────────────────────
    if dataset.file_path:
        old_path = Path(dataset.file_path)
        if old_path.exists():
            old_path.unlink()

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"dataset_{dataset.id}_{uuid4().hex}{suffix}"
    file_path = STORAGE_DIR / stored_name
    file_path.write_bytes(raw_bytes)

    dataframe = read_dataframe(file_path)
    columns = [str(column) for column in dataframe.columns]

    # Auto-detect target columns
    target_columns = get_output_columns(columns)
    if not target_columns:
        target_columns = get_mestc_target_columns(columns)
    if not target_columns:
        target_columns = suggest_target_columns(columns, dataset.task_type)

    dataset.file_path = str(file_path)
    dataset.file_type = suffix.lstrip(".")
    dataset.sample_count = int(len(dataframe))
    dataset.feature_count = int(len(dataframe.columns))
    dataset.target_columns = target_columns

    # Replace old column metadata
    db.execute(delete(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id))
    summaries = build_column_summaries(dataset.id, dataframe, target_columns)

    # ── Auto-ignore low-quality features ──────────────────────────────────
    total_samples = len(dataframe)
    target_set = set(target_columns)
    auto_ignored: list[str] = []
    for col in summaries:
        if col.column_name in target_set:
            continue
        if col.missing_count >= total_samples:
            col.role = "ignored"
            auto_ignored.append(f"{col.column_name}(全缺失)")
        elif col.unique_count <= 1:
            col.role = "ignored"
            auto_ignored.append(f"{col.column_name}(常量)")

    db.add_all(summaries)

    # ── Update description: strip old auto-ignore notes, append new ones ──
    _AUTO_IGNORE_PREFIX = "【自动忽略低质量特征】"
    existing_desc = dataset.description or ""
    # Remove any previous auto-ignore line
    lines = existing_desc.split("\n")
    cleaned_lines = [line for line in lines if not line.startswith(_AUTO_IGNORE_PREFIX)]
    base_desc = "\n".join(cleaned_lines).strip()

    if auto_ignored:
        note = _AUTO_IGNORE_PREFIX + "、".join(auto_ignored)
        dataset.description = f"{base_desc}\n{note}".strip() if base_desc else note
    else:
        dataset.description = base_desc or None

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
        "missing_values": {column.column_name: column.missing_count for column in columns if column.role != "ignored"},
        "target_distribution": target_distribution,
    }


def get_missing_values_chart(db: Session, current_user: User, dataset_id: int) -> dict[str, Any]:
    dataset = get_dataset(db, current_user, dataset_id)
    columns = [column for column in get_dataset_columns(db, current_user, dataset_id) if column.role != "ignored"]
    total_rows = dataset.sample_count or 0
    return {
        "total_rows": total_rows,
        "items": [
            {
                "column_name": column.column_name,
                "missing_count": column.missing_count,
                "missing_rate": (column.missing_count / total_rows) if total_rows else 0,
            }
            for column in columns
        ],
    }


def get_label_distribution_chart(db: Session, current_user: User, dataset_id: int) -> dict[str, Any]:
    dataset = get_dataset(db, current_user, dataset_id)
    dataframe = read_dataset_file(dataset)
    distributions: dict[str, dict[str, int]] = {}
    target_columns = dataset.target_columns or get_output_columns([str(column) for column in dataframe.columns])
    for target in target_columns:
        if target in dataframe.columns:
            counts = dataframe[target].astype(str).value_counts(dropna=False).to_dict()
            distributions[target] = {str(key): int(value) for key, value in counts.items()}
    return {"distributions": distributions}


def get_numeric_statistics_chart(db: Session, current_user: User, dataset_id: int) -> dict[str, Any]:
    columns = [column for column in get_dataset_columns(db, current_user, dataset_id) if column.role == "feature"]
    return {
        "items": [
            {
                "column_name": column.column_name,
                "mean": column.mean,
                "std": column.std,
                "min_value": column.min_value,
                "max_value": column.max_value,
                "missing_count": column.missing_count,
            }
            for column in columns
            if column.mean is not None
        ]
    }


def get_correlation_matrix_chart(db: Session, current_user: User, dataset_id: int) -> dict[str, Any]:
    dataset = get_dataset(db, current_user, dataset_id)
    dataframe = read_dataset_file(dataset)
    dataset_columns = get_dataset_columns(db, current_user, dataset_id)
    feature_columns = [column.column_name for column in dataset_columns if column.role == "feature"]
    if not feature_columns:
        feature_columns = get_default_feature_columns([str(column) for column in dataframe.columns], dataset.target_columns)
    numeric_dataframe = dataframe[feature_columns].apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    if numeric_dataframe.empty:
        return {"columns": [], "matrix": []}

    correlation = numeric_dataframe.corr()
    columns = [str(column) for column in correlation.columns]
    matrix: list[list[float | None]] = []
    for row in correlation.to_numpy().tolist():
        matrix.append([None if pd.isna(value) else round(float(value), 4) for value in row])
    return {"columns": columns, "matrix": matrix}


def get_numeric_distribution_chart(
    db: Session,
    current_user: User,
    dataset_id: int,
    column: str | None = None,
    bins: int = 20,
) -> dict[str, Any]:
    """Return histogram data for numeric feature columns."""
    dataset = get_dataset(db, current_user, dataset_id)
    dataframe = read_dataset_file(dataset)
    dataset_columns = get_dataset_columns(db, current_user, dataset_id)
    feature_columns = [
        col.column_name for col in dataset_columns
        if col.role == "feature" and col.mean is not None
    ]
    if not feature_columns:
        feature_columns = get_default_feature_columns(
            [str(c) for c in dataframe.columns], dataset.target_columns,
        )

    numeric_dataframe = dataframe[feature_columns].apply(pd.to_numeric, errors="coerce")

    targets = column or feature_columns  # type: ignore[assignment]
    if isinstance(targets, str):
        targets = [targets]

    distributions: dict[str, dict[str, list[float]]] = {}
    for col in targets:  # type: ignore[assignment]
        col_str = str(col)
        if col_str not in numeric_dataframe.columns:
            continue
        series = numeric_dataframe[col_str].dropna()
        if series.empty:
            continue
        counts, bin_edges = pd.cut(series, bins=min(bins, len(series.unique())), retbins=True)  # type: ignore[call-overload]
        hist_values = counts.value_counts().sort_index()  # type: ignore[attr-defined]
        distributions[col_str] = {
            "bin_centers": [round(float((bin_edges[i] + bin_edges[i + 1]) / 2), 4) for i in range(len(bin_edges) - 1)],
            "counts": [int(v) for v in hist_values.values],
            "bin_edges": [round(float(v), 4) for v in bin_edges],
        }

    return {"columns": list(distributions.keys()), "distributions": distributions}


def read_dataset_file(dataset: Dataset) -> pd.DataFrame:
    if dataset.file_path is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset file has not been uploaded")
    return read_dataframe(Path(dataset.file_path))


def build_column_summaries(
    dataset_id: int,
    dataframe: pd.DataFrame,
    target_columns: list[str],
) -> list[DatasetColumn]:
    summaries: list[DatasetColumn] = []
    for column_name in dataframe.columns:
        series = dataframe[column_name]
        numeric_series = pd.to_numeric(series, errors="coerce")
        valid_count = int(numeric_series.notna().sum())
        total_count = int(len(series))
        # Only compute stats when at least half the values are valid numeric
        has_enough_valid = valid_count >= 1 and (total_count == 0 or valid_count >= total_count * 0.5)

        # Infer effective dtype: if original is object/string but most values
        # are numeric, report as the detected numeric type
        dtype_str = str(series.dtype)
        non_numeric_dtypes = {"object", "string", "str"}
        if dtype_str.lower() in non_numeric_dtypes and has_enough_valid:
            # Check if values look like integers or floats
            dropped = numeric_series.dropna()
            if len(dropped) > 0:
                if (dropped == dropped.astype(int)).all():
                    dtype_str = "int64"
                else:
                    dtype_str = "float64"

        summaries.append(
            DatasetColumn(
                dataset_id=dataset_id,
                column_name=str(column_name),
                data_type=dtype_str,
                role=infer_column_role(str(column_name), target_columns),
                missing_count=int(series.isna().sum()),
                unique_count=int(series.nunique(dropna=True)),
                mean=float(numeric_series.mean()) if has_enough_valid else None,
                std=float(numeric_series.std()) if has_enough_valid else None,
                min_value=float(numeric_series.min()) if has_enough_valid else None,
                max_value=float(numeric_series.max()) if has_enough_valid else None,
            )
        )
    return summaries


def dataframe_to_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    clean = dataframe.astype(object).where(pd.notnull(dataframe), None)
    return clean.to_dict(orient="records")

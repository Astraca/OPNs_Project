from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


TaskType = Literal["classification", "regression", "multi_output_classification"]


class DatasetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    task_type: TaskType = "classification"
    description: str | None = Field(default=None, max_length=2000)


class DatasetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    task_type: str
    description: str | None
    file_path: str | None
    file_type: str | None
    sample_count: int
    feature_count: int
    target_columns: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetColumnResponse(BaseModel):
    id: int
    dataset_id: int
    column_name: str
    data_type: str
    role: str
    missing_count: int
    unique_count: int
    mean: float | None
    std: float | None
    min_value: float | None
    max_value: float | None

    model_config = {"from_attributes": True}


class DatasetPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int


class DatasetProfileResponse(BaseModel):
    dataset: DatasetResponse
    columns: list[DatasetColumnResponse]
    missing_values: dict[str, int]
    target_distribution: dict[str, dict[str, int]]

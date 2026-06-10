"""Pydantic schemas for dataset context CRUD."""

from datetime import datetime

from pydantic import BaseModel, Field


class DatasetContextPayload(BaseModel):
    dataset_source: str | None = None
    scenario_description: str | None = None
    inclusion_criteria: str | None = None
    exclusion_criteria: str | None = None
    feature_descriptions: dict[str, str] = Field(default_factory=dict)
    target_descriptions: dict[str, str] = Field(default_factory=dict)
    usage_notes: str | None = None


class DatasetContextResponse(BaseModel):
    id: int
    dataset_id: int
    user_id: int
    dataset_source: str | None
    scenario_description: str | None
    inclusion_criteria: str | None
    exclusion_criteria: str | None
    feature_descriptions: dict
    target_descriptions: dict
    usage_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

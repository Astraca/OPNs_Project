"""Pydantic schemas for AI field analysis."""

from pydantic import BaseModel, Field


class FieldRecommendationItem(BaseModel):
    field: str
    recommendation: str  # one of 9 accepted types
    reason: str
    risk_level: str  # high / medium / low
    requires_user_confirmation: bool = False


class FieldAnalysisResponse(BaseModel):
    id: int
    user_id: int
    dataset_id: int
    analysis_type: str
    input_summary_json: dict
    generated_text: str
    created_at: str

    model_config = {"from_attributes": True}


class FieldConfirmationItem(BaseModel):
    field: str
    accepted: bool
    modification: str | None = None


class FieldConfirmationRequest(BaseModel):
    confirmations: list[FieldConfirmationItem] = Field(..., min_length=1)

from datetime import datetime

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    model_id: int
    title: str | None = Field(default=None, max_length=256)


class ReportResponse(BaseModel):
    id: int
    user_id: int
    model_id: int | None
    dataset_id: int | None
    title: str
    content: str
    report_type: str
    created_at: datetime

    model_config = {"from_attributes": True}

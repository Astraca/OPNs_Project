from datetime import datetime

from pydantic import BaseModel


class AIAnalysisReportResponse(BaseModel):
    id: int
    user_id: int
    dataset_id: int | None
    model_id: int | None
    prediction_job_id: int | None
    analysis_type: str
    input_summary_json: dict
    generated_text: str
    created_at: datetime

    model_config = {"from_attributes": True}

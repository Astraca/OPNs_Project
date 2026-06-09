from datetime import datetime
from typing import Any

from pydantic import BaseModel


RESEARCH_DISCLAIMER = (
    "本系统预测结果仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。"
    "实际医学判断应由具有资质的临床医生结合完整病史、检查结果和病理资料完成。"
)


class SinglePredictionRequest(BaseModel):
    model_id: int
    input_data: dict[str, Any]


class PredictionLabelResult(BaseModel):
    label: str
    probability: float | None = None


class SinglePredictionResponse(BaseModel):
    job_id: int
    task: str = "igan_mestc"
    result: dict[str, PredictionLabelResult]
    disclaimer: str = RESEARCH_DISCLAIMER


class RegressionSingleRequest(BaseModel):
    model_id: int
    input_data: dict[str, Any]


class RegressionSinglePredictionResponse(BaseModel):
    job_id: int
    task: str = "regression"
    target: str
    predicted_value: float
    disclaimer: str = RESEARCH_DISCLAIMER


class BatchPredictionResponse(BaseModel):
    job_id: int
    rows: list[dict[str, Any]]
    disclaimer: str = RESEARCH_DISCLAIMER


class PredictionJobResponse(BaseModel):
    id: int
    user_id: int
    model_id: int
    dataset_id: int | None
    job_type: str
    input_file_path: str | None
    output_file_path: str | None
    status: str
    created_at: datetime
    finished_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}

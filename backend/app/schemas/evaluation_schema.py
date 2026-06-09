from pydantic import BaseModel


# --- Classification ---

class ClassificationMetricItem(BaseModel):
    target_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float


class ClassificationMetricsResponse(BaseModel):
    model_id: int
    algorithm: str
    metrics: list[ClassificationMetricItem]


class ConfusionMatrixResponse(BaseModel):
    target_name: str
    labels: list[str]
    matrix: list[list[int]]


class RocCurveItem(BaseModel):
    fpr: list[float]
    tpr: list[float]
    auc: float


class RocCurveResponse(BaseModel):
    target_name: str
    curves: list[RocCurveItem]


# --- Regression ---

class RegressionMetricItem(BaseModel):
    target_name: str
    mae: float
    rmse: float
    r2: float
    mape: float | None = None


class RegressionMetricsResponse(BaseModel):
    model_id: int
    algorithm: str
    metrics: RegressionMetricItem


class PredictedVsActualResponse(BaseModel):
    target_name: str
    actual: list[float]
    predicted: list[float]


class ResidualsResponse(BaseModel):
    target_name: str
    residuals: list[float]
    predicted: list[float]

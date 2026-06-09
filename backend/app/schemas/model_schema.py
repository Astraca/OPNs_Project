from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ClassificationAlgorithm = Literal["SVM", "OPNs-SVM", "RandomForest", "LogisticRegression"]
RegressionAlgorithm = Literal["SVR", "OPNs-SVR", "RandomForest", "Ridge"]
Algorithm = Literal["SVM", "OPNs-SVM", "SVR", "OPNs-SVR", "RandomForest", "LogisticRegression", "Ridge"]
PairingMethod = Literal["adjacent", "random", "correlation_greedy"]


class ModelTrainRequest(BaseModel):
    dataset_id: int
    model_name: str = Field(min_length=1, max_length=128)
    algorithm: Algorithm = "OPNs-SVM"
    target_columns: list[str] = Field(default_factory=lambda: ["out-M", "out-E", "out-S", "out-T", "out-C"])
    feature_columns: list[str] | None = None
    pairing_method: PairingMethod = "adjacent"
    test_size: float = Field(default=0.2, gt=0, lt=0.5)
    random_state: int = 42


class RegressionTrainRequest(BaseModel):
    dataset_id: int
    model_name: str = Field(min_length=1, max_length=128)
    algorithm: RegressionAlgorithm = "OPNs-SVR"
    target_column: str = Field(min_length=1, max_length=128)
    feature_columns: list[str] | None = None
    pairing_method: PairingMethod = "adjacent"
    test_size: float = Field(default=0.2, gt=0, lt=0.5)
    random_state: int = 42


class ModelResponse(BaseModel):
    id: int
    user_id: int
    dataset_id: int
    model_name: str
    task_type: str
    algorithm: str
    target_columns: list[str]
    feature_columns: list[str]
    opns_enabled: bool
    pairing_method: str | None
    mapping_config: dict
    hyperparameters: dict
    model_file_path: str | None
    scaler_file_path: str | None
    metadata_file_path: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ModelMetricResponse(BaseModel):
    id: int
    model_id: int
    target_name: str | None
    metric_name: str
    metric_value: float
    created_at: datetime

    model_config = {"from_attributes": True}

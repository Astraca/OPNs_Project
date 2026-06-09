export type ModelAlgorithm =
  | "SVM" | "OPNs-SVM"
  | "SVR" | "OPNs-SVR"
  | "RandomForest" | "LogisticRegression"
  | "Ridge";
export type PairingMethod = "adjacent" | "random" | "correlation_greedy";

export type MLModel = {
  id: number;
  user_id: number;
  dataset_id: number;
  model_name: string;
  task_type: string;
  algorithm: ModelAlgorithm;
  target_columns: string[];
  feature_columns: string[];
  opns_enabled: boolean;
  pairing_method: PairingMethod | null;
  mapping_config: Record<string, unknown>;
  hyperparameters: Record<string, unknown>;
  model_file_path: string | null;
  scaler_file_path: string | null;
  metadata_file_path: string | null;
  created_at: string;
  updated_at: string;
};

export type ModelTrainPayload = {
  dataset_id: number;
  model_name: string;
  algorithm: ModelAlgorithm;
  task_type: string;
  target_columns: string[];
  pairing_method: PairingMethod;
  test_size: number;
  random_state: number;
};

export type RegressionTrainPayload = {
  dataset_id: number;
  model_name: string;
  algorithm: "SVR" | "OPNs-SVR";
  target_column: string;
  feature_columns?: string[];
  pairing_method: PairingMethod;
  test_size: number;
  random_state: number;
};

export type ModelMetric = {
  id: number;
  model_id: number;
  target_name: string | null;
  metric_name: string;
  metric_value: number;
  created_at: string;
};

// ── Evaluation types ──────────────────────────────────────────────────────────

export type ClassificationMetricItem = {
  target_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
};

export type ClassificationMetricsResponse = {
  model_id: number;
  algorithm: string;
  metrics: ClassificationMetricItem[];
};

export type ConfusionMatrixData = {
  target_name: string;
  labels: string[];
  matrix: number[][];
};

export type RocCurveItem = {
  fpr: number[];
  tpr: number[];
  auc: number;
};

export type RocCurveData = {
  target_name: string;
  curves: RocCurveItem[];
};

export type RegressionMetricItem = {
  target_name: string;
  mae: number;
  rmse: number;
  r2: number;
  mape: number | null;
};

export type RegressionMetricsResponse = {
  model_id: number;
  algorithm: string;
  metrics: RegressionMetricItem;
};

export type PredictedVsActualData = {
  target_name: string;
  actual: number[];
  predicted: number[];
};

export type ResidualsData = {
  target_name: string;
  residuals: number[];
  predicted: number[];
};

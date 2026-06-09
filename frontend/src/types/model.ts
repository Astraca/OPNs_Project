export type ModelAlgorithm = "SVM" | "OPNs-SVM";
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
  target_columns: string[];
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

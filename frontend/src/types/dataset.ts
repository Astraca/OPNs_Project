export type DatasetTaskType = "classification" | "regression" | "multi_output_classification";

export type Dataset = {
  id: number;
  user_id: number;
  name: string;
  task_type: DatasetTaskType;
  description: string | null;
  file_path: string | null;
  file_type: string | null;
  sample_count: number;
  feature_count: number;
  target_columns: string[];
  created_at: string;
  updated_at: string;
};

export type DatasetColumn = {
  id: number;
  dataset_id: number;
  column_name: string;
  data_type: string;
  role: string;
  missing_count: number;
  unique_count: number;
  mean: number | null;
  std: number | null;
  min_value: number | null;
  max_value: number | null;
};

export type DatasetCreatePayload = {
  name: string;
  task_type: DatasetTaskType;
  description?: string;
};

export type DatasetPreview = {
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
};

export type DatasetProfile = {
  dataset: Dataset;
  columns: DatasetColumn[];
  missing_values: Record<string, number>;
  target_distribution: Record<string, Record<string, number>>;
};

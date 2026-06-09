export type DatasetTaskType = "classification" | "regression" | "multi_output_classification";
export type DatasetColumnRole = "feature" | "target" | "ignored";

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
  role: DatasetColumnRole;
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

export type DatasetColumnRoleUpdate = {
  column_name: string;
  role: DatasetColumnRole;
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

export type MissingValueItem = {
  column_name: string;
  missing_count: number;
  missing_rate: number;
};

export type MissingValuesChartData = {
  total_rows: number;
  items: MissingValueItem[];
};

export type LabelDistributionData = {
  distributions: Record<string, Record<string, number>>;
};

export type NumericStatisticsItem = {
  column_name: string;
  mean: number | null;
  std: number | null;
  min_value: number | null;
  max_value: number | null;
  missing_count: number;
};

export type NumericStatisticsData = {
  items: NumericStatisticsItem[];
};

export type CorrelationMatrixData = {
  columns: string[];
  matrix: (number | null)[][];
};

export type NumericDistributionItem = {
  bin_centers: number[];
  counts: number[];
  bin_edges: number[];
};

export type NumericDistributionData = {
  columns: string[];
  distributions: Record<string, NumericDistributionItem>;
};

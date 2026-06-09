export type PredictionLabelResult = {
  label: string;
  probability: number | null;
};

export type SinglePredictionPayload = {
  model_id: number;
  input_data: Record<string, unknown>;
};

export type SinglePredictionResponse = {
  job_id: number;
  task: string;
  result: Record<string, PredictionLabelResult>;
  disclaimer: string;
};

export type BatchPredictionResponse = {
  job_id: number;
  rows: Record<string, unknown>[];
  disclaimer: string;
};

export type PredictionJob = {
  id: number;
  user_id: number;
  model_id: number;
  dataset_id: number | null;
  job_type: string;
  input_file_path: string | null;
  output_file_path: string | null;
  status: string;
  created_at: string;
  finished_at: string | null;
  error_message: string | null;
};

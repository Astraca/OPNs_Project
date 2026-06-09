export type AIAnalysisReport = {
  id: number;
  user_id: number;
  dataset_id: number | null;
  model_id: number | null;
  prediction_job_id: number | null;
  analysis_type: string;
  input_summary_json: Record<string, unknown>;
  generated_text: string;
  created_at: string;
};

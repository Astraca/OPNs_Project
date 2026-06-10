export type Report = {
  id: number;
  user_id: number;
  model_id: number | null;
  dataset_id: number | null;
  title: string;
  content: string;
  report_type: string;
  created_at: string;
};

export type ReportGeneratePayload = {
  title?: string;
};

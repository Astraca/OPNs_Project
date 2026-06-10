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

export type PrivacyFieldItem = {
  field: string;
  classification: "direct_identifier" | "quasi_identifier" | "sensitive_medical" | "normal_modeling";
  reason: string;
  risk_level: "high" | "medium" | "low";
};

export type PrivacyScanResult = {
  classifications: PrivacyFieldItem[];
  has_direct_identifiers: boolean;
  has_quasi_identifiers: boolean;
  sensitive_medical_count: number;
  risk_summary: string;
  scan_id: number;
  confirmed: boolean;
};

export type FieldRecommendation = {
  id?: number;
  field: string;
  recommendation: string;
  reason: string;
  risk_level: string;
  requires_user_confirmation: boolean;
  user_confirmed?: boolean | null;
  user_modification?: string | null;
};

export type FieldConfirmationItem = {
  field: string;
  accepted: boolean;
  modification?: string | null;
};

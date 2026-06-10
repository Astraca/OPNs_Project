import { request } from "./request";
import type { AIAnalysisReport, PrivacyScanResult } from "../types/ai";


export async function generateDatasetAnalysis(datasetId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/dataset-analysis/${datasetId}`);
  return data;
}

export async function generateDatasetRoleSuggestions(datasetId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/dataset-role-suggestions/${datasetId}`);
  return data;
}

export async function generateTrainingSuggestions(datasetId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/training-suggestions/${datasetId}`);
  return data;
}

export async function generateModelAnalysis(modelId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/model-analysis/${modelId}`);
  return data;
}

export async function generatePredictionExplanation(predictionJobId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/prediction-explanation/${predictionJobId}`);
  return data;
}

export async function runPrivacyScan(datasetId: number) {
  const { data } = await request.post<PrivacyScanResult>(`/ai/privacy-scan/${datasetId}`);
  return data;
}

export async function getPrivacyScan(datasetId: number) {
  const { data } = await request.get<PrivacyScanResult>(`/ai/privacy-scan/${datasetId}`);
  return data;
}

export async function generateFieldAnalysis(datasetId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/field-analysis/${datasetId}`);
  return data;
}

export async function getFieldRecommendations(datasetId: number) {
  const { data } = await request.get<import("../types/ai").FieldRecommendation[]>(
    `/ai/field-analysis/${datasetId}/recommendations`,
  );
  return data;
}

export async function confirmFieldRecommendations(
  datasetId: number,
  confirmations: import("../types/ai").FieldConfirmationItem[],
) {
  const { data } = await request.post<{ updated_fields: number }>(
    `/datasets/${datasetId}/feature-config/confirm`,
    { confirmations },
  );
  return data;
}

export async function generateTrainingConfigSuggestion(datasetId: number) {
  const { data } = await request.post<AIAnalysisReport>(
    `/ai/training-config-suggestion/${datasetId}`,
  );
  return data;
}

export async function generateBatchPredictionAnalysis(jobId: number) {
  const { data } = await request.post<AIAnalysisReport>(
    `/ai/batch-prediction-analysis/${jobId}`,
  );
  return data;
}

export async function generateOpnsPairingAnalysis(modelId: number) {
  const { data } = await request.post<AIAnalysisReport>(
    `/ai/opns-pairing-analysis/${modelId}`,
  );
  return data;
}

export async function generateChartInterpretation(
  chartType: string,
  chartTitle: string,
  chartData: Record<string, unknown>,
  context?: Record<string, unknown>,
) {
  const { data } = await request.post<AIAnalysisReport>("/ai/chart-interpretation", {
    chart_type: chartType,
    chart_title: chartTitle,
    chart_data: chartData,
    context: context ?? {},
  });
  return data;
}

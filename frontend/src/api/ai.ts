import { request } from "./request";
import type { AIAnalysisReport } from "../types/ai";


export async function generateDatasetAnalysis(datasetId: number) {
  const { data } = await request.post<AIAnalysisReport>(`/ai/dataset-analysis/${datasetId}`);
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

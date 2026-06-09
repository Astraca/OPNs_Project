import { request } from "./request";
import type {
  ClassificationMetricsResponse,
  ConfusionMatrixData,
  MLModel,
  ModelMetric,
  ModelTrainPayload,
  PredictedVsActualData,
  RegressionMetricsResponse,
  RegressionTrainPayload,
  ResidualsData,
  RocCurveData,
} from "../types/model";


export async function trainModel(payload: ModelTrainPayload) {
  const { data } = await request.post<MLModel>("/models/train", payload);
  return data;
}

export async function trainRegressionModel(payload: RegressionTrainPayload) {
  const { data } = await request.post<MLModel>("/models/train/regression", payload);
  return data;
}

export async function listModels() {
  const { data } = await request.get<MLModel[]>("/models");
  return data;
}

export async function getModel(id: number) {
  const { data } = await request.get<MLModel>(`/models/${id}`);
  return data;
}

export async function deleteModel(id: number) {
  await request.delete(`/models/${id}`);
}

export async function getModelMetrics(id: number) {
  const { data } = await request.get<ModelMetric[]>(`/models/${id}/metrics`);
  return data;
}

// ── Evaluation ────────────────────────────────────────────────────────────────

export async function getClassificationMetrics(modelId: number) {
  const { data } = await request.get<ClassificationMetricsResponse>(`/evaluation/classification/${modelId}`);
  return data;
}

export async function getConfusionMatrices(modelId: number) {
  const { data } = await request.get<ConfusionMatrixData[]>(`/evaluation/confusion-matrix/${modelId}`);
  return data;
}

export async function getRocCurves(modelId: number) {
  const { data } = await request.get<RocCurveData[]>(`/evaluation/roc/${modelId}`);
  return data;
}

export async function getRegressionMetrics(modelId: number) {
  const { data } = await request.get<RegressionMetricsResponse>(`/evaluation/regression/${modelId}`);
  return data;
}

export async function getPredictedVsActual(modelId: number) {
  const { data } = await request.get<PredictedVsActualData>(`/evaluation/predicted-vs-actual/${modelId}`);
  return data;
}

export async function getResiduals(modelId: number) {
  const { data } = await request.get<ResidualsData>(`/evaluation/residuals/${modelId}`);
  return data;
}

import { request } from "./request";
import type { MLModel, ModelMetric, ModelTrainPayload } from "../types/model";


export async function trainModel(payload: ModelTrainPayload) {
  const { data } = await request.post<MLModel>("/models/train", payload);
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

export async function getModelMetrics(id: number) {
  const { data } = await request.get<ModelMetric[]>(`/models/${id}/metrics`);
  return data;
}

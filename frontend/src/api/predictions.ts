import { request } from "./request";
import type { BatchPredictionResponse, PredictionJob, SinglePredictionPayload, SinglePredictionResponse } from "../types/prediction";


export async function predictSingleIgan(payload: SinglePredictionPayload) {
  const { data } = await request.post<SinglePredictionResponse>("/predictions/igan/single", payload);
  return data;
}

export async function runBatchPrediction(modelId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request.post<BatchPredictionResponse>(`/predictions/batch/run/${modelId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listPredictionJobs() {
  const { data } = await request.get<PredictionJob[]>("/predictions/history");
  return data;
}

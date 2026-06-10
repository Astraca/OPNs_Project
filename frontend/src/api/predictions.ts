import { request } from "./request";
import type {
  BatchPredictionResponse,
  PredictionJob,
  RegressionSinglePredictionResponse,
  SinglePredictionPayload,
  SinglePredictionResponse,
} from "../types/prediction";


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

export async function predictSingleRegression(payload: SinglePredictionPayload) {
  const { data } = await request.post<RegressionSinglePredictionResponse>(
    "/predictions/regression/single",
    payload,
  );
  return data;
}

export async function runBatchRegressionPrediction(modelId: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request.post<BatchPredictionResponse>(
    `/predictions/regression/batch/${modelId}`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

export async function listPredictionJobs() {
  const { data } = await request.get<PredictionJob[]>("/predictions/history");
  return data;
}

export async function getPredictionDetail(jobId: number) {
  const { data } = await request.get<Record<string, unknown>>(`/predictions/${jobId}`);
  return data;
}

export async function deletePrediction(jobId: number) {
  await request.delete(`/predictions/${jobId}`);
}

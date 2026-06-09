import { request } from "./request";
import type {
  Dataset,
  DatasetColumn,
  DatasetCreatePayload,
  DatasetPreview,
  DatasetProfile,
} from "../types/dataset";


export async function createDataset(payload: DatasetCreatePayload) {
  const { data } = await request.post<Dataset>("/datasets", payload);
  return data;
}

export async function listDatasets() {
  const { data } = await request.get<Dataset[]>("/datasets");
  return data;
}

export async function getDataset(id: number) {
  const { data } = await request.get<Dataset>(`/datasets/${id}`);
  return data;
}

export async function deleteDataset(id: number) {
  await request.delete(`/datasets/${id}`);
}

export async function uploadDatasetFile(id: number, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await request.post<Dataset>(`/datasets/${id}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getDatasetPreview(id: number) {
  const { data } = await request.get<DatasetPreview>(`/datasets/${id}/preview`);
  return data;
}

export async function getDatasetColumns(id: number) {
  const { data } = await request.get<DatasetColumn[]>(`/datasets/${id}/columns`);
  return data;
}

export async function getDatasetProfile(id: number) {
  const { data } = await request.get<DatasetProfile>(`/datasets/${id}/profile`);
  return data;
}

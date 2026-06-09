import { request } from "./request";
import type {
  Dataset,
  DatasetColumn,
  DatasetColumnRoleUpdate,
  DatasetCreatePayload,
  DatasetPreview,
  DatasetProfile,
  CorrelationMatrixData,
  LabelDistributionData,
  MissingValuesChartData,
  NumericStatisticsData,
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

export async function updateDatasetColumnRoles(id: number, columns: DatasetColumnRoleUpdate[]) {
  const { data } = await request.put<DatasetColumn[]>(`/datasets/${id}/columns/roles`, { columns });
  return data;
}

export async function getDatasetProfile(id: number) {
  const { data } = await request.get<DatasetProfile>(`/datasets/${id}/profile`);
  return data;
}

export async function getMissingValuesChart(id: number) {
  const { data } = await request.get<MissingValuesChartData>(`/datasets/${id}/charts/missing-values`);
  return data;
}

export async function getLabelDistributionChart(id: number) {
  const { data } = await request.get<LabelDistributionData>(`/datasets/${id}/charts/label-distribution`);
  return data;
}

export async function getNumericStatisticsChart(id: number) {
  const { data } = await request.get<NumericStatisticsData>(`/datasets/${id}/charts/numeric-statistics`);
  return data;
}

export async function getCorrelationMatrixChart(id: number) {
  const { data } = await request.get<CorrelationMatrixData>(`/datasets/${id}/charts/correlation`);
  return data;
}

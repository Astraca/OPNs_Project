import { request } from "./request";
import type { Report } from "../types/report";


export async function generateReport(modelId: number, title?: string) {
  const { data } = await request.post<Report>(`/reports/generate/${modelId}`, title ? { title } : {});
  return data;
}

export async function listReports() {
  const { data } = await request.get<Report[]>("/reports");
  return data;
}

export async function getReport(id: number) {
  const { data } = await request.get<Report>(`/reports/${id}`);
  return data;
}

export async function deleteReport(id: number) {
  await request.delete(`/reports/${id}`);
}

import { apiBaseUrl, http } from "./http";
import type {
  AnalysisFilters,
  AnalysisItem,
  Detection,
  ReportReviewPayload,
} from "../types/analysis";

export async function listImages(filters?: Partial<AnalysisFilters>) {
  const params = Object.fromEntries(
    Object.entries(filters ?? {}).filter(
      ([, value]) => value !== "" && value !== undefined && value !== null,
    ),
  );
  const response = await http.get<{ code: number; data: AnalysisItem[] }>(
    "/api/v1/images",
    {
      params,
    },
  );
  return response.data.data;
}

export async function getAnalysis(imageId: string) {
  const response = await http.get<{ code: number; data: AnalysisItem }>(
    `/api/v1/analysis/${imageId}`,
  );
  return response.data.data;
}

export async function uploadImage(payload: {
  file: File;
  patientId: string;
  imageType: AnalysisItem["image_type"];
}) {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("patient_id", payload.patientId);
  formData.append("image_type", payload.imageType);

  const response = await http.post<{
    code: number;
    data: { image_id: string; status: string; message: string };
  }>("/api/v1/images/upload", formData);
  return response.data.data;
}

export async function reviewReport(
  reportId: string,
  payload: ReportReviewPayload,
) {
  const response = await http.put<{
    code: number;
    data: {
      report_id: string;
      status: string;
      doctor_review: string;
      detections: Detection[];
    };
  }>(`/api/v1/reports/${reportId}/review`, payload);
  return response.data.data;
}

export function createAnalysisSocket(imageId: string, accessToken: string) {
  const suffix = `?access_token=${encodeURIComponent(accessToken)}`;
  if (apiBaseUrl.startsWith("http://") || apiBaseUrl.startsWith("https://")) {
    const wsBase = apiBaseUrl.replace(/^http/, "ws");
    return new WebSocket(`${wsBase}/ws/analysis/${imageId}${suffix}`);
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return new WebSocket(
    `${protocol}//${window.location.host}/ws/analysis/${imageId}${suffix}`,
  );
}

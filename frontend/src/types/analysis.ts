export interface Detection {
  bbox: number[];
  class: string;
  confidence: number;
  severity: string;
  tooth_id: string;
}

export type ReportStatus =
  | "processing"
  | "ai_generated"
  | "doctor_reviewed"
  | "finalized";

export interface Report {
  report_id: string;
  content: string;
  doctor_review: string | null;
  status: ReportStatus;
}

export interface AnalysisItem {
  image_id: string;
  patient_id: string;
  image_type: "panoramic" | "periapical" | "cbct";
  filename: string;
  file_path: string;
  image_url: string;
  status: string;
  detections: Detection[];
  segmentation_url: string | null;
  report: Report;
  created_at: string;
  updated_at: string;
}

export interface AnalysisFilters {
  patient_id: string;
  image_type: "" | AnalysisItem["image_type"];
  report_status: "" | ReportStatus;
}

export interface ReportReviewPayload {
  doctor_review: string;
  modified_findings: Detection[];
  status: Extract<ReportStatus, "doctor_reviewed" | "finalized">;
}

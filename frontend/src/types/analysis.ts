export interface Detection {
  bbox: number[];
  class: string;
  confidence: number;
  severity: string;
  tooth_id: string;
  tooth_display_name?: string;
  tooth_confidence_source?: "model_mapped" | "layout_inferred" | "unknown";
  finding_label?: string;
  clinical_meaning?: string;
  risk_hint?: string;
  recommendation?: string;
  evidence_summary?: string;
  follow_up_exam?: string[];
}

export type ReportStatus =
  | "processing"
  | "ai_generated"
  | "doctor_reviewed"
  | "finalized";

export interface ToothGroupedFinding {
  finding_label: string;
  severity: string;
  confidence: number;
  clinical_meaning: string;
  risk_hint: string;
  recommendation: string;
  evidence_summary: string;
  follow_up_exam: string[];
}

export interface ToothFindingGroup {
  tooth_id: string;
  display_name: string;
  source: "model_mapped" | "layout_inferred" | "unknown";
  findings: ToothGroupedFinding[];
}

export interface StructuredReport {
  summary: string;
  key_findings: string[];
  doctor_notes: string;
  follow_up_plan: string[];
  high_priority_findings: string[];
  tooth_findings: ToothFindingGroup[];
}

export interface Report {
  report_id: string;
  content: string;
  structured_content: StructuredReport;
  doctor_review: string | null;
  status: ReportStatus;
  pdf_url: string | null;
  pdf_variant: string | null;
  pdf_generated_at: string | null;
}

export interface AnalysisItem {
  image_id: string;
  patient_id: string;
  patient: {
    patient_id: string;
    name: string;
    gender: string | null;
    age: number | null;
    phone: string | null;
  } | null;
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

export interface PaginationMeta {
  limit: number;
  offset: number;
  total: number;
}

export interface ReportReviewPayload {
  doctor_review: string;
  modified_findings: Detection[];
  status: Extract<ReportStatus, "doctor_reviewed" | "finalized">;
}

export interface ReportRevision {
  revision_id: string;
  report_id: string;
  image_id: string;
  version_no: number;
  status: ReportStatus;
  content: string;
  structured_content: StructuredReport;
  doctor_review: string | null;
  detections: Detection[];
  pdf_url: string | null;
  pdf_variant: string | null;
  pdf_generated_at: string | null;
  actor_sub: string;
  actor_roles: string[];
  created_at: string;
}

export interface DashboardSummary {
  total_images: number;
  total_patients: number;
  recent_patients: number;
  pending_review_cases: number;
  dataset_count: number;
  open_dataset_count: number;
  covered_disease_count: number;
  processing_images: number;
  completed_images: number;
  detection_count: number;
  average_confidence: number;
  report_status_counts: Record<ReportStatus, number>;
  image_type_counts: Record<AnalysisItem["image_type"], number>;
  audit_event_count: number;
  latest_case: AnalysisItem | null;
}

export interface PaginatedAnalysisResult {
  items: AnalysisItem[];
  meta: PaginationMeta;
}

export interface PaginatedReportRevisionsResult {
  items: ReportRevision[];
  meta: PaginationMeta;
}

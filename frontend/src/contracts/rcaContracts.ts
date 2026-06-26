export type RcaMemory = {
  rca_id: string;
  document_id: string;
  title: string;
  service_name: string;
  severity: string;
  symptoms: string[];
  root_cause: string;
  resolution: string;
  prevention_items: string[];
  related_errors: string[];
  related_dependencies: string[];
  incident_date: string;
  source: string | null;
  tags: string[];
  archived: boolean;
  metadata: Record<string, unknown>;
  helpful_count: number;
  not_helpful_count: number;
  created_at: string;
  updated_at: string;
};

export type RcaMemoryMatch = {
  rca_id: string;
  document_id: string;
  title: string;
  service_name: string;
  severity: string;
  score: number;
  match_explanation: string;
  matched_signals: string[];
  symptoms: string[];
  root_cause: string;
  resolution: string;
  prevention_items: string[];
  related_errors: string[];
  related_dependencies: string[];
  incident_date: string;
  source: string | null;
  helpful_count: number;
  not_helpful_count: number;
  metadata: Record<string, unknown>;
};

export type RcaFeedback = {
  feedback_id: string;
  rca_id: string;
  incident_id: string;
  analysis_run_id: string | null;
  helpful: boolean;
  note: string | null;
  created_at: string;
};

export type RcaMemorySearchPayload = {
  service_name: string;
  severity: string;
  symptom: string;
  metric_name?: string | null;
  metric_value?: string | null;
  threshold_value?: string | null;
  top_k?: number;
  tags?: string[] | null;
};

export type RcaFeedbackPayload = {
  incident_id: string;
  rca_id: string;
  helpful: boolean;
  analysis_run_id?: string | null;
  note?: string | null;
};

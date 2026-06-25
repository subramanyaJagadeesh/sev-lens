export type ContractField = {
  field_name: string;
  field_type: string;
  required: boolean;
  description: string;
};

export type ContractRecord = {
  code: string;
  sort_order: number;
  is_terminal?: boolean;
  category?: string;
};

export type ContractRegistry = {
  incident_statuses: ContractRecord[];
  incident_event_types: ContractRecord[];
  decision_types: ContractRecord[];
  incident_scenarios: ScenarioRecord[];
  recommendation_schema_fields: ContractField[];
};

export type ScenarioRecord = {
  scenario_id: string;
  label: string;
  service_name: string;
  severity: string;
  is_default: boolean;
  description: string;
  scenario_path: string;
  expected_evidence_signals?: string[];
  expected_recommendation_direction?: string;
};

export type IncidentSummary = {
  incident_id: string;
  service_name: string;
  severity: string;
  symptom: string;
  metric_name?: string | null;
  metric_value?: string | null;
  threshold_value?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  recommendation_status: string;
  approval_status: string | null;
};

export type IncidentEvent = {
  event_id: string;
  incident_id: string;
  event_type: string;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
  sequence: number;
};

export type Recommendation = {
  summary: string;
  evidence: string[];
  recommended_actions: string[];
  confidence: string;
  requires_human_approval: boolean;
  raw_model_output?: Record<string, unknown> | null;
  created_at?: string;
};

export type IncidentDecision = {
  decision_id: string;
  incident_id: string;
  decision: string;
  decided_by: string;
  note: string | null;
  created_at: string;
};

export type IncidentAnalysisRun = {
  analysis_run_id: string;
  incident_id: string;
  scenario_id: string;
  scenario_type: string;
  trigger_type: string;
  status: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  analysis_latency_ms: number | null;
  retrieved_document_count: number;
  expected_document_hit_rate: number;
  evidence_count: number;
  recommended_action_count: number;
  confidence_value: string | null;
  human_decision_outcome: string | null;
  expected_evidence_signals: string[];
  expected_recommendation_direction: string;
  recommendation?: Recommendation | null;
  analysis_events?: IncidentEvent[];
};

export type IncidentDetail = {
  incident: IncidentSummary;
  events: IncidentEvent[];
  recommendation: Recommendation | null;
  decision: IncidentDecision | null;
  analysis_run: IncidentAnalysisRun | null;
  analysis_runs: IncidentAnalysisRun[];
};

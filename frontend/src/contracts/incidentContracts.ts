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
  recommendation_schema_fields: ContractField[];
};

export type IncidentSummary = {
  incident_id: string;
  service_name: string;
  severity: string;
  symptom: string;
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

export type IncidentDetail = {
  incident: IncidentSummary;
  events: IncidentEvent[];
  recommendation: Recommendation | null;
  decision: IncidentDecision | null;
};


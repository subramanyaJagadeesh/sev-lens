import type { IncidentDetail } from "./incidentContracts";

export type EventRecord = {
  event_id: string;
  incident_id: string;
  service_name: string;
  severity: string;
  symptom: string;
  incident_status: string;
  recommendation_status: string;
  approval_status: string | null;
  event_type: string;
  message: string;
  payload: Record<string, unknown> | null;
  created_at: string;
  sequence: number;
};

export function buildEventRecords(details: IncidentDetail[]): EventRecord[] {
  return details.flatMap((detail) =>
    detail.events.map((event) => ({
      event_id: event.event_id,
      incident_id: detail.incident.incident_id,
      service_name: detail.incident.service_name,
      severity: detail.incident.severity,
      symptom: detail.incident.symptom,
      incident_status: detail.incident.status,
      recommendation_status: detail.incident.recommendation_status,
      approval_status: detail.incident.approval_status,
      event_type: event.event_type,
      message: event.message,
      payload: event.payload,
      created_at: event.created_at,
      sequence: event.sequence,
    })),
  );
}

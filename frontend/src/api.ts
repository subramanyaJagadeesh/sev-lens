import type {
  ContractRegistry,
  IncidentDecision,
  IncidentDetail,
  IncidentSummary,
  Recommendation,
} from "./contracts/incidentContracts";

const INCIDENT_API_BASE_URL = import.meta.env.VITE_INCIDENT_API_BASE_URL ?? "http://localhost:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${INCIDENT_API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchContracts(): Promise<ContractRegistry> {
  return requestJson<ContractRegistry>("/api/contracts");
}

export function listIncidents(): Promise<IncidentSummary[]> {
  return requestJson<IncidentSummary[]>("/api/incidents");
}

export async function listIncidentDetails(): Promise<IncidentDetail[]> {
  const incidents = await listIncidents();
  return Promise.all(incidents.map((incident) => getIncident(incident.incident_id)));
}

export function getIncident(incidentId: string): Promise<IncidentDetail> {
  return requestJson<IncidentDetail>(`/api/incidents/${incidentId}`);
}

export function triggerMockIncident(scenario: string): Promise<IncidentSummary> {
  return requestJson<IncidentSummary>("/api/incidents/mock", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export function postDecision(
  incidentId: string,
  decision: "APPROVE" | "REJECT" | "ESCALATE",
  note: string,
): Promise<IncidentDecision> {
  return requestJson<IncidentDecision>(`/api/incidents/${incidentId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, note }),
  });
}

export function retryIncidentAnalysis(incidentId: string): Promise<IncidentSummary> {
  return requestJson<IncidentSummary>(`/api/incidents/${incidentId}/analysis/retry`, {
    method: "POST",
  });
}

export function subscribeToIncidentStream(
  incidentId: string,
  onEvent: (event: IncidentEventSourcePayload) => void,
): () => void {
  const source = new EventSource(`${INCIDENT_API_BASE_URL}/api/incidents/${incidentId}/stream`);
  source.addEventListener("incident-event", (event) => {
    const payload = JSON.parse((event as MessageEvent).data) as IncidentEventSourcePayload;
    onEvent(payload);
  });
  source.onerror = () => source.close();
  return () => source.close();
}

export type IncidentEventSourcePayload = {
  incident_id: string;
  event_type: string;
  message: string;
  created_at: string;
  sequence: number;
  payload: Record<string, unknown> | null;
};

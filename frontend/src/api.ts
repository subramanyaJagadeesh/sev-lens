import type {
  ContractRegistry,
  IncidentDecision,
  IncidentDetail,
  IncidentSummary,
} from "./contracts/incidentContracts";
import type {
  KnowledgeDocument,
  KnowledgeDocumentCreatePayload,
  KnowledgeDocumentDetail,
  KnowledgeDocumentUpdatePayload,
  KnowledgeSearchPayload,
  KnowledgeSearchResult,
} from "./contracts/knowledgeContracts";
import type {
  RcaFeedback,
  RcaFeedbackPayload,
  RcaMemory,
  RcaMemoryMatch,
  RcaMemorySearchPayload,
} from "./contracts/rcaContracts";

const INCIDENT_API_BASE_URL = import.meta.env.VITE_INCIDENT_API_BASE_URL ?? "http://localhost:8000";
const RAG_API_BASE_URL = import.meta.env.VITE_RAG_API_BASE_URL ?? "http://localhost:8001";

async function requestJson<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
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
  return requestJson<ContractRegistry>(INCIDENT_API_BASE_URL, "/api/contracts");
}

export function listIncidents(): Promise<IncidentSummary[]> {
  return requestJson<IncidentSummary[]>(INCIDENT_API_BASE_URL, "/api/incidents");
}

export async function listIncidentDetails(): Promise<IncidentDetail[]> {
  const incidents = await listIncidents();
  return Promise.all(incidents.map((incident) => getIncident(incident.incident_id)));
}

export function getIncident(incidentId: string): Promise<IncidentDetail> {
  return requestJson<IncidentDetail>(INCIDENT_API_BASE_URL, `/api/incidents/${incidentId}`);
}

export function triggerMockIncident(scenario: string): Promise<IncidentSummary> {
  return requestJson<IncidentSummary>(INCIDENT_API_BASE_URL, "/api/incidents/mock", {
    method: "POST",
    body: JSON.stringify({ scenario }),
  });
}

export function postDecision(
  incidentId: string,
  decision: "APPROVE" | "REJECT" | "ESCALATE",
  note: string,
): Promise<IncidentDecision> {
  return requestJson<IncidentDecision>(INCIDENT_API_BASE_URL, `/api/incidents/${incidentId}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision, note }),
  });
}

export function retryIncidentAnalysis(incidentId: string): Promise<IncidentSummary> {
  return requestJson<IncidentSummary>(INCIDENT_API_BASE_URL, `/api/incidents/${incidentId}/analysis/retry`, {
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

export function listKnowledgeDocuments(includeArchived = false): Promise<KnowledgeDocument[]> {
  const query = includeArchived ? "?include_archived=true" : "";
  return requestJson<KnowledgeDocument[]>(RAG_API_BASE_URL, `/knowledge/documents${query}`);
}

export function getKnowledgeDocument(documentId: string): Promise<KnowledgeDocumentDetail> {
  return requestJson<KnowledgeDocumentDetail>(RAG_API_BASE_URL, `/knowledge/documents/${encodeURIComponent(documentId)}`);
}

export function createKnowledgeDocument(
  payload: KnowledgeDocumentCreatePayload,
): Promise<KnowledgeDocument> {
  return requestJson<KnowledgeDocument>(RAG_API_BASE_URL, "/knowledge/documents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateKnowledgeDocument(
  documentId: string,
  payload: KnowledgeDocumentUpdatePayload,
): Promise<KnowledgeDocument> {
  return requestJson<KnowledgeDocument>(RAG_API_BASE_URL, `/knowledge/documents/${encodeURIComponent(documentId)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function archiveKnowledgeDocument(documentId: string): Promise<KnowledgeDocument> {
  return requestJson<KnowledgeDocument>(
    RAG_API_BASE_URL,
    `/knowledge/documents/${encodeURIComponent(documentId)}/archive`,
    {
      method: "POST",
    },
  );
}

export function reindexKnowledgeDocument(documentId: string): Promise<KnowledgeDocumentDetail> {
  return requestJson<KnowledgeDocumentDetail>(
    RAG_API_BASE_URL,
    `/knowledge/documents/${encodeURIComponent(documentId)}/reindex`,
    {
      method: "POST",
    },
  );
}

export function searchKnowledge(payload: KnowledgeSearchPayload): Promise<KnowledgeSearchResult[]> {
  return requestJson<KnowledgeSearchResult[]>(RAG_API_BASE_URL, "/knowledge/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listRcaMemories(includeArchived = false): Promise<RcaMemory[]> {
  const query = includeArchived ? "?include_archived=true" : "";
  return requestJson<RcaMemory[]>(RAG_API_BASE_URL, `/rca-memory${query}`);
}

export function getRcaMemory(rcaId: string): Promise<{ memory: RcaMemory; feedback: RcaFeedback[] }> {
  return requestJson<{ memory: RcaMemory; feedback: RcaFeedback[] }>(
    RAG_API_BASE_URL,
    `/rca-memory/${encodeURIComponent(rcaId)}`,
  );
}

export function searchRcaMemories(payload: RcaMemorySearchPayload): Promise<RcaMemoryMatch[]> {
  return requestJson<RcaMemoryMatch[]>(RAG_API_BASE_URL, "/rca-memory/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listRcaFeedback(params: {
  incidentId?: string;
  analysisRunId?: string;
  rcaId?: string;
}): Promise<RcaFeedback[]> {
  const searchParams = new URLSearchParams();
  if (params.incidentId) searchParams.set("incident_id", params.incidentId);
  if (params.analysisRunId) searchParams.set("analysis_run_id", params.analysisRunId);
  if (params.rcaId) searchParams.set("rca_id", params.rcaId);
  const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return requestJson<RcaFeedback[]>(RAG_API_BASE_URL, `/rca-memory/feedback${suffix}`);
}

export function recordRcaFeedback(payload: RcaFeedbackPayload): Promise<RcaFeedback> {
  return requestJson<RcaFeedback>(RAG_API_BASE_URL, "/rca-memory/feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

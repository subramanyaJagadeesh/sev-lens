import type { IncidentDetail } from "../contracts/incidentContracts";

export function sortByCreatedAtDesc(left: { created_at: string }, right: { created_at: string }) {
  return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
}

export function getLastEventSequence(detail: IncidentDetail | null | undefined): number | null {
  if (!detail || detail.events.length === 0) {
    return null;
  }
  return detail.events[detail.events.length - 1]?.sequence ?? null;
}

const statusLabelMap: Record<string, string> = {
  QUEUED: "Queued",
  ANALYZING: "Analyzing",
  RECOMMENDATION_READY: "Recommendation ready",
  READY: "Ready",
  FAILED: "Failed",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  ESCALATED: "Escalated",
  PENDING: "Pending",
  LIVE: "Live",
  PAUSED: "Paused",
  FINISHED: "Finished",
};

export function formatStatusLabel(value: string | null | undefined, fallback = "—"): string {
  if (!value) {
    return fallback;
  }
  return statusLabelMap[value] ?? value.replaceAll("_", " ").toLowerCase().replace(/(^|\s)\S/g, (char) => char.toUpperCase());
}

export function formatDecisionLabel(value: string | null | undefined): string {
  if (!value) {
    return "Decision pending";
  }
  return formatStatusLabel(value);
}

export function formatConfidenceLabel(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  return value.replaceAll("_", " ").toLowerCase().replace(/(^|\s)\S/g, (char) => char.toUpperCase());
}

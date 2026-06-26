import type { IncidentAnalysisRun, IncidentEvent, Recommendation } from "../contracts/incidentContracts";

export function getDefaultAnalysisRunId(runs: IncidentAnalysisRun[]) {
  if (!runs.length) {
    return null;
  }
  const latestRun = runs[runs.length - 1];
  if (latestRun.status === "QUEUED" || latestRun.status === "ANALYZING") {
    return latestRun.analysis_run_id;
  }
  const completedRun = [...runs]
    .reverse()
    .find((run) => run.completed_at || run.status === "RECOMMENDATION_READY" || run.status === "FAILED");
  return completedRun?.analysis_run_id ?? latestRun.analysis_run_id;
}

export function getSelectedAnalysisRun(runs: IncidentAnalysisRun[], selectedRunId: string | null | undefined) {
  if (!runs.length) {
    return null;
  }
  if (!selectedRunId) {
    return runs[runs.length - 1];
  }
  return runs.find((run) => run.analysis_run_id === selectedRunId) ?? runs[runs.length - 1];
}

export function getRunRecommendation(run: IncidentAnalysisRun | null | undefined, fallback: Recommendation | null) {
  return run?.recommendation ?? fallback;
}

export function getRunEvents(run: IncidentAnalysisRun | null | undefined, fallbackEvents: IncidentEvent[]) {
  if (!run) {
    return fallbackEvents;
  }
  return run.analysis_events ?? [];
}

export function getRawModelOutput(run: IncidentAnalysisRun | null | undefined) {
  return run?.recommendation?.raw_model_output ?? null;
}

export function getOperationalContext(run: IncidentAnalysisRun | null | undefined) {
  const raw = getRawModelOutput(run);
  if (!raw || typeof raw !== "object") {
    return null;
  }
  const context = (raw as Record<string, unknown>).operational_context;
  return context && typeof context === "object" ? (context as Record<string, unknown>) : null;
}

export function getRcaMatches(run: IncidentAnalysisRun | null | undefined) {
  const context = getOperationalContext(run);
  if (!context) {
    return [];
  }
  const matches = context.rca_matches;
  return Array.isArray(matches) ? (matches as Array<Record<string, unknown>>) : [];
}

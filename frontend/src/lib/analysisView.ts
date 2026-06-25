import type { IncidentAnalysisRun, IncidentEvent, Recommendation } from "../contracts/incidentContracts";

export function getDefaultAnalysisRunId(runs: IncidentAnalysisRun[]) {
  if (!runs.length) {
    return null;
  }
  const completedRun = runs.find((run) => run.completed_at || run.status === "RECOMMENDATION_READY" || run.status === "FAILED");
  return completedRun?.analysis_run_id ?? runs[0].analysis_run_id;
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
  return run?.analysis_events?.length ? run.analysis_events : fallbackEvents;
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

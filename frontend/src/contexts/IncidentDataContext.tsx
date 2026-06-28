import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  getIncident,
  listIncidentDetails,
  postDecision,
  retryIncidentAnalysis,
  triggerMockIncident,
} from "../api";
import type { IncidentDetail, IncidentEvent, IncidentSummary } from "../contracts/incidentContracts";
import { sortByCreatedAtDesc } from "../lib/incidentHelpers";

type IncidentDataContextValue = {
  incidents: IncidentSummary[];
  incidentDetailsById: Record<string, IncidentDetail>;
  isLoading: boolean;
  error: string | null;
  refreshIncidents: (preferredIncidentId?: string) => Promise<void>;
  triggerIncident: (scenarioId: string) => Promise<IncidentSummary>;
  submitDecision: (incidentId: string, decision: "APPROVE" | "REJECT" | "ESCALATE") => Promise<void>;
  retryAnalysis: (incidentId: string) => Promise<void>;
  mergeStreamEvent: (event: IncidentEvent) => void;
  getIncidentDetail: (incidentId: string | null | undefined) => IncidentDetail | null;
  getIncidentSummary: (incidentId: string | null | undefined) => IncidentSummary | null;
  setError: (error: string | null) => void;
};

const IncidentDataContext = createContext<IncidentDataContextValue | null>(null);

export function IncidentDataProvider({ children }: { children: ReactNode }) {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [incidentDetailsById, setIncidentDetailsById] = useState<Record<string, IncidentDetail>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshIncidents = useCallback(async (preferredIncidentId?: string) => {
    if (preferredIncidentId) {
      const nextDetail = await getIncident(preferredIncidentId);
      setIncidentDetailsById((current) => ({
        ...current,
        [preferredIncidentId]: nextDetail,
      }));
      setIncidents((current) => {
        const nextSummary = nextDetail.incident;
        const nextIncidents = current.some((incident) => incident.incident_id === preferredIncidentId)
          ? current.map((incident) => (incident.incident_id === preferredIncidentId ? nextSummary : incident))
          : [...current, nextSummary];
        return [...nextIncidents].sort(sortByCreatedAtDesc);
      });
      setError(null);
      return;
    }

    const nextDetails = await listIncidentDetails();
    const nextIncidents = nextDetails.map((detail) => detail.incident);
    const nextIncidentDetailsById = Object.fromEntries(
      nextDetails.map((detail) => [detail.incident.incident_id, detail]),
    ) as Record<string, IncidentDetail>;

    setIncidents(nextIncidents);
    setIncidentDetailsById(nextIncidentDetailsById);
    setError(null);

    if (preferredIncidentId && !nextIncidentDetailsById[preferredIncidentId]) {
      return;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        await refreshIncidents();
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load incidents");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [refreshIncidents]);

  const triggerIncident = useCallback(async (scenarioId: string) => {
    const created = await triggerMockIncident(scenarioId);
    await refreshIncidents(created.incident_id);
    return created;
  }, [refreshIncidents]);

  const submitDecision = useCallback(
    async (incidentId: string, decision: "APPROVE" | "REJECT" | "ESCALATE") => {
      await postDecision(incidentId, decision, "demo-user approved from dashboard");
      await refreshIncidents(incidentId);
    },
    [refreshIncidents],
  );

  const retryAnalysis = useCallback(
    async (incidentId: string) => {
      await retryIncidentAnalysis(incidentId);
      await refreshIncidents(incidentId);
    },
    [refreshIncidents],
  );

  const mergeStreamEvent = useCallback((nextEvent: IncidentEvent) => {
    const analysisRunId =
      nextEvent.payload && typeof nextEvent.payload === "object" && typeof nextEvent.payload.analysis_run_id === "string"
        ? nextEvent.payload.analysis_run_id
        : null;

    setIncidentDetailsById((current) => {
      const detail = current[nextEvent.incident_id];
      if (!detail) {
        return current;
      }
      const nextEvents = [...detail.events.filter((item) => item.sequence !== nextEvent.sequence), nextEvent].sort(
        (left, right) => left.sequence - right.sequence,
      );
      const nextAnalysisRuns = analysisRunId
        ? detail.analysis_runs.map((run) => {
            if (run.analysis_run_id !== analysisRunId) {
              return run;
            }
            const nextRunEvents = [...(run.analysis_events ?? []).filter((item) => item.sequence !== nextEvent.sequence), nextEvent].sort(
              (left, right) => left.sequence - right.sequence,
            );
            return {
              ...run,
              analysis_events: nextRunEvents,
            };
          })
        : detail.analysis_runs;
      return {
        ...current,
        [nextEvent.incident_id]: {
          ...detail,
          incident: {
            ...detail.incident,
            updated_at: nextEvent.created_at,
          },
          events: nextEvents,
          analysis_run:
            detail.analysis_run && detail.analysis_run.analysis_run_id === analysisRunId
              ? {
                  ...detail.analysis_run,
                  analysis_events: [...(detail.analysis_run.analysis_events ?? []).filter((item) => item.sequence !== nextEvent.sequence), nextEvent].sort(
                    (left, right) => left.sequence - right.sequence,
                  ),
                }
              : detail.analysis_run,
          analysis_runs: nextAnalysisRuns,
        },
      };
    });

    if (
      nextEvent.event_type === "ANALYSIS_QUEUED" ||
      nextEvent.event_type === "ANALYSIS_STARTED" ||
      nextEvent.event_type === "RECOMMENDATION_GENERATED" ||
      nextEvent.event_type === "ANALYSIS_FAILED" ||
      nextEvent.event_type === "HUMAN_APPROVED" ||
      nextEvent.event_type === "HUMAN_REJECTED" ||
      nextEvent.event_type === "HUMAN_ESCALATED"
    ) {
      void refreshIncidents(nextEvent.incident_id).catch(() => undefined);
    }

    setIncidents((current) =>
      current.map((incident) =>
        incident.incident_id === nextEvent.incident_id ? { ...incident, updated_at: nextEvent.created_at } : incident,
      ),
    );
  }, [refreshIncidents]);

  const value = useMemo<IncidentDataContextValue>(
    () => ({
      incidents,
      incidentDetailsById,
      isLoading,
      error,
      refreshIncidents,
      triggerIncident,
      submitDecision,
      retryAnalysis,
      mergeStreamEvent,
      getIncidentDetail: (incidentId) => (incidentId ? incidentDetailsById[incidentId] ?? null : null),
      getIncidentSummary: (incidentId) =>
        incidentId ? incidents.find((incident) => incident.incident_id === incidentId) ?? null : null,
      setError,
    }),
    [
      error,
      incidents,
      incidentDetailsById,
      isLoading,
      mergeStreamEvent,
      refreshIncidents,
      retryAnalysis,
      submitDecision,
      triggerIncident,
    ],
  );

  return <IncidentDataContext.Provider value={value}>{children}</IncidentDataContext.Provider>;
}

export function useIncidentData() {
  const value = useContext(IncidentDataContext);
  if (!value) {
    throw new Error("useIncidentData must be used within IncidentDataProvider");
  }
  return value;
}

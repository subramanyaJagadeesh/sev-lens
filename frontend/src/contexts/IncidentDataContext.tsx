import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  listIncidentDetails,
  postDecision,
  triggerMockIncident,
} from "../api";
import type { IncidentDetail, IncidentEvent, IncidentSummary } from "../contracts/incidentContracts";

type IncidentDataContextValue = {
  incidents: IncidentSummary[];
  incidentDetailsById: Record<string, IncidentDetail>;
  isLoading: boolean;
  error: string | null;
  refreshIncidents: (preferredIncidentId?: string) => Promise<void>;
  triggerIncident: () => Promise<IncidentSummary>;
  submitDecision: (incidentId: string, decision: "APPROVE" | "REJECT" | "ESCALATE") => Promise<void>;
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

  const triggerIncident = useCallback(async () => {
    const created = await triggerMockIncident();
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

  const mergeStreamEvent = useCallback((nextEvent: IncidentEvent) => {
    setIncidentDetailsById((current) => {
      const detail = current[nextEvent.incident_id];
      if (!detail) {
        return current;
      }
      const nextEvents = [...detail.events.filter((item) => item.sequence !== nextEvent.sequence), nextEvent].sort(
        (left, right) => left.sequence - right.sequence,
      );
      return {
        ...current,
        [nextEvent.incident_id]: {
          ...detail,
          incident: {
            ...detail.incident,
            updated_at: nextEvent.created_at,
          },
          events: nextEvents,
        },
      };
    });

    setIncidents((current) =>
      current.map((incident) =>
        incident.incident_id === nextEvent.incident_id ? { ...incident, updated_at: nextEvent.created_at } : incident,
      ),
    );
  }, []);

  const value = useMemo<IncidentDataContextValue>(
    () => ({
      incidents,
      incidentDetailsById,
      isLoading,
      error,
      refreshIncidents,
      triggerIncident,
      submitDecision,
      mergeStreamEvent,
      getIncidentDetail: (incidentId) => (incidentId ? incidentDetailsById[incidentId] ?? null : null),
      getIncidentSummary: (incidentId) =>
        incidentId ? incidents.find((incident) => incident.incident_id === incidentId) ?? null : null,
      setError,
    }),
    [error, incidents, incidentDetailsById, isLoading, mergeStreamEvent, refreshIncidents, submitDecision, triggerIncident],
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

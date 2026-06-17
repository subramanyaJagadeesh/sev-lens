import { useEffect } from "react";
import { subscribeToIncidentStream, type IncidentEventSourcePayload } from "../api";
import type { IncidentEvent } from "../contracts/incidentContracts";

export function useIncidentStream(
  incidentId: string | null,
  enabled: boolean,
  onEvent: (event: IncidentEvent) => void,
) {
  useEffect(() => {
    if (!incidentId || !enabled) {
      return;
    }
    return subscribeToIncidentStream(incidentId, (payload: IncidentEventSourcePayload) => {
      onEvent({
        event_id: `${payload.incident_id}:${payload.sequence}`,
        incident_id: payload.incident_id,
        event_type: payload.event_type,
        message: payload.message,
        payload: payload.payload,
        created_at: payload.created_at,
        sequence: payload.sequence,
      });
    });
  }, [enabled, incidentId, onEvent]);
}


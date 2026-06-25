import type { IncidentSummary } from "../contracts/incidentContracts";
import { formatStatusLabel } from "../lib/statusLabels";

type Props = {
  incidents: IncidentSummary[];
  selectedIncidentId: string | null;
  onSelectIncident: (incidentId: string) => void;
};

export function IncidentList({ incidents, selectedIncidentId, onSelectIncident }: Props) {
  return (
    <div className="space-y-3">
      {incidents.map((incident) => {
        const selected = incident.incident_id === selectedIncidentId;
        return (
          <button
            key={incident.incident_id}
            onClick={() => onSelectIncident(incident.incident_id)}
            className={`panel w-full rounded-xl p-4 text-left transition ${
              selected ? "border-[color:var(--accent)] bg-[color:var(--surface-strong)]" : "panel-hover"
            }`}
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-muted">{incident.service_name}</p>
                <h3 className="font-semibold text-strong">{incident.symptom}</h3>
              </div>
              <span className="chip-accent px-3 py-1 text-xs">{formatStatusLabel(incident.status)}</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-subtle">
              <span>{formatStatusLabel(incident.severity)}</span>
              <span>{formatStatusLabel(incident.recommendation_status)}</span>
            </div>
            {incident.status === "QUEUED" ? <p className="mt-2 text-xs text-muted">Waiting for async analysis</p> : null}
          </button>
        );
      })}
    </div>
  );
}

import type { IncidentSummary } from "../contracts/incidentContracts";
import { formatDecisionLabel, formatStatusLabel } from "../lib/statusLabels";

type Props = {
  incident: IncidentSummary;
};

export function IncidentHeader({ incident }: Props) {
  const isQueued = incident.status === "QUEUED";
  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted">{incident.service_name}</p>
          <h2 className="text-2xl font-semibold">{incident.symptom}</h2>
          {isQueued ? <p className="mt-2 text-sm text-muted">Queued for async analysis.</p> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="chip px-3 py-1 text-xs">{formatStatusLabel(incident.severity)}</span>
          <span className="chip-accent px-3 py-1 text-xs">{formatStatusLabel(incident.status)}</span>
          <span className="chip px-3 py-1 text-xs">{formatDecisionLabel(incident.approval_status)}</span>
        </div>
      </div>
      <div className="mt-4 grid gap-3 text-sm text-muted md:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Incident ID</p>
          <p className="break-all font-mono text-strong">{incident.incident_id}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Recommendation status</p>
          <p className="text-strong">{formatStatusLabel(incident.recommendation_status)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Created</p>
          <p className="text-strong">{new Date(incident.created_at).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}

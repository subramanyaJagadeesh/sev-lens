import type { IncidentSummary } from "../contracts/incidentContracts";

type Props = {
  incident: IncidentSummary;
};

export function IncidentHeader({ incident }: Props) {
  return (
    <div className="panel rounded-2xl p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted">{incident.service_name}</p>
          <h2 className="text-2xl font-semibold">{incident.symptom}</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="chip px-3 py-1 text-xs">{incident.severity}</span>
          <span className="chip-accent px-3 py-1 text-xs">{incident.status}</span>
          <span className="chip px-3 py-1 text-xs">{incident.approval_status ?? "PENDING"}</span>
        </div>
      </div>
      <div className="mt-4 grid gap-3 text-sm text-muted md:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Incident ID</p>
          <p className="font-mono text-strong">{incident.incident_id}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Recommendation status</p>
          <p className="text-strong">{incident.recommendation_status}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-subtle">Created</p>
          <p className="text-strong">{new Date(incident.created_at).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}

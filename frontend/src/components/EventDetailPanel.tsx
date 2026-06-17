import type { IncidentDetail } from "../contracts/incidentContracts";
import { Timeline } from "./Timeline";

type Props = {
  detail: IncidentDetail;
  live: boolean;
};

export function EventDetailPanel({ detail, live }: Props) {
  return (
    <div className="panel rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Incident event chain</h3>
          <p className="text-sm text-muted">Streaming from the incident SSE channel.</p>
        </div>
        <span className="chip-accent px-3 py-1 text-xs">{live ? "LIVE" : "PAUSED"}</span>
      </div>
      <Timeline events={detail.events} />
    </div>
  );
}

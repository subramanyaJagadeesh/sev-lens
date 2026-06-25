import type { IncidentDetail } from "../contracts/incidentContracts";
import { Timeline } from "./Timeline";

type Props = {
  events: IncidentDetail["events"];
  title?: string;
  description?: string;
  stateLabel: string;
};

export function EventDetailPanel({ events, title = "Incident event chain", description = "Streaming from the incident SSE channel.", stateLabel }: Props) {
  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted">{description}</p>
        </div>
        <span className="chip-accent px-3 py-1 text-xs">{stateLabel}</span>
      </div>
      <Timeline events={events} />
    </div>
  );
}

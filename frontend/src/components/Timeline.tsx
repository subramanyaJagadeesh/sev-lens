import type { IncidentEvent } from "../contracts/incidentContracts";
import { formatStatusLabel } from "../lib/statusLabels";

type Props = {
  events: IncidentEvent[];
};

export function Timeline({ events }: Props) {
  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div key={event.event_id} className="panel min-w-0 rounded-xl p-4">
          <div className="flex items-center justify-between gap-4">
            <span className="break-words text-sm font-medium text-[color:var(--accent)]">
              {formatStatusLabel(event.event_type)}
            </span>
            <span className="text-xs text-subtle">{new Date(event.created_at).toLocaleString()}</span>
          </div>
          <p className="mt-2 break-words text-sm text-strong">{event.message}</p>
        </div>
      ))}
    </div>
  );
}

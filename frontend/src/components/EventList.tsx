import type { EventRecord } from "../contracts/eventView";
import { formatStatusLabel } from "../lib/statusLabels";

type Props = {
  events: EventRecord[];
  selectedEventId: string | null;
  onSelectEvent: (event: EventRecord) => void;
};

export function EventList({ events, selectedEventId, onSelectEvent }: Props) {
  return (
    <div className="space-y-3">
      {events.map((event) => {
        const selected = event.event_id === selectedEventId;
        return (
          <button
            key={event.event_id}
            type="button"
            onClick={() => onSelectEvent(event)}
            className={`panel w-full rounded-xl p-4 text-left transition ${
              selected ? "border-[color:var(--accent)] bg-[color:var(--surface-strong)]" : "panel-hover"
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm text-muted">{event.service_name}</p>
                <h3 className="font-semibold text-strong">{event.message}</h3>
              </div>
              <span className="chip-accent px-3 py-1 text-xs">{event.event_type}</span>
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-subtle">
              <span>{formatStatusLabel(event.incident_status)}</span>
              <span>{new Date(event.created_at).toLocaleString()}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

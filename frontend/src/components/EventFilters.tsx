import { Select } from "./forms/Select";

type Props = {
  query: string;
  eventType: string;
  serviceName: string;
  eventTypes: string[];
  serviceNames: string[];
  onQueryChange: (query: string) => void;
  onEventTypeChange: (eventType: string) => void;
  onServiceNameChange: (serviceName: string) => void;
};

export function EventFilters({
  query,
  eventType,
  serviceName,
  eventTypes,
  serviceNames,
  onQueryChange,
  onEventTypeChange,
  onServiceNameChange,
}: Props) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      <label className="space-y-2 text-sm">
        <span className="text-subtle">Search</span>
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search message, service, incident, or event type"
          className="w-full rounded-xl border border-[color:var(--border)] bg-[color:var(--surface-soft)] px-4 py-2 text-strong outline-none transition placeholder:text-subtle focus:border-[color:var(--accent)]"
        />
      </label>
      <label className="space-y-2 text-sm">
        <span className="text-subtle">Event type</span>
        <Select
          value={eventType}
          onChange={onEventTypeChange}
          placeholder="All types"
          options={eventTypes.map((item) => ({ value: item, label: item }))}
        />
      </label>
      <label className="space-y-2 text-sm">
        <span className="text-subtle">Service</span>
        <Select
          value={serviceName}
          onChange={onServiceNameChange}
          placeholder="All services"
          options={serviceNames.map((item) => ({ value: item, label: item }))}
        />
      </label>
    </div>
  );
}

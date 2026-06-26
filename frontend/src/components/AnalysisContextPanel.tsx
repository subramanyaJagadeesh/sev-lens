import type { IncidentAnalysisRun } from "../contracts/incidentContracts";
import { getOperationalContext } from "../lib/analysisView";

type Props = {
  analysisRun: IncidentAnalysisRun | null;
};

function toEntries(value: unknown): Array<[string, string]> {
  if (!value || typeof value !== "object") {
    return [];
  }
  return Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, stringify(item)]);
}

function stringify(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map(stringify).join(", ");
  }
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export function AnalysisContextPanel({ analysisRun }: Props) {
  const operationalContext = getOperationalContext(analysisRun);

  const metrics = extractMetricRows(operationalContext?.metrics);
  const serviceMetadata = operationalContext ? toEntries(operationalContext.service_metadata) : [];
  const deployments = operationalContext && Array.isArray(operationalContext.deployments) ? operationalContext.deployments : [];
  const runbookCount = operationalContext && Array.isArray(operationalContext.runbook_chunks) ? operationalContext.runbook_chunks.length : 0;
  const rcaCount = operationalContext && Array.isArray(operationalContext.rca_chunks) ? operationalContext.rca_chunks.length : 0;

  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Tool context</h3>
        <p className="text-sm text-muted">How the recommendation was assembled from logs, metrics, and reference material.</p>
      </div>

      {!analysisRun?.recommendation ? (
        <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
          Tool context will appear when the selected run has a recommendation.
        </div>
      ) : (
        <div className="space-y-4">
          <section className="min-w-0 rounded-xl border border-border bg-panel-soft p-4">
            <p className="text-xs uppercase tracking-wide text-subtle">Deployments</p>
            {deployments.length ? (
              <div className="mt-3 space-y-3">
                {deployments.slice(0, 2).map((deployment) => (
                  <div key={stringify(deployment)} className="rounded-lg border border-border bg-[color:var(--surface)] p-3">
                    <p className="break-words text-sm font-medium text-strong">{stringify((deployment as Record<string, unknown>).commit ?? "Deployment")}</p>
                    <p className="mt-1 break-words text-xs text-subtle">{formatTimestamp((deployment as Record<string, unknown>).deployed_at)}</p>
                    <div className="mt-2 space-y-2">
                      <FieldLabelValue label="Changes" value={(deployment as Record<string, unknown>).changes} />
                      <FieldLabelValue label="Service" value={(deployment as Record<string, unknown>).service} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">No deployment history available.</p>
            )}

            <div className="mt-4 rounded-lg border border-dashed border-border bg-[color:var(--surface)] p-3">
              <p className="text-xs uppercase tracking-wide text-subtle">Reference docs</p>
              <div className="mt-2 space-y-2 text-sm text-muted">
                <p>{runbookCount} runbook chunk{runbookCount === 1 ? "" : "s"}</p>
                <p>{rcaCount} RCA chunk{rcaCount === 1 ? "" : "s"}</p>
              </div>
            </div>
          </section>

          <section className="min-w-0 rounded-xl border border-border bg-panel-soft p-4">
            <p className="text-xs uppercase tracking-wide text-subtle">Service metadata</p>
            <div className="mt-3 space-y-2">
              {serviceMetadata.length ? (
                serviceMetadata.map(([label, value]) => (
                  <FieldRow key={label} label={label.replace(/_/g, " ")} value={value} />
                ))
              ) : (
                <p className="text-sm text-muted">No service metadata available.</p>
              )}
            </div>
          </section>

          <section className="min-w-0 rounded-xl border border-border bg-panel-soft p-4">
            <p className="text-xs uppercase tracking-wide text-subtle">Metrics</p>
            {metrics.length ? (
              <div className="mt-3 space-y-3">
                {metrics.map((metric) => (
                  <FieldRow key={metric.label} label={metric.label} value={metric.value} />
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">No metrics snapshot available.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="min-w-0 rounded-lg border border-border bg-[color:var(--surface)] p-3">
      <p className="text-xs uppercase tracking-wide text-subtle">{label}</p>
      <p className="mt-1 break-words text-sm leading-5 text-strong">{formatFriendlyValue(value)}</p>
    </div>
  );
}

function FieldLabelValue({ label, value }: { label: string; value: unknown }) {
  const display = stringify(value);
  return (
    <div className="min-w-0 rounded-lg border border-dashed border-border bg-[color:var(--surface-soft)] p-3">
      <p className="text-xs uppercase tracking-wide text-subtle">{label}</p>
      <p className="mt-1 break-words text-sm leading-5 text-strong">{display}</p>
    </div>
  );
}

function extractMetricRows(value: unknown): Array<{ label: string; value: unknown }> {
  if (!value || typeof value !== "object") {
    return [];
  }

  const record = value as Record<string, unknown>;
  const nestedMetrics = record.metrics;
  const rows: Array<{ label: string; value: unknown }> = [];

  if (record.service) {
    rows.push({ label: "Service", value: record.service });
  }
  if (record.window) {
    rows.push({ label: "Window", value: record.window });
  }

  if (nestedMetrics && typeof nestedMetrics === "object" && !Array.isArray(nestedMetrics)) {
    for (const [metricName, metricValue] of Object.entries(nestedMetrics as Record<string, unknown>)) {
      if (metricValue && typeof metricValue === "object" && !Array.isArray(metricValue)) {
        const metricRecord = metricValue as Record<string, unknown>;
        const before = metricRecord.before;
        const current = metricRecord.current;
        const threshold = metricRecord.threshold;
        rows.push({
          label: formatMetricLabel(metricName),
          value: [
            before != null && current != null ? `${stringify(before)} → ${stringify(current)}` : current != null ? stringify(current) : before != null ? stringify(before) : null,
            threshold != null ? `(threshold ${stringify(threshold)})` : null,
          ]
            .filter(Boolean)
            .join(" "),
        });
      } else {
        rows.push({ label: formatMetricLabel(metricName), value: metricValue });
      }
    }
    return rows;
  }

  for (const [label, metricValue] of Object.entries(record)) {
    rows.push({ label: formatMetricLabel(label), value: metricValue });
  }
  return rows;
}

function formatMetricLabel(value: string) {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function formatFriendlyValue(value: unknown) {
  if (value == null || value === "") {
    return "—";
  }
  if (Array.isArray(value)) {
    return value.map((item) => stringify(item)).join(", ");
  }
  if (typeof value === "object") {
    return stringify(value);
  }
  const text = String(value);
  return text.replaceAll("_", " ").replace(/\b([a-z])/g, (match) => match.toUpperCase());
}

function formatTimestamp(value: unknown) {
  if (value == null) {
    return "—";
  }
  const parsed = typeof value === "string" ? new Date(value) : null;
  if (parsed && !Number.isNaN(parsed.getTime())) {
    return parsed.toLocaleString();
  }
  return stringify(value);
}

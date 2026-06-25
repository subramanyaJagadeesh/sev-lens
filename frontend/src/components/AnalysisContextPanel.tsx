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

  const metrics = operationalContext ? toEntries(operationalContext.metrics) : [];
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
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <section className="min-w-0 rounded-xl border border-border bg-panel-soft p-4">
            <p className="text-xs uppercase tracking-wide text-subtle">Deployments</p>
            {deployments.length ? (
              <div className="mt-3 space-y-3">
                {deployments.slice(0, 2).map((deployment) => (
                  <div key={stringify(deployment)} className="rounded-lg border border-border bg-[color:var(--surface)] p-3">
                    <p className="break-words text-sm font-medium">{stringify((deployment as Record<string, unknown>).commit ?? "Deployment")}</p>
                    <p className="mt-1 break-words text-xs text-subtle">{stringify((deployment as Record<string, unknown>).deployed_at ?? "—")}</p>
                    <p className="mt-2 break-words text-xs text-muted">{stringify((deployment as Record<string, unknown>).changes ?? [])}</p>
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

          <section className="min-w-0 space-y-4">
            <div className="rounded-xl border border-border bg-panel-soft p-4">
              <p className="text-xs uppercase tracking-wide text-subtle">Service metadata</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {serviceMetadata.length ? (
                  serviceMetadata.map(([label, value]) => (
                    <div key={label} className="rounded-lg border border-border bg-[color:var(--surface)] p-3">
                      <p className="text-xs uppercase tracking-wide text-subtle">{label.replace(/_/g, " ")}</p>
                      <p className="mt-1 break-words text-sm text-strong">{value}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted">No service metadata available.</p>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-panel-soft p-4">
              <p className="text-xs uppercase tracking-wide text-subtle">Metrics</p>
              {metrics.length ? (
                <dl className="mt-3 space-y-2">
                  {metrics.map(([label, value]) => (
                    <div key={label}>
                      <dt className="text-xs text-subtle">{label.replace(/_/g, " ")}</dt>
                      <dd className="break-words text-sm text-strong">{value}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <p className="mt-2 text-sm text-muted">No metrics snapshot available.</p>
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

import type { IncidentAnalysisRun } from "../contracts/incidentContracts";
import { getRawModelOutput } from "../lib/analysisView";

type Props = {
  analysisRun: IncidentAnalysisRun | null;
};

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

export function LogEvidencePanel({ analysisRun }: Props) {
  const raw = getRawModelOutput(analysisRun);
  const operationalContext = raw && typeof raw === "object" ? (raw as Record<string, unknown>).operational_context : null;
  const logEvidence = operationalContext && typeof operationalContext === "object" && Array.isArray(operationalContext.log_evidence)
    ? (operationalContext.log_evidence as Array<Record<string, unknown>>)
    : [];

  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Log evidence</h3>
        <p className="text-sm text-muted">Summarized OpenSearch evidence used by the analysis pipeline.</p>
      </div>

      {!analysisRun?.recommendation ? (
        <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
          No log evidence is available until the selected run produces a recommendation.
        </div>
      ) : logEvidence.length ? (
        <div className="space-y-3">
          {logEvidence.map((item) => (
            <div key={`${stringify(item.scenario_id)}-${stringify(item.time_window)}-${stringify(item.summary)}`} className="rounded-xl border border-border bg-panel-soft p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="break-words text-sm font-medium text-strong">{stringify(item.summary)}</p>
                <span className="chip px-2 py-1 text-[11px]">{stringify(item.source ?? "opensearch")}</span>
              </div>
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                <Meta label="Window" value={stringify(item.time_window)} />
                <Meta label="Score" value={stringify(item.score ?? "1.0")} />
              </div>
              {Array.isArray(item.top_errors) && item.top_errors.length ? (
                <div className="mt-3">
                  <p className="text-xs uppercase tracking-wide text-subtle">Top errors</p>
                  <ul className="mt-2 space-y-1 text-sm text-muted">
                    {item.top_errors.slice(0, 3).map((error) => (
                      <li key={stringify(error.error)} className="break-words">
                        {stringify(error.error)} · {stringify(error.count)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {Array.isArray(item.sample_messages) && item.sample_messages.length ? (
                <div className="mt-3">
                  <p className="text-xs uppercase tracking-wide text-subtle">Sample messages</p>
                  <ul className="mt-2 space-y-1 text-sm text-muted">
                    {item.sample_messages.map((message) => (
                      <li key={message} className="break-words">
                        {message}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
          The selected run did not retain log evidence.
        </div>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-subtle">{label}</p>
      <p className="mt-1 break-words text-sm text-strong">{value}</p>
    </div>
  );
}

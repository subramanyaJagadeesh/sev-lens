import type { IncidentAnalysisRun } from "../contracts/incidentContracts";
import { Select } from "./forms/Select";
import { formatStatusLabel } from "../lib/statusLabels";

type Props = {
  runs: IncidentAnalysisRun[];
  selectedRunId: string | null;
  defaultRunId: string | null;
  onSelectRun: (runId: string) => void;
};

function formatRunLabel(run: IncidentAnalysisRun, index: number) {
  const ordinal = index + 1;
  const timestamp = new Date(run.created_at).toLocaleString();
  return `Run ${ordinal} · ${formatStatusLabel(run.status)} · ${timestamp}`;
}

export function AnalysisRunSelector({ runs, selectedRunId, defaultRunId, onSelectRun }: Props) {
  if (!runs.length) {
    return (
      <div className="panel min-w-0 rounded-2xl p-5">
        <h3 className="text-lg font-semibold">Analysis runs</h3>
        <p className="mt-2 text-sm text-muted">This incident has not started an analysis run yet.</p>
      </div>
    );
  }

  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Analysis runs</h3>
        <p className="text-sm text-muted">Select a run to inspect its context, evidence, and recommendation.</p>
      </div>
      <label className="space-y-2 text-sm">
        <span className="text-subtle">Run</span>
        <Select
          value={selectedRunId ?? defaultRunId ?? runs[0].analysis_run_id}
          onChange={onSelectRun}
          options={runs.map((run, index) => ({
            value: run.analysis_run_id,
            label: formatRunLabel(run, index),
          }))}
        />
      </label>
      <div className="mt-4 grid max-w-4xl gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {runs.map((run, index) => {
          const isActive = run.analysis_run_id === (selectedRunId ?? defaultRunId ?? runs[0].analysis_run_id);
          return (
            <button
              key={run.analysis_run_id}
              type="button"
              onClick={() => onSelectRun(run.analysis_run_id)}
              className={`min-w-0 rounded-2xl border px-4 py-3 text-left transition ${
                isActive
                  ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)]"
                  : "border-[color:var(--border)] bg-[color:var(--surface-soft)] hover:border-[color:var(--accent)]"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium">Run {index + 1}</p>
                <span className="chip px-2 py-1 text-[11px]">{formatStatusLabel(run.status)}</span>
              </div>
              <p className="mt-2 break-words text-xs text-subtle">{new Date(run.created_at).toLocaleString()}</p>
              <p className="mt-2 break-words text-xs text-muted">{run.trigger_type}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

import type { IncidentAnalysisRun } from "../contracts/incidentContracts";
import { formatConfidenceLabel, formatStatusLabel } from "../lib/statusLabels";

type Props = {
  analysisRun: IncidentAnalysisRun | null;
};

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatLatency(value: number | null) {
  if (value == null) return "—";
  return `${value} ms`;
}

export function EvaluationPanel({ analysisRun }: Props) {
  if (!analysisRun) {
    return (
      <div className="panel min-w-0 rounded-2xl p-5">
        <div className="mb-4">
          <h3 className="text-lg font-semibold">Evaluation</h3>
          <p className="text-sm text-muted">Evaluation metadata appears once analysis has completed.</p>
        </div>
        <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
          No analysis run recorded yet.
        </div>
      </div>
    );
  }

  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Evaluation</h3>
        <p className="text-sm text-muted">Lightweight quality and timing metadata for the latest analysis run.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Metric label="Run status" value={formatStatusLabel(analysisRun.status)} />
        <Metric label="Latency" value={formatLatency(analysisRun.analysis_latency_ms)} />
        <Metric label="Retrieved docs" value={String(analysisRun.retrieved_document_count)} />
        <Metric label="Expected hit rate" value={formatPercent(analysisRun.expected_document_hit_rate)} />
        <Metric label="Evidence count" value={String(analysisRun.evidence_count)} />
        <Metric label="Actions" value={String(analysisRun.recommended_action_count)} />
        <Metric label="Confidence" value={formatConfidenceLabel(analysisRun.confidence_value)} />
        <Metric label="Human outcome" value={analysisRun.human_decision_outcome ?? "—"} />
      </div>
      <div className="mt-4 rounded-xl border border-border bg-panel-soft p-4 text-sm text-muted">
        <p className="text-xs uppercase tracking-wide text-subtle">Expected evidence signals</p>
        <p className="mt-2 break-words">{analysisRun.expected_evidence_signals.length ? analysisRun.expected_evidence_signals.join(", ") : "None configured."}</p>
        <p className="mt-4 text-xs uppercase tracking-wide text-subtle">Expected recommendation direction</p>
        <p className="mt-2 break-words">{analysisRun.expected_recommendation_direction || "Not configured."}</p>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-panel-soft p-4">
      <p className="text-xs uppercase tracking-wide text-subtle">{label}</p>
      <p className="mt-2 break-words text-sm font-medium text-strong">{value}</p>
    </div>
  );
}

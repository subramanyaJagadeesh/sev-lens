import { useEffect, useMemo, useState } from "react";
import { listRcaFeedback, recordRcaFeedback } from "../api";
import type { IncidentAnalysisRun } from "../contracts/incidentContracts";
import type { RcaFeedback, RcaMemoryMatch } from "../contracts/rcaContracts";
import { getRcaMatches } from "../lib/analysisView";

type Props = {
  incidentId: string;
  analysisRun: IncidentAnalysisRun | null;
};

export function RcaMatchPanel({ incidentId, analysisRun }: Props) {
  const matches = useMemo(() => getRcaMatches(analysisRun), [analysisRun]);
  const [feedbackByRcaId, setFeedbackByRcaId] = useState<Record<string, RcaFeedback[]>>({});
  const [isSaving, setIsSaving] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!analysisRun?.analysis_run_id || !matches.length) {
      setFeedbackByRcaId({});
      return;
    }
    let cancelled = false;
    void listRcaFeedback({ incidentId, analysisRunId: analysisRun.analysis_run_id })
      .then((feedback) => {
        if (cancelled) {
          return;
        }
        const grouped = feedback.reduce<Record<string, RcaFeedback[]>>((accumulator, item) => {
          accumulator[item.rca_id] = [...(accumulator[item.rca_id] ?? []), item];
          return accumulator;
        }, {});
        setFeedbackByRcaId(grouped);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [analysisRun?.analysis_run_id, incidentId, matches.length]);

  async function handleFeedback(match: RcaMemoryMatch, helpful: boolean) {
    if (!analysisRun?.analysis_run_id) {
      return;
    }
    setIsSaving((current) => ({ ...current, [match.rca_id]: true }));
    try {
      const saved = await recordRcaFeedback({
        incident_id: incidentId,
        rca_id: match.rca_id,
        helpful,
        analysis_run_id: analysisRun.analysis_run_id,
        note: `Marked from incident detail as ${helpful ? "helpful" : "not helpful"}`,
      });
      setFeedbackByRcaId((current) => ({
        ...current,
        [match.rca_id]: [...(current[match.rca_id] ?? []), saved],
      }));
    } finally {
      setIsSaving((current) => ({ ...current, [match.rca_id]: false }));
    }
  }

  return (
    <div className="panel min-w-0 rounded-2xl p-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">RCA memory</h3>
        <p className="text-sm text-muted">Similar historical incidents and why they match the current incident.</p>
      </div>

      {!analysisRun?.recommendation ? (
        <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
          RCA matches will appear when the selected run has a recommendation.
        </div>
      ) : matches.length ? (
        <div className="space-y-4">
          {matches.map((match) => {
            const feedback = feedbackByRcaId[match.rca_id] ?? [];
            const latestFeedback = feedback.at(0) ?? null;
            return (
              <div key={match.rca_id} className="rounded-xl border border-border bg-panel-soft p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">{match.title}</p>
                    <p className="mt-1 text-xs text-subtle">
                      {match.service_name} • {match.severity} • {match.incident_date || "Date not set"}
                    </p>
                  </div>
                  <span className="chip-accent px-3 py-1 text-xs">Score {match.score.toFixed(3)}</span>
                </div>

                <p className="mt-3 text-sm text-strong">{match.match_explanation}</p>

                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <MiniBlock title="Root cause" value={match.root_cause || "Not captured"} />
                  <MiniBlock title="Resolution" value={match.resolution || "Not captured"} />
                  <MiniBlock title="Helpful votes" value={String(match.helpful_count)} />
                  <MiniBlock title="Not helpful votes" value={String(match.not_helpful_count)} />
                </div>

                {match.prevention_items.length ? (
                  <div className="mt-4">
                    <p className="text-xs uppercase tracking-wide text-subtle">Prevention items</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
                      {match.prevention_items.map((item) => (
                        <li key={`${match.rca_id}-${item}`}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    className="button button-success"
                    disabled={Boolean(isSaving[match.rca_id])}
                    onClick={() => handleFeedback(match, true)}
                  >
                    Helpful
                  </button>
                  <button
                    type="button"
                    className="button button-danger"
                    disabled={Boolean(isSaving[match.rca_id])}
                    onClick={() => handleFeedback(match, false)}
                  >
                    Not helpful
                  </button>
                  {latestFeedback ? (
                    <span className="text-xs text-muted">
                      Last feedback: {latestFeedback.helpful ? "helpful" : "not helpful"}
                    </span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
          No RCA matches are available for the selected run yet.
        </div>
      )}
    </div>
  );
}

function MiniBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-[color:var(--surface)] p-3">
      <p className="text-xs uppercase tracking-wide text-subtle">{title}</p>
      <p className="mt-1 text-sm text-strong">{value}</p>
    </div>
  );
}

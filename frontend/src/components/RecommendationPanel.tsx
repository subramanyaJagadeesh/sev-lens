import type { Recommendation } from "../contracts/incidentContracts";
import { formatConfidenceLabel } from "../lib/statusLabels";

type Props = {
  recommendation: Recommendation | null;
  queued?: boolean;
  failed?: boolean;
  failureMessage?: string;
};

export function RecommendationPanel({ recommendation, queued = false, failed = false, failureMessage }: Props) {
  if (!recommendation) {
    return (
      <div className="panel rounded-xl border-dashed p-4 text-sm text-muted">
        {failed
          ? failureMessage ?? "Analysis failed. Retry to generate a recommendation."
          : queued
            ? "Analysis is queued. Recommendation will appear once the worker picks it up."
            : "No recommendation available yet."}
      </div>
    );
  }

  return (
    <div className="panel min-w-0 space-y-4 rounded-xl p-4">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-semibold">Recommendation</h3>
        <div className="group relative">
          <span className="chip-accent cursor-help px-3 py-1 text-xs">{formatConfidenceLabel(recommendation.confidence)}</span>
          <div className="pointer-events-none absolute right-0 top-full z-20 mt-2 w-max max-w-xs rounded-lg border border-border bg-[color:var(--surface-strong)] px-3 py-2 text-xs text-strong opacity-0 shadow-lg transition group-hover:opacity-100">
            recommendation confidence
          </div>
        </div>
      </div>
      <p className="break-words text-sm text-strong">{recommendation.summary}</p>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Evidence</p>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {recommendation.evidence.map((item) => (
            <li key={item} className="break-words">
              {item}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Recommended actions</p>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {recommendation.recommended_actions.map((item) => (
            <li key={item} className="break-words">
              {item}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

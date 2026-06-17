import type { Recommendation } from "../contracts/incidentContracts";

type Props = {
  recommendation: Recommendation | null;
};

export function RecommendationPanel({ recommendation }: Props) {
  if (!recommendation) {
    return (
      <div className="panel rounded-xl border-dashed p-4 text-sm text-muted">
        No recommendation available yet.
      </div>
    );
  }

  return (
    <div className="panel space-y-4 rounded-xl p-4">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-semibold">Recommendation</h3>
        <span className="chip-accent px-3 py-1 text-xs">{recommendation.confidence}</span>
      </div>
      <p className="text-sm text-strong">{recommendation.summary}</p>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Evidence</p>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {recommendation.evidence.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Recommended actions</p>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          {recommendation.recommended_actions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

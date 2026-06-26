import { useEffect, useMemo, useState } from "react";
import type { Recommendation } from "../contracts/incidentContracts";
import { Select } from "./forms/Select";
import { formatConfidenceLabel } from "../lib/statusLabels";

type Props = {
  recommendation: Recommendation | null;
  queued?: boolean;
  failed?: boolean;
  failureMessage?: string;
};

export function RecommendationPanel({ recommendation, queued = false, failed = false, failureMessage }: Props) {
  const actionOptions = useMemo(
    () =>
      recommendation?.action_evidence_links?.map((item, index) => ({
        value: `${index}`,
        label: stringValue(item["action"]) || `Action ${index + 1}`,
      })) ?? [],
    [recommendation],
  );
  const [selectedActionIndex, setSelectedActionIndex] = useState("0");

  useEffect(() => {
    setSelectedActionIndex(actionOptions[0]?.value ?? "0");
  }, [actionOptions]);

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
        <div className="flex flex-wrap items-center justify-end gap-2">
          {recommendation.risk_level ? <span className="chip-accent px-3 py-1 text-xs">{formatLabel(recommendation.risk_level)}</span> : null}
        </div>
      </div>
      {(recommendation.incident_summary || recommendation.symptoms?.length) && (
        <div className="rounded-xl border border-border bg-panel-soft p-4">
          <p className="text-xs uppercase tracking-wide text-subtle">Incident context</p>
          {recommendation.incident_summary ? <p className="mt-2 break-words text-sm text-strong">{recommendation.incident_summary}</p> : null}
          {recommendation.symptoms?.length ? <p className="mt-2 break-words text-sm text-muted">{recommendation.symptoms.join(", ")}</p> : null}
        </div>
      )}
      <p className="break-words text-sm text-strong">{recommendation.summary}</p>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Evidence-backed actions</p>
        {recommendation.action_evidence_links?.length ? (
          <div className="space-y-4">
            <label className="space-y-2 text-sm">
              <span className="text-subtle">Select action</span>
              <Select
                value={selectedActionIndex}
                onChange={setSelectedActionIndex}
                options={actionOptions}
                maxLabelLength={30}
                ariaLabel="Select recommendation action"
              />
            </label>

            {recommendation.action_evidence_links
              .filter((_, index) => `${index}` === selectedActionIndex)
              .map((item, index) => (
                <div
                  key={`${stringValue(item["action"])}-${index}`}
                  className="rounded-2xl border border-border bg-[color:var(--surface-soft)] p-5 shadow-sm transition hover:border-[color:var(--accent)]"
                >
                  <div className="flex flex-col gap-3 border-b border-border/70 pb-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0 space-y-2">
                      <p className="text-[11px] uppercase tracking-[0.28em] text-subtle">Recommended action</p>
                      <p className="break-words text-base font-semibold text-strong">{stringValue(item["action"])}</p>
                      <p className="max-w-3xl break-words text-sm text-muted">
                        {summarizeActionSupport(item["evidence"], item["source_documents"], item["similar_rcas"])}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 sm:justify-end">
                      <span className="chip-accent px-3 py-1 text-xs">{countLabel(item["evidence"], "evidence")}</span>
                      <span className="chip px-3 py-1 text-xs">{countLabel(item["source_documents"], "source docs")}</span>
                      <span className="chip px-3 py-1 text-xs">{countLabel(item["similar_rcas"], "similar RCAs")}</span>
                    </div>
                  </div>

                  <div className="mt-4 space-y-3">
                    <EvidenceGroup
                      title="Evidence"
                      accent="chip-accent"
                      items={arrayValue(item["evidence"])}
                      emptyLabel="No direct evidence captured."
                    />
                    <EvidenceGroup
                      title="Source documents"
                      accent="chip"
                      items={arrayValue(item["source_documents"])}
                      emptyLabel="No source documents attached."
                    />
                    <EvidenceGroup
                      title="Similar RCAs"
                      accent="chip"
                      items={arrayValue(item["similar_rcas"])}
                      emptyLabel="No RCA matches attached."
                    />
                  </div>
                </div>
              ))}
          </div>
        ) : (
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
              {recommendation.evidence.map((item) => (
                <li key={item} className="break-words">
                  {item}
                </li>
              ))}
            </ul>
        )}
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
      {recommendation.hypotheses?.length ? (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Hypotheses</p>
          <ul className="space-y-2 text-sm text-muted">
            {recommendation.hypotheses.map((item, index) => (
              <li key={`${stringValue(item["hypothesis"])}-${index}`} className="rounded-lg border border-border bg-panel-soft px-3 py-2">
                <p className="break-words text-strong">{stringValue(item["hypothesis"])}</p>
                <p className="mt-1 text-xs text-subtle">Confidence: {formatLabel(stringValue(item["confidence"]))}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {recommendation.source_documents?.length ? (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Source documents</p>
          <ul className="space-y-2 text-sm text-muted">
            {recommendation.source_documents.map((item, index) => (
              <li key={`${stringValue(item["title"])}-${index}`} className="rounded-lg border border-border bg-panel-soft px-3 py-2">
                <p className="break-words text-strong">{stringValue(item["title"])}</p>
                <p className="mt-1 text-xs text-subtle">
                  {stringValue(item["doc_type"])}{item["service"] ? ` · ${stringValue(item["service"])}` : ""}
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {recommendation.similar_rcas?.length ? (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Similar RCAs</p>
          <ul className="space-y-2 text-sm text-muted">
            {recommendation.similar_rcas.map((item, index) => (
              <li key={`${stringValue(item["title"])}-${index}`} className="rounded-lg border border-border bg-panel-soft px-3 py-2">
                <p className="break-words text-strong">{stringValue(item["title"])}</p>
                <p className="mt-1 text-xs text-subtle">{stringValue(item["match_explanation"])}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {recommendation.unsupported_areas?.length ? (
        <div>
          <p className="mb-2 text-xs uppercase tracking-wide text-subtle">Unsupported / low-confidence areas</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {recommendation.unsupported_areas.map((item) => (
              <li key={item} className="break-words">
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function EvidenceGroup({
  title,
  items,
  emptyLabel,
  accent,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
  accent: "chip" | "chip-accent";
}) {
  return (
    <section className="rounded-xl border border-border bg-[color:var(--surface)] p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.22em] text-subtle">{title}</p>
        <span className={`${accent} px-2 py-1 text-[11px]`}>{items.length}</span>
      </div>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm text-muted">
          {items.map((item) => (
            <li key={item} className="rounded-lg border border-border/80 bg-[color:var(--surface-soft)] px-3 py-2 leading-5">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-3 rounded-lg border border-dashed border-border bg-panel-soft px-3 py-4 text-sm text-muted">
          {emptyLabel}
        </div>
      )}
    </section>
  );
}

function stringValue(value: unknown) {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return value == null ? "" : JSON.stringify(value);
}

function arrayValue(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => stringValue(item)).filter(Boolean);
}

function summarizeActionSupport(
  evidenceValue: unknown,
  sourceDocumentsValue: unknown,
  similarRcasValue: unknown,
) {
  const evidenceCount = arrayValue(evidenceValue).length;
  const sourceCount = arrayValue(sourceDocumentsValue).length;
  const rcaCount = arrayValue(similarRcasValue).length;
  const parts: string[] = [];

  if (evidenceCount) {
    parts.push(`${evidenceCount} evidence point${evidenceCount === 1 ? "" : "s"}`);
  }
  if (sourceCount) {
    parts.push(`${sourceCount} source doc${sourceCount === 1 ? "" : "s"}`);
  }
  if (rcaCount) {
    parts.push(`${rcaCount} RCA match${rcaCount === 1 ? "" : "es"}`);
  }

  return parts.length ? `Supported by ${parts.join(" · ")}.` : "No supporting context was attached to this action.";
}

function countLabel(value: unknown, noun: string) {
  const count = arrayValue(value).length;
  return `${count} ${noun}`;
}

function formatLabel(value: string) {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

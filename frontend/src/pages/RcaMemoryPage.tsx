import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getRcaMemory, listRcaMemories } from "../api";
import { PageHeader } from "../components/PageHeader";
import { Select } from "../components/forms/Select";
import type { RcaFeedback, RcaMemory } from "../contracts/rcaContracts";

type MemoryDetail = {
  memory: RcaMemory;
  feedback: RcaFeedback[];
};

function isKnownText(value: string | null | undefined) {
  if (value == null) {
    return false;
  }
  const normalized = value.trim().toLowerCase();
  return normalized.length > 0 && normalized !== "unknown" && normalized !== "not set" && normalized !== "not captured" && normalized !== "date not set";
}

export function RcaMemoryPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedId = searchParams.get("rcaId");
  const [memories, setMemories] = useState<RcaMemory[]>([]);
  const [detail, setDetail] = useState<MemoryDetail | null>(null);
  const [listSearchTerm, setListSearchTerm] = useState("");
  const [serviceFilter, setServiceFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const serviceOptions = useMemo(
    () =>
      Array.from(new Set(memories.map((memory) => memory.service_name).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [memories],
  );
  const severityOptions = useMemo(
    () =>
      Array.from(new Set(memories.map((memory) => memory.severity).filter(Boolean)))
        .sort()
        .map((value) => ({ value, label: value })),
    [memories],
  );

  const filteredMemories = useMemo(() => {
    const query = listSearchTerm.trim().toLowerCase();
    return memories.filter((memory) => {
      if (serviceFilter !== "ALL" && memory.service_name !== serviceFilter) {
        return false;
      }
      if (severityFilter !== "ALL" && memory.severity !== severityFilter) {
        return false;
      }
      if (!query) {
        return true;
      }
      return (
        memory.title.toLowerCase().includes(query) ||
        memory.rca_id.toLowerCase().includes(query) ||
        memory.service_name.toLowerCase().includes(query) ||
        memory.root_cause.toLowerCase().includes(query) ||
        memory.resolution.toLowerCase().includes(query) ||
        memory.symptoms.join(" ").toLowerCase().includes(query) ||
        memory.related_errors.join(" ").toLowerCase().includes(query)
      );
    });
  }, [listSearchTerm, memories, serviceFilter, severityFilter]);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    void listRcaMemories()
      .then((items) => {
        if (cancelled) {
          return;
        }
        setMemories(items);
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load RCA memories.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!filteredMemories.length) {
      return;
    }
    if (!selectedId || !filteredMemories.some((memory) => memory.rca_id === selectedId)) {
      setSearchParams({ rcaId: filteredMemories[0].rca_id });
    }
  }, [filteredMemories, selectedId, setSearchParams]);

  useEffect(() => {
    if (!selectedId) {
      return;
    }
    let cancelled = false;
    setDetail(null);
    setIsDetailLoading(true);
    setError(null);
    void getRcaMemory(selectedId)
      .then((response) => {
        if (!cancelled) {
          setDetail(response);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load RCA memory.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsDetailLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const detailRecord = detail?.memory ?? null;
  const detailFeedback = detail?.feedback ?? [];
  const detailHelpfulVotes = detailFeedback.length ? detailFeedback.filter((entry) => entry.helpful).length : detailRecord?.helpful_count ?? 0;
  const detailNotHelpfulVotes = detailFeedback.length ? detailFeedback.filter((entry) => !entry.helpful).length : detailRecord?.not_helpful_count ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="RCA memory"
        description="Browse historical incident memories, inspect why they match, and review feedback."
        showBackButton
        onBack={() => navigate("/knowledge")}
      />

      {error ? <div className="panel panel-danger rounded-2xl p-4">{error}</div> : null}

      <div className="panel rounded-2xl p-5">
        <div className="grid gap-3 md:grid-cols-3">
          <input
            className="input"
            value={listSearchTerm}
            onChange={(event) => setListSearchTerm(event.target.value)}
            placeholder="Search RCA memories"
          />
          <Select
            value={serviceFilter}
            onChange={setServiceFilter}
            options={[{ value: "ALL", label: "All services" }, ...serviceOptions]}
            ariaLabel="Filter RCA memories by service"
          />
          <Select
            value={severityFilter}
            onChange={setSeverityFilter}
            options={[{ value: "ALL", label: "All severities" }, ...severityOptions]}
            ariaLabel="Filter RCA memories by severity"
          />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section className="panel rounded-2xl p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Memory list</h2>
              <p className="text-sm text-muted">Select an RCA to inspect its stored context and feedback.</p>
            </div>
            <span className="chip px-4 py-2 text-xs">{filteredMemories.length} memories</span>
          </div>

          <div className="mt-4 space-y-3">
            {isLoading ? <p className="text-sm text-muted">Loading RCA memories…</p> : null}
            {!isLoading && !filteredMemories.length ? (
              <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                No RCA memories match the current filters.
              </div>
            ) : null}
            {filteredMemories.map((memory) => {
              const isSelected = selectedId === memory.rca_id;
              const selectedFeedback = isSelected && detailRecord?.rca_id === memory.rca_id ? detailFeedback : [];
              const helpfulVotes = selectedFeedback.length ? selectedFeedback.filter((entry) => entry.helpful).length : memory.helpful_count;

              return (
                <button
                  key={memory.rca_id}
                  type="button"
                  onClick={() => setSearchParams({ rcaId: memory.rca_id })}
                  className={`w-full rounded-xl border p-4 text-left transition ${
                    isSelected ? "border-[color:var(--accent)] bg-panel-soft" : "border-border bg-panel-soft/60"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold">{memory.title}</p>
                      <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1 text-xs text-subtle">
                        {isKnownText(memory.service_name) ? <span>{memory.service_name}</span> : null}
                        {isKnownText(memory.service_name) && isKnownText(memory.severity) ? <span>•</span> : null}
                        {isKnownText(memory.severity) ? <span>{memory.severity}</span> : null}
                        {((isKnownText(memory.service_name) || isKnownText(memory.severity)) && isKnownText(memory.incident_date)) ? <span>•</span> : null}
                        {isKnownText(memory.incident_date) ? <span>{memory.incident_date}</span> : null}
                      </div>
                    </div>
                    <span className="chip-accent px-4 py-2 text-xs">Helpful {helpfulVotes}</span>
                  </div>
                  {isKnownText(memory.root_cause) ? <p className="mt-3 max-h-12 overflow-hidden text-sm text-muted">{memory.root_cause}</p> : null}
                </button>
              );
            })}
          </div>
        </section>

        <section className="space-y-6">
          {isDetailLoading ? <div className="panel rounded-2xl p-6 text-muted">Loading RCA memory detail…</div> : null}
          {!isDetailLoading && detailRecord ? (
            <>
              <div className="panel rounded-2xl p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="heading-eyebrow text-xs">Selected RCA</p>
                    <h2 className="mt-2 text-2xl font-semibold">{detailRecord.title}</h2>
                    <p className="mt-1 text-sm text-muted">{detailRecord.rca_id}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {isKnownText(detailRecord.service_name) ? <span className="chip px-4 py-2">{detailRecord.service_name}</span> : null}
                    {isKnownText(detailRecord.severity) ? <span className="chip px-4 py-2">{detailRecord.severity}</span> : null}
                    <span className="chip px-4 py-2">{detailRecord.archived ? "Archived" : "Active"}</span>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 md:grid-cols-2">
                  {detailRecord.symptoms.length ? <InfoCard title="Symptoms" value={detailRecord.symptoms.join(", ")} /> : null}
                  {isKnownText(detailRecord.incident_date) ? <InfoCard title="Incident date" value={detailRecord.incident_date} /> : null}
                  <InfoCard title="Helpful votes" value={String(detailHelpfulVotes)} />
                  <InfoCard title="Not helpful votes" value={String(detailNotHelpfulVotes)} />
                </div>

                <div className="mt-5 grid gap-3 md:grid-cols-2">
                  {isKnownText(detailRecord.root_cause) ? <InfoCard title="Root cause" value={detailRecord.root_cause} /> : null}
                  {isKnownText(detailRecord.resolution) ? <InfoCard title="Resolution" value={detailRecord.resolution} /> : null}
                </div>

                {detailRecord.prevention_items.length ? (
                  <div className="mt-5">
                    <p className="text-xs uppercase tracking-wide text-subtle">Prevention items</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
                      {detailRecord.prevention_items.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>

              <div className="panel rounded-2xl p-5">
                <h3 className="text-lg font-semibold">Feedback</h3>
                <p className="text-sm text-muted">Recent helpful / not helpful signals recorded for this RCA.</p>
                <div className="mt-4 space-y-3">
                  {detail?.feedback.length ? (
                    detail.feedback.map((entry) => (
                      <div key={entry.feedback_id} className="rounded-xl border border-border bg-panel-soft p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className={`chip px-4 py-2 ${entry.helpful ? "chip-success" : "chip-danger"}`}>
                            {entry.helpful ? "Helpful" : "Not helpful"}
                          </span>
                          <span className="text-xs text-subtle">{new Date(entry.created_at).toLocaleString()}</span>
                        </div>
                        <p className="mt-2 text-sm text-muted">{entry.note || "No note provided."}</p>
                        <p className="mt-2 text-xs text-subtle">Incident {entry.incident_id}</p>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                      No feedback has been recorded for this RCA yet.
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}

function InfoCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-panel-soft p-4">
      <p className="text-xs uppercase tracking-wide text-subtle">{title}</p>
      <p className="mt-2 break-words text-sm text-strong">{value}</p>
    </div>
  );
}

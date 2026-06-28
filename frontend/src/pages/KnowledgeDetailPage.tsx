import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getKnowledgeDocument, getRcaMemory, reindexKnowledgeDocument } from "../api";
import { PageHeader } from "../components/PageHeader";
import type { KnowledgeDocumentDetail } from "../contracts/knowledgeContracts";
import type { RcaFeedback, RcaMemory } from "../contracts/rcaContracts";

function isKnownText(value: string | null | undefined) {
  if (value == null) {
    return false;
  }
  const normalized = value.trim().toLowerCase();
  return normalized.length > 0 && normalized !== "unknown" && normalized !== "not set" && normalized !== "not captured" && normalized !== "date not set";
}

export function KnowledgeDetailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const documentId = searchParams.get("documentId");
  const [detail, setDetail] = useState<KnowledgeDocumentDetail | null>(null);
  const [rcaDetail, setRcaDetail] = useState<{ memory: RcaMemory; feedback: RcaFeedback[] } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReindexing, setIsReindexing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) {
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    setRcaDetail(null);
    void getKnowledgeDocument(documentId)
      .then((response) => {
        if (!cancelled) {
          setDetail(response);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load knowledge document.");
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
  }, [documentId]);

  useEffect(() => {
    if (!detail || detail.document.doc_type !== "rca") {
      return;
    }
    let cancelled = false;
    void getRcaMemory(detail.document.document_id)
      .then((response) => {
        if (!cancelled) {
          setRcaDetail(response);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRcaDetail(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [detail]);

  async function handleReindex() {
    if (!documentId) {
      return;
    }
    setIsReindexing(true);
    setError(null);
    try {
      const response = await reindexKnowledgeDocument(documentId);
      setDetail(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to re-index knowledge document.");
    } finally {
      setIsReindexing(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge detail"
        description="Inspect metadata, raw content, chunks, and indexing state for a persisted KB document."
        showBackButton
        onBack={() => navigate("/knowledge")}
        actions={
          detail ? (
            <>
              <button type="button" className="button theme-toggle" onClick={() => navigate(`/knowledge?edit=${detail.document.document_id}`)}>
                Edit
              </button>
              <button type="button" className="button button-primary" onClick={handleReindex} disabled={isReindexing}>
                Re-index
              </button>
            </>
          ) : null
        }
      />

      {error ? <div className="panel panel-danger rounded-2xl p-4">{error}</div> : null}
      {isLoading ? <div className="panel rounded-2xl p-6 text-muted">Loading knowledge detail…</div> : null}

      {!isLoading && detail ? (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
          <div className="space-y-6">
            <section className="panel rounded-2xl p-5">
              <h2 className="text-xl font-semibold">{detail.document.title}</h2>
              <p className="mt-2 break-all text-sm text-subtle">{detail.document.document_id}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-panel-soft p-4">
                  <p className="text-xs uppercase tracking-wide text-subtle">Document type</p>
                  <p className="mt-2 text-sm text-strong">{detail.document.doc_type}</p>
                </div>
                {isKnownText(detail.document.service) ? (
                  <div className="rounded-xl border border-border bg-panel-soft p-4">
                    <p className="text-xs uppercase tracking-wide text-subtle">Service</p>
                    <p className="mt-2 text-sm text-strong">{detail.document.service}</p>
                  </div>
                ) : null}
                {detail.document.indexed_at ? (
                  <div className="rounded-xl border border-border bg-panel-soft p-4">
                    <p className="text-xs uppercase tracking-wide text-subtle">Indexed at</p>
                    <p className="mt-2 text-sm text-strong">{new Date(detail.document.indexed_at).toLocaleString()}</p>
                  </div>
                ) : null}
                <div className="rounded-xl border border-border bg-panel-soft p-4">
                  <p className="text-xs uppercase tracking-wide text-subtle">Chunk count</p>
                  <p className="mt-2 text-sm text-strong">{detail.document.chunk_count}</p>
                </div>
                {typeof detail.document.metadata.severity_relevance === "string" && detail.document.metadata.severity_relevance ? (
                  <div className="rounded-xl border border-border bg-panel-soft p-4 md:col-span-2">
                    <p className="text-xs uppercase tracking-wide text-subtle">Severity relevance</p>
                    <p className="mt-2 text-sm text-strong">{detail.document.metadata.severity_relevance}</p>
                  </div>
                ) : null}
              </div>
              <div className="mt-4">
                <p className="text-xs uppercase tracking-wide text-subtle">Tags</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {detail.document.tags.length ? detail.document.tags.map((tag) => (
                    <span key={tag} className="chip px-2 py-1 text-xs">
                      {tag}
                    </span>
                  )) : <span className="text-sm text-muted">No tags.</span>}
                </div>
              </div>
            </section>

            <section className="panel rounded-2xl p-5">
              <h2 className="text-xl font-semibold">Raw content</h2>
              <pre className="mt-4 whitespace-pre-wrap break-words rounded-xl border border-border bg-panel-soft p-4 text-sm text-muted">
                {detail.document.content}
              </pre>
            </section>

            <section className="panel rounded-2xl p-5">
              <h2 className="text-xl font-semibold">Linked incidents</h2>
              {detail?.document.doc_type === "rca" ? (
                rcaDetail?.feedback.length ? (
                  <div className="mt-4 space-y-3">
                    {rcaDetail.feedback.map((entry) => (
                      <div key={entry.feedback_id} className="rounded-xl border border-border bg-panel-soft p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold">Incident {entry.incident_id}</p>
                            <p className="mt-1 text-xs text-subtle">
                              {entry.analysis_run_id ? `Run ${entry.analysis_run_id}` : "No analysis run linked"}
                            </p>
                          </div>
                          <span className={`chip px-3 py-1 text-xs ${entry.helpful ? "chip-success" : "chip-danger"}`}>
                            {entry.helpful ? "Helpful" : "Not helpful"}
                          </span>
                        </div>
                        <p className="mt-3 text-sm text-muted">{entry.note || "No note provided."}</p>
                        <p className="mt-2 text-xs text-subtle">{new Date(entry.created_at).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                    No linked incidents have been recorded for this RCA yet.
                  </div>
                )
              ) : (
                <div className="mt-4 rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                  Linked incidents are only available for RCA documents.
                </div>
              )}
            </section>
          </div>

          <section className="panel min-w-0 rounded-2xl p-5">
            <h2 className="text-xl font-semibold">Chunks</h2>
            <p className="text-sm text-muted">Chunk list and indexing output currently persisted in the vector-backed KB.</p>
            <div className="mt-4 space-y-3">
              {detail.chunks.map((chunk) => (
                <div key={chunk.chunk_id} className="rounded-xl border border-border bg-panel-soft p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-semibold">Chunk {chunk.chunk_index + 1}</p>
                      <p className="text-xs text-subtle">{chunk.doc_type}{chunk.service ? ` • ${chunk.service}` : ""}</p>
                    </div>
                    <span className="chip px-3 py-1 text-xs">{chunk.chunk_id}</span>
                  </div>
                  <p className="mt-3 text-sm text-muted">{chunk.text}</p>
                </div>
              ))}
              {!detail.chunks.length ? (
                <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                  No chunks are available for this document yet.
                </div>
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

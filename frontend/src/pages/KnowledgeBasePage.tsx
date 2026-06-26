import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  createKnowledgeDocument,
  getKnowledgeDocument,
  listKnowledgeDocuments,
  reindexKnowledgeDocument,
  searchKnowledge,
  updateKnowledgeDocument,
} from "../api";
import { PageHeader } from "../components/PageHeader";
import { Select } from "../components/forms/Select";
import type {
  KnowledgeDocument,
  KnowledgeDocumentCreatePayload,
  KnowledgeDocumentDetail,
  KnowledgeSearchResult,
} from "../contracts/knowledgeContracts";

type EditorState = {
  documentId: string;
  title: string;
  docType: string;
  service: string;
  tags: string;
  severityRelevance: string;
  source: string;
  content: string;
};

const DEFAULT_EDITOR_STATE: EditorState = {
  documentId: "",
  title: "",
  docType: "runbook",
  service: "",
  tags: "",
  severityRelevance: "",
  source: "",
  content: "",
};

const DEFAULT_DOCUMENT_TYPES = ["runbook", "rca", "policy", "guide", "sop"];

function slugify(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function tagsToString(tags: string[]): string {
  return tags.join(", ");
}

function toEditorState(document: KnowledgeDocument): EditorState {
  return {
    documentId: document.document_id,
    title: document.title,
    docType: document.doc_type,
    service: document.service ?? "",
    tags: tagsToString(document.tags),
    severityRelevance:
      typeof document.metadata.severity_relevance === "string" ? document.metadata.severity_relevance : "",
    source: document.source ?? "",
    content: document.content,
  };
}

function buildPayload(editor: EditorState): KnowledgeDocumentCreatePayload {
  return {
    document_id: editor.documentId,
    title: editor.title.trim(),
    doc_type: editor.docType.trim(),
    service: editor.service.trim() || null,
    tags: editor.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    source: editor.source.trim() || null,
    content: editor.content.trim(),
    metadata: {
      severity_relevance: editor.severityRelevance.trim() || null,
    },
  };
}

export function KnowledgeBasePage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const editDocumentId = searchParams.get("edit");
  const editorSectionRef = useRef<HTMLElement | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocumentDetail | null>(null);
  const [editor, setEditor] = useState<EditorState>(DEFAULT_EDITOR_STATE);
  const [listSearchTerm, setListSearchTerm] = useState("");
  const [previewQuery, setPreviewQuery] = useState("");
  const [queryService, setQueryService] = useState("ALL");
  const [queryDocType, setQueryDocType] = useState("ALL");
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const serviceOptions = useMemo(() => {
    const services = Array.from(new Set(documents.map((document) => document.service).filter(Boolean))).sort();
    return services.map((service) => ({ value: service ?? "", label: service ?? "" }));
  }, [documents]);

  const docTypeOptions = useMemo(() => {
    const docTypes = Array.from(new Set([...DEFAULT_DOCUMENT_TYPES, ...documents.map((document) => document.doc_type)])).sort();
    return docTypes.map((docType) => ({ value: docType, label: docType }));
  }, [documents]);

  const filteredDocuments = useMemo(() => {
    const normalizedSearch = listSearchTerm.trim().toLowerCase();
    return documents.filter((document) => {
      if (queryService !== "ALL" && document.service !== queryService) {
        return false;
      }
      if (queryDocType !== "ALL" && document.doc_type !== queryDocType) {
        return false;
      }
      if (!normalizedSearch) {
        return true;
      }
      return (
        document.title.toLowerCase().includes(normalizedSearch) ||
        document.document_id.toLowerCase().includes(normalizedSearch) ||
        document.doc_type.toLowerCase().includes(normalizedSearch) ||
        (document.service ?? "").toLowerCase().includes(normalizedSearch) ||
        document.tags.join(" ").toLowerCase().includes(normalizedSearch)
      );
    });
  }, [documents, listSearchTerm, queryDocType, queryService]);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);
    void listKnowledgeDocuments()
      .then((items) => {
        if (cancelled) {
          return;
        }
        setDocuments(items);
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load knowledge documents.");
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
    if (!editDocumentId) {
      setSelectedDocument(null);
      setEditor(DEFAULT_EDITOR_STATE);
      return;
    }
    let cancelled = false;
    void getKnowledgeDocument(editDocumentId)
      .then((detail) => {
        if (cancelled) {
          return;
        }
        setSelectedDocument(detail);
        setEditor(toEditorState(detail.document));
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError instanceof Error ? requestError.message : "Unable to load knowledge detail.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [editDocumentId]);

  async function refreshDocuments(nextSelectedId?: string | null) {
    const items = await listKnowledgeDocuments();
    setDocuments(items);
    if (nextSelectedId) {
      const detail = await getKnowledgeDocument(nextSelectedId);
      setSelectedDocument(detail);
      setEditor(toEditorState(detail.document));
    }
  }

  function updateEditor<K extends keyof EditorState>(field: K, value: EditorState[K]) {
    setEditor((current) => ({ ...current, [field]: value }));
  }

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const normalizedDocumentId = editor.documentId.trim() || slugify(editor.title);
      const payload = buildPayload({ ...editor, documentId: normalizedDocumentId });
      if (!payload.document_id || !payload.title || !payload.doc_type || !payload.content) {
        throw new Error("Document ID, title, document type, and content are required.");
      }
      if (selectedDocument?.document.document_id) {
        await updateKnowledgeDocument(selectedDocument.document.document_id, {
          title: payload.title,
          doc_type: payload.doc_type,
          service: payload.service,
          tags: payload.tags,
          source: payload.source,
          content: payload.content,
          metadata: payload.metadata,
        });
        setMessage("Knowledge document updated.");
        await refreshDocuments(selectedDocument.document.document_id);
      } else {
        const created = await createKnowledgeDocument(payload);
        setMessage("Knowledge document created and indexed.");
        setSearchParams({ edit: created.document_id });
        await refreshDocuments(created.document_id);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save knowledge document.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleReindex() {
    if (!selectedDocument) {
      return;
    }
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const detail = await reindexKnowledgeDocument(selectedDocument.document.document_id);
      setSelectedDocument(detail);
      setEditor(toEditorState(detail.document));
      await refreshDocuments(selectedDocument.document.document_id);
      setMessage("Knowledge document re-indexed.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to re-index knowledge document.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleNewDocument() {
    setSearchParams({});
    setSelectedDocument(null);
    setEditor(DEFAULT_EDITOR_STATE);
    setMessage(null);
    setError(null);
    window.setTimeout(() => {
      editorSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 0);
  }

  async function handlePreviewSearch() {
    setIsSearching(true);
    setError(null);
    try {
        const results = await searchKnowledge({
        query: previewQuery.trim() || "incident remediation guidance",
        top_k: 8,
        service_name: queryService === "ALL" ? null : queryService,
        doc_types: queryDocType === "ALL" ? null : [queryDocType],
      });
      setSearchResults(results);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to run retrieval preview.");
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Base"
        description="Manage persisted knowledge documents, inspect indexing state, and preview retrieval against the local KB."
      />

      {error ? <div className="panel panel-danger rounded-2xl p-4">{error}</div> : null}
      {message ? <div className="panel rounded-2xl p-4 text-sm text-muted">{message}</div> : null}
      {isLoading ? <div className="panel rounded-2xl p-6 text-muted">Loading knowledge base…</div> : null}

      {!isLoading ? (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,1.25fr)]">
          <section className="panel min-w-0 rounded-2xl p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">Knowledge list</h2>
                <p className="text-sm text-muted">Browse indexed documents by service, type, and tags.</p>
              </div>
            </div>

            <div className="mt-4 grid gap-3">
              <input
                type="search"
                value={listSearchTerm}
                onChange={(event) => setListSearchTerm(event.target.value)}
                placeholder="Search title, document id, service, or tags"
                className="input"
              />
              <div className="grid gap-3 md:grid-cols-2">
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Service</span>
                  <Select
                    value={queryService}
                    onChange={setQueryService}
                    options={[
                      { value: "ALL", label: "All services" },
                      ...serviceOptions,
                    ]}
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Document type</span>
                  <Select
                    value={queryDocType}
                    onChange={setQueryDocType}
                    options={[
                      { value: "ALL", label: "All document types" },
                      ...docTypeOptions,
                    ]}
                  />
                </label>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              {filteredDocuments.map((document) => {
                const isSelected = document.document_id === selectedDocument?.document.document_id;
                return (
                  <div
                    key={document.document_id}
                    role="button"
                    tabIndex={0}
                    className={`panel w-full rounded-xl p-4 text-left transition ${
                      isSelected ? "border-[color:var(--accent)] bg-[color:var(--surface-strong)]" : "panel-hover"
                    }`}
                    onClick={() => navigate(`/knowledge/detail?documentId=${encodeURIComponent(document.document_id)}`)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        navigate(`/knowledge/detail?documentId=${encodeURIComponent(document.document_id)}`);
                      }
                    }}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-base font-semibold">{document.title}</p>
                        <p className="mt-1 break-all text-xs text-subtle">{document.document_id}</p>
                      </div>
                      <span className="chip px-3 py-1 text-xs">{document.doc_type}</span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
                      {document.service ? <span>{document.service}</span> : null}
                      <span>Chunks: {document.chunk_count}</span>
                      <span>{document.indexed_at ? "Indexed" : "Pending index"}</span>
                    </div>
                    {document.tags.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {document.tags.map((tag) => (
                          <span key={`${document.document_id}-${tag}`} className="chip px-2 py-1 text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}
                    <div className="mt-3 flex items-center justify-between text-xs text-subtle">
                      <span>{document.updated_at ? new Date(document.updated_at).toLocaleString() : "Unknown update time"}</span>
                      <button
                        type="button"
                        className="text-[color:var(--accent)]"
                        onClick={(event) => {
                          event.stopPropagation();
                          navigate(`/knowledge/detail?documentId=${encodeURIComponent(document.document_id)}`);
                        }}
                      >
                        Open detail
                      </button>
                    </div>
                  </div>
                );
              })}
              {!filteredDocuments.length ? (
                <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                  No knowledge documents match the current filters yet.
                </div>
              ) : null}
            </div>
          </section>

          <div className="space-y-6">
            <section ref={editorSectionRef} className="panel min-w-0 rounded-2xl p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">{selectedDocument ? "Edit knowledge" : "Add knowledge"}</h2>
                  <p className="text-sm text-muted">Create or update a persisted KB document and index it immediately.</p>
                </div>
                {selectedDocument ? (
                  <button type="button" className="button theme-toggle" onClick={handleReindex} disabled={isSaving}>
                    Re-index
                  </button>
                ) : null}
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Document ID</span>
                  <input
                    value={editor.documentId}
                    onChange={(event) => updateEditor("documentId", event.target.value)}
                    disabled={Boolean(selectedDocument)}
                    placeholder="notification-service-owner-guide"
                    className="input"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Document type</span>
                  <Select
                    value={editor.docType}
                    onChange={(value) => updateEditor("docType", value)}
                    options={docTypeOptions}
                    placeholder="Select a document type"
                    ariaLabel="Document type"
                  />
                </label>
                <label className="space-y-2 text-sm md:col-span-2">
                  <span className="text-subtle">Title</span>
                  <input
                    value={editor.title}
                    onChange={(event) => updateEditor("title", event.target.value)}
                    placeholder="Notification service escalation guide"
                    className="input"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Service</span>
                  <input
                    value={editor.service}
                    onChange={(event) => updateEditor("service", event.target.value)}
                    placeholder="notification-service"
                    className="input"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Tags</span>
                  <input
                    value={editor.tags}
                    onChange={(event) => updateEditor("tags", event.target.value)}
                    placeholder="kafka, alerts, escalation"
                    className="input"
                  />
                </label>
                <label className="space-y-2 text-sm">
                  <span className="text-subtle">Severity relevance</span>
                  <input
                    value={editor.severityRelevance}
                    onChange={(event) => updateEditor("severityRelevance", event.target.value)}
                    placeholder="P2, P1, customer-impacting"
                    className="input"
                  />
                </label>
                {selectedDocument ? (
                  <label className="space-y-2 text-sm md:col-span-2">
                    <span className="text-subtle">Source</span>
                    <input
                      value={editor.source}
                      onChange={(event) => updateEditor("source", event.target.value)}
                      placeholder="docs/knowledge/service-docs/notification-service.md"
                      className="input"
                    />
                  </label>
                ) : null}
                <label className="space-y-2 text-sm md:col-span-2">
                  <span className="text-subtle">Content</span>
                  <textarea
                    value={editor.content}
                    onChange={(event) => updateEditor("content", event.target.value)}
                    placeholder="Paste the operational knowledge content here."
                    className="input min-h-[18rem] resize-y"
                  />
                </label>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button type="button" className="button button-primary" onClick={handleSave} disabled={isSaving}>
                  {selectedDocument ? "Save changes" : "Save and index"}
                </button>
                {selectedDocument ? (
                  <button type="button" className="button theme-toggle" onClick={handleNewDocument}>
                    Create another
                  </button>
                ) : null}
              </div>
            </section>

            <section className="panel min-w-0 rounded-2xl p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">Retrieval preview</h2>
                  <p className="text-sm text-muted">Test how the KB ranks chunks for a query before analysis uses them.</p>
                </div>
                <button type="button" className="button theme-toggle" onClick={handlePreviewSearch} disabled={isSearching}>
                  Preview retrieval
                </button>
              </div>

              <div className="mt-4 space-y-3">
                <input
                  type="search"
                  value={previewQuery}
                  onChange={(event) => setPreviewQuery(event.target.value)}
                  placeholder="notification service kafka timeout escalation"
                  className="input"
                />
              </div>

              <div className="mt-4 space-y-3">
                {searchResults.map((result) => (
                  <div key={`${result.document_id}-${result.chunk_index}`} className="rounded-xl border border-border bg-panel-soft p-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-semibold">{result.title}</p>
                        <p className="text-xs text-subtle">
                          {result.doc_type}
                          {result.service ? ` • ${result.service}` : ""}
                          {` • Chunk ${result.chunk_index + 1}`}
                        </p>
                      </div>
                      <span className="chip-accent px-3 py-1 text-xs">Score {result.score.toFixed(3)}</span>
                    </div>
                    <p className="mt-3 text-sm text-muted">{result.text}</p>
                    {result.tags.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {result.tags.map((tag) => (
                          <span key={`${result.document_id}-${result.chunk_index}-${tag}`} className="chip px-2 py-1 text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
                {!searchResults.length ? (
                  <div className="rounded-xl border border-dashed border-border bg-panel-soft px-4 py-5 text-sm text-muted">
                    Retrieval preview results will appear here after you run a KB query.
                  </div>
                ) : null}
              </div>
            </section>
          </div>
        </div>
      ) : null}
    </div>
  );
}

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_loader import LoadedDocument, chunk_text, load_markdown_documents
from .schemas import DocumentRecord, RetrievedDocumentChunk

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    chromadb = None


@dataclass(frozen=True)
class IndexedChunk:
    source: str
    title: str
    doc_type: str
    service: str | None
    tags: list[str]
    text: str
    chunk_index: int


class KnowledgeBase:
    def __init__(self) -> None:
        self._chunks = self._build_chunks(load_markdown_documents())
        self._collection = self._build_chroma_collection() if chromadb else None
        if self._collection is not None:
            self._ingest_into_chroma()

    def _build_chunks(self, documents: list[LoadedDocument]) -> list[IndexedChunk]:
        chunks: list[IndexedChunk] = []
        for document in documents:
            for index, chunk in enumerate(chunk_text(document.text)):
                chunks.append(
                    IndexedChunk(
                        source=document.source,
                        title=document.title,
                        doc_type=document.doc_type,
                        service=document.service,
                        tags=document.tags,
                        text=chunk,
                        chunk_index=index,
                    )
                )
        return chunks

    def _build_chroma_collection(self):  # pragma: no cover - optional dependency path
        client = chromadb.EphemeralClient()
        return client.get_or_create_collection("opspulse-rag")

    def _ingest_into_chroma(self) -> None:  # pragma: no cover - optional dependency path
        for index, chunk in enumerate(self._chunks):
            self._collection.add(
                ids=[str(index)],
                documents=[chunk.text],
                metadatas=[
                    {
                        "source": chunk.source,
                        "title": chunk.title,
                        "doc_type": chunk.doc_type,
                        "service": chunk.service or "",
                        "tags": ",".join(chunk.tags),
                        "chunk_index": chunk.chunk_index,
                    }
                ],
            )

    def _score_chunk(self, query_tokens: set[str], chunk: IndexedChunk) -> float:
        text_tokens = set(chunk.text.lower().split())
        title_tokens = set(chunk.title.lower().split())
        tag_tokens = {tag.lower() for tag in chunk.tags}
        score = len(query_tokens & text_tokens)
        score += 2 * len(query_tokens & title_tokens)
        score += 2 * len(query_tokens & tag_tokens)
        if chunk.service and chunk.service.lower() in query_tokens:
            score += 4
        return float(score)

    def search(self, query: str, top_k: int = 5, service_name: str | None = None) -> list[RetrievedDocumentChunk]:
        if self._collection is not None:  # pragma: no cover - optional dependency path
            results = self._collection.query(query_texts=[query], n_results=top_k)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            retrieved: list[RetrievedDocumentChunk] = []
            for index, document in enumerate(documents):
                metadata = metadatas[index] or {}
                retrieved.append(
                    RetrievedDocumentChunk(
                        source=str(metadata.get("source", "")),
                        title=str(metadata.get("title", "")),
                        doc_type=str(metadata.get("doc_type", "")),
                        service=metadata.get("service") or None,
                        tags=(metadata.get("tags") or "").split(",") if metadata.get("tags") else [],
                        chunk_index=int(metadata.get("chunk_index", index)),
                        text=document,
                        score=float(1.0 / (1.0 + (distances[index] if distances else index))),
                    )
                )
            return [chunk for chunk in retrieved if not service_name or chunk.service in (None, "", service_name)][:top_k]

        query_tokens = {token.strip(".,:;!?").lower() for token in query.split() if token.strip()}
        ranked: list[tuple[float, IndexedChunk]] = []
        for chunk in self._chunks:
            if service_name and chunk.service and chunk.service != service_name:
                continue
            score = self._score_chunk(query_tokens, chunk)
            if score > 0:
                ranked.append((score, chunk))
        ranked.sort(key=lambda item: (item[0], len(item[1].text)), reverse=True)
        return [
            RetrievedDocumentChunk(
                source=chunk.source,
                title=chunk.title,
                doc_type=chunk.doc_type,
                service=chunk.service,
                tags=chunk.tags,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                score=score,
            )
            for score, chunk in ranked[:top_k]
        ]


def format_context_for_query(
    service_name: str,
    severity: str,
    symptom: str,
    metric_name: str | None,
    metric_value: str | None,
    threshold_value: str | None,
    deployment_summary: str | None,
) -> str:
    parts = [
        f"Service: {service_name}",
        f"Severity: {severity}",
        f"Symptom: {symptom}",
    ]
    if metric_name and metric_value and threshold_value:
        parts.append(f"Metric: {metric_name} is {metric_value} versus threshold {threshold_value}")
    if deployment_summary:
        parts.append(f"Recent deployment context: {deployment_summary}")
    parts.append("Need: relevant runbooks, similar RCAs, and remediation guidance")
    return "\n".join(parts)


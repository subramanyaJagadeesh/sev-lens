from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable
from uuid import uuid4

from shared.contracts.knowledge_contracts import KnowledgeChunk, KnowledgeDocument, KnowledgeRetrievalResult
from shared.contracts.rca_contracts import RcaFeedbackRecord, RcaMemoryMatch, RcaMemoryRecord

from .config import KNOWLEDGE_BACKEND, KNOWLEDGE_CHROMA_PATH, KNOWLEDGE_DB_PATH, PROJECT_ROOT
from .data_loader import LoadedDocument, chunk_text, load_markdown_documents
from .embedding_provider import EmbeddingProvider, create_embedding_provider

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional import is validated in smoke tests
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - dependency guard
    chromadb = None


@dataclass(frozen=True)
class KnowledgeContext:
    service_name: str
    severity: str
    symptom: str
    metric_name: str | None = None
    metric_value: str | None = None
    threshold_value: str | None = None
    deployment_summary: str | None = None
    service_profile_summary: str | None = None


@runtime_checkable
class KnowledgeBackend(Protocol):
    backend_name: str

    def add_document(self, document: KnowledgeDocument) -> KnowledgeDocument: ...

    def list_documents(self, include_archived: bool = False) -> list[KnowledgeDocument]: ...

    def get_document(self, document_id: str) -> KnowledgeDocument | None: ...

    def update_document(self, document_id: str, **changes: Any) -> KnowledgeDocument: ...

    def delete_document(self, document_id: str) -> None: ...

    def archive_document(self, document_id: str) -> KnowledgeDocument: ...

    def reindex_document(self, document_id: str) -> None: ...

    def list_document_chunks(self, document_id: str) -> list[KnowledgeChunk]: ...

    def list_rca_memories(self, include_archived: bool = False) -> list[RcaMemoryRecord]: ...

    def get_rca_memory(self, rca_id: str) -> RcaMemoryRecord | None: ...

    def search_rca_memories(
        self,
        incident_context: KnowledgeContext | Mapping[str, Any],
        top_k: int = 5,
        tags: list[str] | None = None,
    ) -> list[RcaMemoryMatch]: ...

    def record_rca_feedback(
        self,
        rca_id: str,
        incident_id: str,
        helpful: bool,
        analysis_run_id: str | None = None,
        note: str | None = None,
    ) -> RcaFeedbackRecord: ...

    def list_rca_feedback(
        self,
        incident_id: str | None = None,
        analysis_run_id: str | None = None,
        rca_id: str | None = None,
    ) -> list[RcaFeedbackRecord]: ...

    def search(
        self,
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]: ...

    def retrieve_by_context(
        self,
        incident_context: KnowledgeContext | Mapping[str, Any],
        top_k: int = 5,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]: ...

    def retrieve_by_document_type(
        self,
        document_types: list[str],
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]: ...

    def retrieve_by_service(
        self,
        service_name: str,
        query: str,
        top_k: int = 5,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]: ...

    def retrieve_by_tags(
        self,
        tags: list[str],
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]: ...


@dataclass(frozen=True)
class _StoredDocument:
    document_id: str
    title: str
    doc_type: str
    content: str
    service: str | None
    tags: list[str]
    source: str | None
    archived: bool
    metadata: dict[str, Any]
    chunk_ids: list[str]
    chunk_count: int
    created_at: str
    updated_at: str
    indexed_at: str | None

    def to_document(self) -> KnowledgeDocument:
        metadata = dict(self.metadata)
        metadata.setdefault("chunk_count", self.chunk_count)
        metadata.setdefault("created_at", self.created_at)
        metadata.setdefault("updated_at", self.updated_at)
        metadata.setdefault("indexed_at", self.indexed_at)
        metadata.setdefault("chunk_ids", list(self.chunk_ids))
        return KnowledgeDocument(
            document_id=self.document_id,
            title=self.title,
            doc_type=self.doc_type,
            content=self.content,
            service=self.service,
            tags=list(self.tags),
            source=self.source,
            archived=self.archived,
            metadata=metadata,
        )


class LocalKnowledgeBackend:
    backend_name = "local"
    _collection_name = "sevlens-knowledge"

    def __init__(
        self,
        seed_documents: list[LoadedDocument] | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        if chromadb is None:  # pragma: no cover - dependency guard
            raise RuntimeError("chromadb is required for the local knowledge backend")

        self._lock = threading.RLock()
        self._db_path = KNOWLEDGE_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._chroma_path = KNOWLEDGE_CHROMA_PATH
        self._chroma_path.parent.mkdir(parents=True, exist_ok=True)
        self._seed_documents = seed_documents or load_markdown_documents()
        self._embedding_provider = embedding_provider or create_embedding_provider()
        self._connection = sqlite3.connect(self._db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._client = chromadb.PersistentClient(path=str(self._chroma_path))
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._initialize_schema()
        self._migrate_legacy_document_ids()
        self._seed_missing_documents()
        self._repair_index_if_needed()
        logger.info(
            "Loaded persistent local knowledge backend documents=%s database=%s chroma=%s",
            len(self.list_documents(include_archived=True)),
            self._db_path,
            self._chroma_path,
        )

    def _initialize_schema(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    service TEXT,
                    tags_json TEXT NOT NULL,
                    source TEXT,
                    archived INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    chunk_ids_json TEXT NOT NULL DEFAULT '[]',
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    indexed_at TEXT
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS rca_feedback (
                    id TEXT PRIMARY KEY,
                    rca_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    analysis_run_id TEXT,
                    helpful INTEGER NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_service ON knowledge_documents(service)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_doc_type ON knowledge_documents(doc_type)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_documents_archived ON knowledge_documents(archived)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rca_feedback_rca_id ON rca_feedback(rca_id, created_at DESC)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rca_feedback_incident_run ON rca_feedback(incident_id, analysis_run_id)"
            )

    def _seed_missing_documents(self) -> None:
        existing_ids = {document.document_id for document in self.list_documents(include_archived=True)}
        seeded = 0
        for loaded_document in self._seed_documents:
            if loaded_document.document_id in existing_ids:
                continue
            self.add_document(
                KnowledgeDocument(
                    document_id=loaded_document.document_id,
                    title=loaded_document.title,
                    doc_type=loaded_document.doc_type,
                    content=loaded_document.text,
                    service=loaded_document.service,
                    tags=list(loaded_document.tags),
                    source=loaded_document.source,
                    metadata={**dict(loaded_document.metadata), "seeded": True},
                )
            )
            seeded += 1
        if seeded:
            logger.info("Seeded %s new knowledge documents from markdown sources", seeded)

    def _rca_metadata(self, document: _StoredDocument) -> dict[str, Any]:
        metadata = dict(document.metadata)
        return metadata if isinstance(metadata, dict) else {}

    def _record_to_rca_memory(self, record: _StoredDocument) -> RcaMemoryRecord:
        metadata = self._rca_metadata(record)
        feedback = self._rca_feedback_summary(record.document_id)
        return RcaMemoryRecord(
            rca_id=record.document_id,
            document_id=record.document_id,
            title=record.title,
            service_name=str(metadata.get("service_name") or record.service or ""),
            severity=str(metadata.get("severity") or metadata.get("severity_level") or "unknown"),
            symptoms=[str(item) for item in metadata.get("symptoms", []) if str(item).strip()],
            root_cause=str(metadata.get("root_cause") or ""),
            resolution=str(metadata.get("resolution") or ""),
            prevention_items=[str(item) for item in metadata.get("prevention_items", []) if str(item).strip()],
            related_errors=[str(item) for item in metadata.get("related_errors", []) if str(item).strip()],
            related_dependencies=[str(item) for item in metadata.get("related_dependencies", []) if str(item).strip()],
            incident_date=str(metadata.get("incident_date") or ""),
            source=record.source,
            tags=list(record.tags),
            archived=record.archived,
            metadata=metadata,
            helpful_count=feedback["helpful_count"],
            not_helpful_count=feedback["not_helpful_count"],
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _rca_feedback_summary(self, rca_id: str) -> dict[str, int]:
        cursor = self._connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END), 0) AS helpful_count,
                COALESCE(SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END), 0) AS not_helpful_count
            FROM rca_feedback
            WHERE rca_id = ?
            """,
            (rca_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return {"helpful_count": 0, "not_helpful_count": 0}
        return {
            "helpful_count": int(row["helpful_count"] or 0),
            "not_helpful_count": int(row["not_helpful_count"] or 0),
        }

    def _normalize_document_id(self, document: _StoredDocument) -> str | None:
        if not document.source:
            return None
        source_path = Path(document.source)
        if not source_path.is_absolute():
            source_path = (PROJECT_ROOT / source_path).resolve()
        try:
            source_path.relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            return None
        if "/" not in document.document_id and "\\" not in document.document_id and not document.document_id.endswith(".md"):
            return None
        normalized = f"{document.doc_type}-{source_path.stem}".lower()
        return "".join(char if char.isalnum() else "-" for char in normalized).strip("-")

    def _rename_document_id(self, old_document_id: str, new_document_id: str) -> None:
        if old_document_id == new_document_id:
            return
        record = self._load_record(old_document_id)
        if record is None:
            return
        self._delete_document_vectors(old_document_id, record.chunk_ids)
        with self._lock, self._connection:
            self._connection.execute("DELETE FROM knowledge_documents WHERE document_id = ?", (old_document_id,))
        if self._document_exists(new_document_id):
            return
        renamed = _StoredDocument(
            **{
                **record.__dict__,
                "document_id": new_document_id,
                "chunk_ids": [],
                "chunk_count": 0,
                "indexed_at": None,
                "updated_at": self._now(),
            }
        )
        indexed = self._index_document(renamed)
        self._persist_record(indexed)

    def _migrate_legacy_document_ids(self) -> None:
        migrated = 0
        for document in self.list_documents(include_archived=True):
            record = self._load_record(document.document_id)
            if record is None:
                continue
            normalized = self._normalize_document_id(record)
            if normalized and normalized != record.document_id:
                self._rename_document_id(record.document_id, normalized)
                migrated += 1
        if migrated:
            logger.info("Migrated %s legacy knowledge document ids to normalized ids", migrated)

    def _repair_index_if_needed(self) -> None:
        if self._collection.count() > 0:
            return
        documents = [document for document in self.list_documents(include_archived=False)]
        if not documents:
            return
        logger.info("Repairing empty vector index from %s persisted knowledge documents", len(documents))
        for document in documents:
            self._index_document(self._record_from_document(document))

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize_tags(self, tags: Any) -> list[str]:
        if tags is None:
            return []
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]
        return [str(tag) for tag in tags if str(tag).strip()]

    def _serialize_tags(self, tags: list[str]) -> str:
        return json.dumps(sorted({tag.strip() for tag in tags if tag.strip()}))

    def _serialize_metadata(self, metadata: dict[str, Any]) -> str:
        return json.dumps(metadata, sort_keys=True)

    def _merge_metadata(self, base: dict[str, Any], extra: Any) -> dict[str, Any]:
        merged = dict(base)
        if isinstance(extra, dict):
            merged.update(extra)
        elif extra is not None:
            merged.update(dict(extra))
        return merged

    def _deserialize_json(self, raw: str | None, default: Any) -> Any:
        if not raw:
            return default
        return json.loads(raw)

    def _row_to_record(self, row: sqlite3.Row) -> _StoredDocument:
        metadata = self._deserialize_json(row["metadata_json"], {})
        if not isinstance(metadata, dict):
            metadata = {}
        return _StoredDocument(
            document_id=str(row["document_id"]),
            title=str(row["title"]),
            doc_type=str(row["doc_type"]),
            content=str(row["content"]),
            service=row["service"] or None,
            tags=self._normalize_tags(self._deserialize_json(row["tags_json"], [])),
            source=row["source"] or None,
            archived=bool(row["archived"]),
            metadata=metadata,
            chunk_ids=[str(chunk_id) for chunk_id in self._deserialize_json(row["chunk_ids_json"], [])],
            chunk_count=int(row["chunk_count"] or 0),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            indexed_at=row["indexed_at"] or None,
        )

    def _document_exists(self, document_id: str) -> bool:
        return self._get_record_row(document_id) is not None

    def _get_record_row(self, document_id: str) -> sqlite3.Row | None:
        cursor = self._connection.execute(
            "SELECT * FROM knowledge_documents WHERE document_id = ?",
            (document_id,),
        )
        return cursor.fetchone()

    def _record_from_document(self, document: KnowledgeDocument) -> _StoredDocument:
        return _StoredDocument(
            document_id=document.document_id,
            title=document.title,
            doc_type=document.doc_type,
            content=document.content,
            service=document.service,
            tags=list(document.tags),
            source=document.source,
            archived=document.archived,
            metadata=dict(document.metadata),
            chunk_ids=[],
            chunk_count=0,
            created_at=self._now(),
            updated_at=self._now(),
            indexed_at=None,
        )

    def _chunk_document(self, document: _StoredDocument) -> list[tuple[str, str, list[float], dict[str, Any]]]:
        chunks = chunk_text(document.content)
        chunk_payloads: list[tuple[str, str, list[float], dict[str, Any]]] = []
        for index, chunk_text_value in enumerate(chunks):
            chunk_id = f"{document.document_id}::chunk::{index}"
            chunk_payloads.append(
                (
                    chunk_id,
                    chunk_text_value,
                    self._embedding_provider.embed_text(chunk_text_value),
                    {
                        "document_id": document.document_id,
                        "title": document.title,
                        "doc_type": document.doc_type,
                        "service": document.service or "",
                        "tags_json": self._serialize_tags(document.tags),
                        "source": document.source or "",
                        "archived": int(document.archived),
                        "chunk_index": index,
                    },
                )
            )
        return chunk_payloads

    def _delete_document_vectors(self, document_id: str, chunk_ids: list[str] | None = None) -> None:
        if chunk_ids:
            try:
                self._collection.delete(ids=list(chunk_ids))
                return
            except Exception:  # noqa: BLE001
                logger.exception("Failed deleting chunk ids for document_id=%s; trying metadata delete", document_id)
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception as exc:  # noqa: BLE001
            logger.debug("Metadata delete for document_id=%s failed: %s", document_id, exc)

    def _index_document(self, document: _StoredDocument) -> _StoredDocument:
        chunk_payloads = self._chunk_document(document)
        chunk_ids = [chunk_id for chunk_id, _, _, _ in chunk_payloads]
        if chunk_ids:
            self._collection.add(
                ids=chunk_ids,
                documents=[text for _, text, _, _ in chunk_payloads],
                embeddings=[embedding for _, _, embedding, _ in chunk_payloads],
                metadatas=[metadata for _, _, _, metadata in chunk_payloads],
            )
        updated = _StoredDocument(
            **{
                **document.__dict__,
                "chunk_ids": chunk_ids,
                "chunk_count": len(chunk_ids),
                "indexed_at": self._now(),
            }
        )
        return updated

    def _persist_record(self, record: _StoredDocument) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents (
                    document_id, title, doc_type, content, service, tags_json, source,
                    archived, metadata_json, chunk_ids_json, chunk_count, created_at, updated_at, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.document_id,
                    record.title,
                    record.doc_type,
                    record.content,
                    record.service,
                    self._serialize_tags(record.tags),
                    record.source,
                    int(record.archived),
                    self._serialize_metadata(record.metadata),
                    json.dumps(record.chunk_ids),
                    record.chunk_count,
                    record.created_at,
                    record.updated_at,
                    record.indexed_at,
                ),
            )

    def _load_record(self, document_id: str) -> _StoredDocument | None:
        row = self._get_record_row(document_id)
        if row is None:
            return None
        return self._row_to_record(row)

    def _search_records(
        self,
        query: str,
        top_k: int,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[tuple[_StoredDocument, str, int, float]]:
        query_embedding = self._embedding_provider.embed_text(query)
        search_size = max(top_k * 5, 20)
        response = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=search_size,
            include=["documents", "metadatas", "distances"],
        )
        documents = (response.get("documents") or [[]])[0]
        metadatas = (response.get("metadatas") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]
        results: list[tuple[_StoredDocument, str, int, float]] = []
        for index, chunk_text_value in enumerate(documents):
            metadata = metadatas[index] or {}
            document_id = str(metadata.get("document_id", ""))
            if not document_id:
                continue
            record = self._load_record(document_id)
            if record is None or record.archived:
                continue
            if service_name and record.service and record.service != service_name:
                continue
            if doc_types and record.doc_type not in doc_types:
                continue
            if tags and not set(tags).intersection(set(record.tags)):
                continue
            distance = float(distances[index]) if index < len(distances) and distances[index] is not None else 1.0
            score = 1.0 / (1.0 + max(distance, 0.0))
            results.append((record, str(chunk_text_value), int(metadata.get("chunk_index", 0)), score))
        results.sort(key=lambda item: (item[3], len(item[1])), reverse=True)
        return results[:top_k]

    def add_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        with self._lock:
            if self._document_exists(document.document_id):
                raise ValueError(f"Knowledge document already exists: {document.document_id}")
            record = self._record_from_document(document)
            indexed_record = self._index_document(record)
            self._persist_record(indexed_record)
            return indexed_record.to_document()

    def list_documents(self, include_archived: bool = False) -> list[KnowledgeDocument]:
        query = "SELECT * FROM knowledge_documents"
        params: tuple[Any, ...] = ()
        if not include_archived:
            query += " WHERE archived = 0"
        query += " ORDER BY updated_at DESC, title ASC"
        cursor = self._connection.execute(query, params)
        return [self._row_to_record(row).to_document() for row in cursor.fetchall()]

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        record = self._load_record(document_id)
        return record.to_document() if record else None

    def update_document(self, document_id: str, **changes: Any) -> KnowledgeDocument:
        with self._lock:
            record = self._load_record(document_id)
            if record is None:
                raise KeyError(f"Unknown knowledge document: {document_id}")

            payload = {
                "document_id": record.document_id,
                "title": changes.get("title", record.title),
                "doc_type": changes.get("doc_type", record.doc_type),
                "content": changes.get("content", record.content),
                "service": changes.get("service", record.service),
                "tags": self._normalize_tags(changes.get("tags", record.tags)),
                "source": changes.get("source", record.source),
                "archived": bool(changes.get("archived", record.archived)),
                "metadata": self._merge_metadata(record.metadata, changes.get("metadata")),
                "chunk_ids": list(record.chunk_ids),
                "chunk_count": record.chunk_count,
                "created_at": record.created_at,
                "updated_at": self._now(),
                "indexed_at": record.indexed_at,
            }

            self._delete_document_vectors(document_id, record.chunk_ids)
            updated_record = _StoredDocument(**payload)
            if not updated_record.archived:
                updated_record = self._index_document(updated_record)
            else:
                updated_record = _StoredDocument(
                    **{
                        **updated_record.__dict__,
                        "chunk_ids": [],
                        "chunk_count": 0,
                        "indexed_at": self._now(),
                    }
                )
            self._persist_record(updated_record)
            return updated_record.to_document()

    def delete_document(self, document_id: str) -> None:
        with self._lock, self._connection:
            record = self._load_record(document_id)
            if record is None:
                raise KeyError(f"Unknown knowledge document: {document_id}")
            self._delete_document_vectors(document_id, record.chunk_ids)
            self._connection.execute("DELETE FROM knowledge_documents WHERE document_id = ?", (document_id,))

    def archive_document(self, document_id: str) -> KnowledgeDocument:
        return self.update_document(document_id, archived=True)

    def reindex_document(self, document_id: str) -> None:
        with self._lock:
            record = self._load_record(document_id)
            if record is None:
                raise KeyError(f"Unknown knowledge document: {document_id}")
            self._delete_document_vectors(document_id, record.chunk_ids)
            reindexed = self._index_document(record)
            self._persist_record(reindexed)

    def list_document_chunks(self, document_id: str) -> list[KnowledgeChunk]:
        record = self._load_record(document_id)
        if record is None:
            raise KeyError(f"Unknown knowledge document: {document_id}")
        if not record.chunk_ids:
            return []
        response = self._collection.get(ids=record.chunk_ids, include=["documents", "metadatas"])
        documents = response.get("documents") or []
        metadatas = response.get("metadatas") or []
        ids = response.get("ids") or []
        chunks: list[KnowledgeChunk] = []
        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] or {}
            chunks.append(
                KnowledgeChunk(
                    chunk_id=str(chunk_id),
                    document_id=record.document_id,
                    title=record.title,
                    doc_type=record.doc_type,
                    text=str(documents[index] or ""),
                    chunk_index=int(metadata.get("chunk_index", index)),
                    service=record.service,
                    tags=list(record.tags),
                    source=record.source,
                    metadata={
                        "backend": self.backend_name,
                        "indexed_at": record.indexed_at,
                        **record.metadata,
                    },
                )
            )
        return sorted(chunks, key=lambda chunk: chunk.chunk_index)

    def list_rca_memories(self, include_archived: bool = False) -> list[RcaMemoryRecord]:
        documents = [
            self._load_record(document.document_id)
            for document in self.list_documents(include_archived=include_archived)
            if document.doc_type == "rca"
        ]
        return [self._record_to_rca_memory(record) for record in documents if record is not None]

    def get_rca_memory(self, rca_id: str) -> RcaMemoryRecord | None:
        record = self._load_record(rca_id)
        if record is None or record.doc_type != "rca":
            return None
        return self._record_to_rca_memory(record)

    def search_rca_memories(
        self,
        incident_context: KnowledgeContext | Mapping[str, Any],
        top_k: int = 5,
        tags: list[str] | None = None,
    ) -> list[RcaMemoryMatch]:
        context = self._coerce_context(incident_context)
        query = format_context_for_query(
            service_name=context.service_name,
            severity=context.severity,
            symptom=context.symptom,
            metric_name=context.metric_name,
            metric_value=context.metric_value,
            threshold_value=context.threshold_value,
            deployment_summary=context.deployment_summary,
            service_profile_summary=context.service_profile_summary,
        )
        normalized_tags = self._normalize_tags(tags)
        records = self._search_records(
            query=query,
            top_k=top_k,
            service_name=context.service_name,
            doc_types=["rca"],
            tags=normalized_tags,
        )
        matches: list[RcaMemoryMatch] = []
        for record, chunk_text_value, chunk_index, score in records:
            rca_memory = self._record_to_rca_memory(record)
            explanation, signals = self._build_rca_match_explanation(context, rca_memory, chunk_text_value)
            matches.append(
                RcaMemoryMatch(
                    rca_id=rca_memory.rca_id,
                    document_id=rca_memory.document_id,
                    title=rca_memory.title,
                    service_name=rca_memory.service_name,
                    severity=rca_memory.severity,
                    score=score,
                    match_explanation=explanation,
                    matched_signals=signals,
                    symptoms=list(rca_memory.symptoms),
                    root_cause=rca_memory.root_cause,
                    resolution=rca_memory.resolution,
                    prevention_items=list(rca_memory.prevention_items),
                    related_errors=list(rca_memory.related_errors),
                    related_dependencies=list(rca_memory.related_dependencies),
                    incident_date=rca_memory.incident_date,
                    source=rca_memory.source,
                    helpful_count=rca_memory.helpful_count,
                    not_helpful_count=rca_memory.not_helpful_count,
                    metadata={
                        **rca_memory.metadata,
                        "chunk_index": chunk_index,
                    },
                )
            )
        return matches

    def record_rca_feedback(
        self,
        rca_id: str,
        incident_id: str,
        helpful: bool,
        analysis_run_id: str | None = None,
        note: str | None = None,
    ) -> RcaFeedbackRecord:
        feedback_id = str(uuid4())
        created_at = self._now()
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO rca_feedback (
                    id, rca_id, incident_id, analysis_run_id, helpful, note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    rca_id,
                    incident_id,
                    analysis_run_id,
                    1 if helpful else 0,
                    note,
                    created_at,
                ),
            )
        return RcaFeedbackRecord(
            feedback_id=feedback_id,
            rca_id=rca_id,
            incident_id=incident_id,
            analysis_run_id=analysis_run_id,
            helpful=helpful,
            note=note,
            created_at=created_at,
        )

    def list_rca_feedback(
        self,
        incident_id: str | None = None,
        analysis_run_id: str | None = None,
        rca_id: str | None = None,
    ) -> list[RcaFeedbackRecord]:
        query = "SELECT * FROM rca_feedback"
        clauses: list[str] = []
        params: list[Any] = []
        if incident_id is not None:
            clauses.append("incident_id = ?")
            params.append(incident_id)
        if analysis_run_id is not None:
            clauses.append("analysis_run_id = ?")
            params.append(analysis_run_id)
        if rca_id is not None:
            clauses.append("rca_id = ?")
            params.append(rca_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        cursor = self._connection.execute(query, tuple(params))
        records: list[RcaFeedbackRecord] = []
        for row in cursor.fetchall():
            records.append(
                RcaFeedbackRecord(
                    feedback_id=str(row["id"]),
                    rca_id=str(row["rca_id"]),
                    incident_id=str(row["incident_id"]),
                    analysis_run_id=row["analysis_run_id"] or None,
                    helpful=bool(row["helpful"]),
                    note=row["note"],
                    created_at=str(row["created_at"]),
                )
            )
        return records

    def search(
        self,
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        normalized_tags = self._normalize_tags(tags)
        records = self._search_records(
            query=query,
            top_k=top_k,
            service_name=service_name,
            doc_types=doc_types,
            tags=normalized_tags,
        )
        return [
            KnowledgeRetrievalResult(
                document_id=record.document_id,
                title=record.title,
                doc_type=record.doc_type,
                text=chunk_text_value,
                score=score,
                service=record.service,
                tags=list(record.tags),
                source=record.source,
                chunk_index=chunk_index,
                metadata={
                    "backend": self.backend_name,
                    "chunk_count": record.chunk_count,
                    "indexed_at": record.indexed_at,
                    **record.metadata,
                },
            )
            for record, chunk_text_value, chunk_index, score in records
        ]

    def retrieve_by_context(
        self,
        incident_context: KnowledgeContext | Mapping[str, Any],
        top_k: int = 5,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        context = self._coerce_context(incident_context)
        query = format_context_for_query(
            service_name=context.service_name,
            severity=context.severity,
            symptom=context.symptom,
            metric_name=context.metric_name,
            metric_value=context.metric_value,
            threshold_value=context.threshold_value,
            deployment_summary=context.deployment_summary,
            service_profile_summary=context.service_profile_summary,
        )
        return self.search(
            query=query,
            top_k=top_k,
            service_name=context.service_name,
            doc_types=doc_types,
            tags=tags,
        )

    def retrieve_by_document_type(
        self,
        document_types: list[str],
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        return self.search(
            query=query,
            top_k=top_k,
            service_name=service_name,
            doc_types=document_types,
            tags=tags,
        )

    def retrieve_by_service(
        self,
        service_name: str,
        query: str,
        top_k: int = 5,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        return self.search(
            query=query,
            top_k=top_k,
            service_name=service_name,
            doc_types=doc_types,
            tags=tags,
        )

    def retrieve_by_tags(
        self,
        tags: list[str],
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        return self.search(
            query=query,
            top_k=top_k,
            service_name=service_name,
            doc_types=doc_types,
            tags=tags,
        )

    def _coerce_context(self, incident_context: KnowledgeContext | Mapping[str, Any]) -> KnowledgeContext:
        if isinstance(incident_context, KnowledgeContext):
            return incident_context
        return KnowledgeContext(
            service_name=str(incident_context.get("service_name", "")),
            severity=str(incident_context.get("severity", "")),
            symptom=str(incident_context.get("symptom", "")),
            metric_name=incident_context.get("metric_name"),
            metric_value=incident_context.get("metric_value"),
            threshold_value=incident_context.get("threshold_value"),
            deployment_summary=incident_context.get("deployment_summary"),
            service_profile_summary=incident_context.get("service_profile_summary"),
        )

    def _build_rca_match_explanation(
        self,
        context: KnowledgeContext,
        memory: RcaMemoryRecord,
        chunk_text_value: str,
    ) -> tuple[str, list[str]]:
        signals: list[str] = []
        if memory.service_name and memory.service_name == context.service_name:
            signals.append(f"service match: {memory.service_name}")
        if memory.severity and memory.severity.lower() == context.severity.lower():
            signals.append(f"severity match: {memory.severity}")

        symptom_hits = [
            symptom
            for symptom in memory.symptoms
            if symptom and symptom.lower() in context.symptom.lower()
        ]
        if symptom_hits:
            signals.append(f"symptom overlap: {', '.join(symptom_hits[:3])}")

        error_hits = [
            error
            for error in memory.related_errors
            if error and (error.lower() in context.symptom.lower() or error.lower() in chunk_text_value.lower())
        ]
        if error_hits:
            signals.append(f"related errors: {', '.join(error_hits[:3])}")

        dependency_hits = [
            dependency
            for dependency in memory.related_dependencies
            if dependency and dependency.lower() in chunk_text_value.lower()
        ]
        if dependency_hits:
            signals.append(f"dependency overlap: {', '.join(dependency_hits[:3])}")

        if not signals:
            signals.append("semantic similarity across the incident context and RCA content")

        explanation = "; ".join(signals)
        if memory.root_cause:
            explanation = f"{explanation}. Root cause: {memory.root_cause}"
        if memory.resolution:
            explanation = f"{explanation}. Resolution: {memory.resolution}"
        return explanation, signals


class DifyKnowledgeBackend:
    backend_name = "dify"

    def _not_implemented(self) -> None:
        raise NotImplementedError(
            "The Dify knowledge backend is reserved for a future V3 stage and is not implemented yet."
        )

    def add_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self._not_implemented()

    def list_documents(self, include_archived: bool = False) -> list[KnowledgeDocument]:
        self._not_implemented()

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        self._not_implemented()

    def update_document(self, document_id: str, **changes: Any) -> KnowledgeDocument:
        self._not_implemented()

    def delete_document(self, document_id: str) -> None:
        self._not_implemented()

    def archive_document(self, document_id: str) -> KnowledgeDocument:
        self._not_implemented()

    def reindex_document(self, document_id: str) -> None:
        self._not_implemented()

    def list_document_chunks(self, document_id: str) -> list[KnowledgeChunk]:
        self._not_implemented()

    def list_rca_memories(self, include_archived: bool = False) -> list[RcaMemoryRecord]:
        self._not_implemented()

    def get_rca_memory(self, rca_id: str) -> RcaMemoryRecord | None:
        self._not_implemented()

    def search_rca_memories(
        self,
        incident_context: KnowledgeContext | Mapping[str, Any],
        top_k: int = 5,
        tags: list[str] | None = None,
    ) -> list[RcaMemoryMatch]:
        self._not_implemented()

    def record_rca_feedback(
        self,
        rca_id: str,
        incident_id: str,
        helpful: bool,
        analysis_run_id: str | None = None,
        note: str | None = None,
    ) -> RcaFeedbackRecord:
        self._not_implemented()

    def list_rca_feedback(
        self,
        incident_id: str | None = None,
        analysis_run_id: str | None = None,
        rca_id: str | None = None,
    ) -> list[RcaFeedbackRecord]:
        self._not_implemented()

    def search(
        self,
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        self._not_implemented()

    def retrieve_by_context(
        self,
        incident_context: KnowledgeContext | Mapping[str, Any],
        top_k: int = 5,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        self._not_implemented()

    def retrieve_by_document_type(
        self,
        document_types: list[str],
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        self._not_implemented()

    def retrieve_by_service(
        self,
        service_name: str,
        query: str,
        top_k: int = 5,
        doc_types: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        self._not_implemented()

    def retrieve_by_tags(
        self,
        tags: list[str],
        query: str,
        top_k: int = 5,
        service_name: str | None = None,
        doc_types: list[str] | None = None,
    ) -> list[KnowledgeRetrievalResult]:
        self._not_implemented()


def create_knowledge_backend(
    backend_name: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> KnowledgeBackend:
    selected_backend = (backend_name or KNOWLEDGE_BACKEND).strip().lower()
    if selected_backend in {"local", "default"}:
        logger.info("Using persistent local knowledge backend")
        return LocalKnowledgeBackend(embedding_provider=embedding_provider)
    if selected_backend == "dify":
        logger.info("Using Dify knowledge backend")
        return DifyKnowledgeBackend()
    raise ValueError(f"Unknown knowledge backend: {selected_backend}")


def format_context_for_query(
    service_name: str,
    severity: str,
    symptom: str,
    metric_name: str | None,
    metric_value: str | None,
    threshold_value: str | None,
    deployment_summary: str | None,
    service_profile_summary: str | None = None,
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
    if service_profile_summary:
        parts.append(f"Service catalog context: {service_profile_summary}")
    parts.append("Need: relevant runbooks, similar RCAs, and remediation guidance")
    return "\n".join(parts)

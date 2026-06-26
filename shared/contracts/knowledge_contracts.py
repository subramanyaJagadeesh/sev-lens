from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    doc_type: str
    content: str
    service: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    archived: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeDocument":
        return cls(
            document_id=str(payload["document_id"]),
            title=str(payload["title"]),
            doc_type=str(payload["doc_type"]),
            content=str(payload.get("content", "")),
            service=payload.get("service"),
            tags=list(payload.get("tags", [])),
            source=payload.get("source"),
            archived=bool(payload.get("archived", False)),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class KnowledgeRetrievalResult:
    document_id: str
    title: str
    doc_type: str
    text: str
    score: float
    service: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeRetrievalResult":
        return cls(
            document_id=str(payload["document_id"]),
            title=str(payload["title"]),
            doc_type=str(payload["doc_type"]),
            text=str(payload.get("text", "")),
            score=float(payload.get("score", 0.0)),
            service=payload.get("service"),
            tags=list(payload.get("tags", [])),
            source=payload.get("source"),
            chunk_index=int(payload.get("chunk_index", 0)),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    title: str
    doc_type: str
    text: str
    chunk_index: int
    service: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KnowledgeChunk":
        return cls(
            chunk_id=str(payload["chunk_id"]),
            document_id=str(payload["document_id"]),
            title=str(payload["title"]),
            doc_type=str(payload["doc_type"]),
            text=str(payload.get("text", "")),
            chunk_index=int(payload.get("chunk_index", 0)),
            service=payload.get("service"),
            tags=list(payload.get("tags", [])),
            source=payload.get("source"),
            metadata=dict(payload.get("metadata", {})),
        )

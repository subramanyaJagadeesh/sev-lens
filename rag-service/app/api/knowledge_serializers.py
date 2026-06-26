from __future__ import annotations

from shared.contracts.knowledge_contracts import KnowledgeChunk, KnowledgeDocument, KnowledgeRetrievalResult

from ..schemas import KnowledgeChunkResponse, KnowledgeDocumentResponse, KnowledgeSearchResult


def serialize_knowledge_document(document: KnowledgeDocument) -> KnowledgeDocumentResponse:
    metadata = dict(document.metadata)
    return KnowledgeDocumentResponse(
        document_id=document.document_id,
        title=document.title,
        doc_type=document.doc_type,
        content=document.content,
        service=document.service,
        tags=list(document.tags),
        source=document.source,
        archived=document.archived,
        metadata=metadata,
        created_at=metadata.get("created_at"),
        updated_at=metadata.get("updated_at"),
        indexed_at=metadata.get("indexed_at"),
        chunk_count=int(metadata.get("chunk_count", 0) or 0),
        chunk_ids=[str(chunk_id) for chunk_id in metadata.get("chunk_ids", [])],
    )


def serialize_knowledge_chunk(chunk: KnowledgeChunk) -> KnowledgeChunkResponse:
    return KnowledgeChunkResponse(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        title=chunk.title,
        doc_type=chunk.doc_type,
        text=chunk.text,
        chunk_index=chunk.chunk_index,
        service=chunk.service,
        tags=list(chunk.tags),
        source=chunk.source,
        metadata=dict(chunk.metadata),
    )


def serialize_search_result(result: KnowledgeRetrievalResult) -> KnowledgeSearchResult:
    return KnowledgeSearchResult(
        document_id=result.document_id,
        title=result.title,
        doc_type=result.doc_type,
        text=result.text,
        score=result.score,
        service=result.service,
        tags=list(result.tags),
        source=result.source,
        chunk_index=result.chunk_index,
        metadata=dict(result.metadata),
    )

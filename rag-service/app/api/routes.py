from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from shared.contracts.knowledge_contracts import KnowledgeDocument

from ..core.runtime import get_runtime
from ..schemas import (
    AnalyzeIncidentRequest,
    AnalyzeIncidentResponse,
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdateRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResult,
    RcaMemoryDetailResponse,
    RcaMemoryFeedbackRequest,
    RcaMemoryFeedbackResponse,
    RcaMemoryMatchResponse,
    RcaMemoryResponse,
    RcaMemorySearchRequest,
)
from .knowledge_serializers import (
    serialize_knowledge_chunk,
    serialize_knowledge_document,
    serialize_search_result,
)
from .rca_serializers import serialize_rca_feedback, serialize_rca_memory, serialize_rca_match

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeIncidentResponse)
def analyze_incident(payload: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
    try:
        logger.info(
            "Received /analyze request incident_id=%s service=%s severity=%s",
            payload.incident_id,
            payload.service_name,
            payload.severity,
        )
        return get_runtime().analysis_engine.analyze(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Required mock data is missing") from exc


@router.get("/knowledge/documents", response_model=list[KnowledgeDocumentResponse])
def list_knowledge_documents(include_archived: bool = False) -> list[KnowledgeDocumentResponse]:
    runtime = get_runtime()
    return [
        serialize_knowledge_document(document)
        for document in runtime.knowledge_backend.list_documents(include_archived=include_archived)
    ]


@router.get("/knowledge/documents/{document_id}", response_model=KnowledgeDocumentDetailResponse)
def get_knowledge_document(document_id: str) -> KnowledgeDocumentDetailResponse:
    runtime = get_runtime()
    document = runtime.knowledge_backend.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Unknown knowledge document: {document_id}")
    chunks = runtime.knowledge_backend.list_document_chunks(document_id)
    return KnowledgeDocumentDetailResponse(
        document=serialize_knowledge_document(document),
        chunks=[serialize_knowledge_chunk(chunk) for chunk in chunks],
    )


@router.post("/knowledge/documents", response_model=KnowledgeDocumentResponse, status_code=201)
def create_knowledge_document(payload: KnowledgeDocumentCreateRequest) -> KnowledgeDocumentResponse:
    runtime = get_runtime()
    try:
        document = runtime.knowledge_backend.add_document(
            KnowledgeDocument(
                document_id=payload.document_id,
                title=payload.title,
                doc_type=payload.doc_type,
                content=payload.content,
                service=payload.service,
                tags=list(payload.tags),
                source=payload.source,
                metadata=dict(payload.metadata),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_knowledge_document(document)


@router.put("/knowledge/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def update_knowledge_document(
    document_id: str, payload: KnowledgeDocumentUpdateRequest
) -> KnowledgeDocumentResponse:
    runtime = get_runtime()
    try:
        document = runtime.knowledge_backend.update_document(
            document_id,
            **payload.model_dump(exclude_none=True),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return serialize_knowledge_document(document)


@router.post("/knowledge/documents/{document_id}/archive", response_model=KnowledgeDocumentResponse)
def archive_knowledge_document(document_id: str) -> KnowledgeDocumentResponse:
    runtime = get_runtime()
    try:
        document = runtime.knowledge_backend.archive_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return serialize_knowledge_document(document)


@router.post("/knowledge/documents/{document_id}/reindex", response_model=KnowledgeDocumentDetailResponse)
def reindex_knowledge_document(document_id: str) -> KnowledgeDocumentDetailResponse:
    runtime = get_runtime()
    try:
        runtime.knowledge_backend.reindex_document(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    document = runtime.knowledge_backend.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Unknown knowledge document: {document_id}")
    chunks = runtime.knowledge_backend.list_document_chunks(document_id)
    return KnowledgeDocumentDetailResponse(
        document=serialize_knowledge_document(document),
        chunks=[serialize_knowledge_chunk(chunk) for chunk in chunks],
    )


@router.post("/knowledge/search", response_model=list[KnowledgeSearchResult])
def search_knowledge(payload: KnowledgeSearchRequest) -> list[KnowledgeSearchResult]:
    runtime = get_runtime()
    return [
        serialize_search_result(result)
        for result in runtime.knowledge_backend.search(
            query=payload.query,
            top_k=payload.top_k,
            service_name=payload.service_name,
            doc_types=payload.doc_types,
            tags=payload.tags,
        )
    ]


@router.get("/rca-memory", response_model=list[RcaMemoryResponse])
def list_rca_memories(include_archived: bool = False) -> list[RcaMemoryResponse]:
    runtime = get_runtime()
    return [serialize_rca_memory(record) for record in runtime.knowledge_backend.list_rca_memories(include_archived=include_archived)]


@router.get("/rca-memory/{rca_id}", response_model=RcaMemoryDetailResponse)
def get_rca_memory(rca_id: str) -> RcaMemoryDetailResponse:
    runtime = get_runtime()
    memory = runtime.knowledge_backend.get_rca_memory(rca_id)
    if memory is None:
        raise HTTPException(status_code=404, detail=f"Unknown RCA memory: {rca_id}")
    feedback = runtime.knowledge_backend.list_rca_feedback(rca_id=rca_id)
    return RcaMemoryDetailResponse(
        memory=serialize_rca_memory(memory),
        feedback=[serialize_rca_feedback(record) for record in feedback],
    )


@router.post("/rca-memory/search", response_model=list[RcaMemoryMatchResponse])
def search_rca_memory(payload: RcaMemorySearchRequest) -> list[RcaMemoryMatchResponse]:
    runtime = get_runtime()
    matches = runtime.knowledge_backend.search_rca_memories(
        incident_context=payload.model_dump(exclude={"top_k", "tags"}),
        top_k=payload.top_k,
        tags=payload.tags,
    )
    return [serialize_rca_match(match) for match in matches]


@router.post("/rca-memory/feedback", response_model=RcaMemoryFeedbackResponse, status_code=201)
def record_rca_feedback(payload: RcaMemoryFeedbackRequest) -> RcaMemoryFeedbackResponse:
    runtime = get_runtime()
    record = runtime.knowledge_backend.record_rca_feedback(
        rca_id=payload.rca_id,
        incident_id=payload.incident_id,
        analysis_run_id=payload.analysis_run_id,
        helpful=payload.helpful,
        note=payload.note,
    )
    return serialize_rca_feedback(record)


@router.get("/rca-memory/feedback", response_model=list[RcaMemoryFeedbackResponse])
def list_rca_feedback(
    incident_id: str | None = None,
    analysis_run_id: str | None = None,
    rca_id: str | None = None,
) -> list[RcaMemoryFeedbackResponse]:
    runtime = get_runtime()
    return [
        serialize_rca_feedback(record)
        for record in runtime.knowledge_backend.list_rca_feedback(
            incident_id=incident_id,
            analysis_run_id=analysis_run_id,
            rca_id=rca_id,
        )
    ]

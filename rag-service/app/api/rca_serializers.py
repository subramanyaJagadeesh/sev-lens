from __future__ import annotations

from shared.contracts.rca_contracts import RcaFeedbackRecord, RcaMemoryMatch, RcaMemoryRecord

from ..schemas import (
    RcaMemoryFeedbackResponse,
    RcaMemoryMatchResponse,
    RcaMemoryResponse,
)


def serialize_rca_memory(record: RcaMemoryRecord) -> RcaMemoryResponse:
    return RcaMemoryResponse(
        rca_id=record.rca_id,
        document_id=record.document_id,
        title=record.title,
        service_name=record.service_name,
        severity=record.severity,
        symptoms=list(record.symptoms),
        root_cause=record.root_cause,
        resolution=record.resolution,
        prevention_items=list(record.prevention_items),
        related_errors=list(record.related_errors),
        related_dependencies=list(record.related_dependencies),
        incident_date=record.incident_date,
        source=record.source,
        tags=list(record.tags),
        archived=record.archived,
        metadata=dict(record.metadata),
        helpful_count=record.helpful_count,
        not_helpful_count=record.not_helpful_count,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def serialize_rca_match(match: RcaMemoryMatch) -> RcaMemoryMatchResponse:
    return RcaMemoryMatchResponse(
        rca_id=match.rca_id,
        document_id=match.document_id,
        title=match.title,
        service_name=match.service_name,
        severity=match.severity,
        score=match.score,
        match_explanation=match.match_explanation,
        matched_signals=list(match.matched_signals),
        symptoms=list(match.symptoms),
        root_cause=match.root_cause,
        resolution=match.resolution,
        prevention_items=list(match.prevention_items),
        related_errors=list(match.related_errors),
        related_dependencies=list(match.related_dependencies),
        incident_date=match.incident_date,
        source=match.source,
        helpful_count=match.helpful_count,
        not_helpful_count=match.not_helpful_count,
        metadata=dict(match.metadata),
    )


def serialize_rca_feedback(record: RcaFeedbackRecord) -> RcaMemoryFeedbackResponse:
    return RcaMemoryFeedbackResponse(
        feedback_id=record.feedback_id,
        rca_id=record.rca_id,
        incident_id=record.incident_id,
        analysis_run_id=record.analysis_run_id,
        helpful=record.helpful,
        note=record.note,
        created_at=record.created_at,
    )

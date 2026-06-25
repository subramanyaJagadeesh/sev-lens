from __future__ import annotations

from dataclasses import dataclass

from ..config import ENABLE_SYNC_ANALYSIS_FALLBACK
from ..events import EventBus
from ..queue import RedisAnalysisQueuePublisher
from ..repository import IncidentRepository
from ..result_consumer import RedisAnalysisResultConsumer
from ..service import IncidentService


@dataclass(slots=True)
class IncidentRuntime:
    repository: IncidentRepository
    event_bus: EventBus
    analysis_queue: RedisAnalysisQueuePublisher
    incident_service: IncidentService
    result_consumer: RedisAnalysisResultConsumer


def build_runtime() -> IncidentRuntime:
    repository = IncidentRepository()
    event_bus = EventBus()
    analysis_queue = RedisAnalysisQueuePublisher()
    incident_service = IncidentService(repository, event_bus, sync_fallback_enabled=ENABLE_SYNC_ANALYSIS_FALLBACK)
    result_consumer = RedisAnalysisResultConsumer(incident_service, event_bus)
    return IncidentRuntime(
        repository=repository,
        event_bus=event_bus,
        analysis_queue=analysis_queue,
        incident_service=incident_service,
        result_consumer=result_consumer,
    )


_RUNTIME = build_runtime()


def get_runtime() -> IncidentRuntime:
    return _RUNTIME

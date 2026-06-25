from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from shared.contracts.analysis_contracts import AnalysisRequestEnvelope

from .config import ANALYSIS_REQUEST_STREAM, REDIS_URL

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueuePublishResult:
    stream: str
    entry_id: str


class RedisAnalysisQueuePublisher:
    def __init__(self, redis_url: str = REDIS_URL, stream_name: str = ANALYSIS_REQUEST_STREAM) -> None:
        self.redis_url = redis_url
        self.stream_name = stream_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from redis import Redis
            except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError("redis package is required to publish analysis jobs") from exc
            self._client = Redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def publish(self, request: AnalysisRequestEnvelope) -> QueuePublishResult:
        payload = request.to_dict()
        client = self._get_client()
        entry_id = client.xadd(
            self.stream_name,
            {
                "event_type": "ANALYSIS_REQUESTED",
                "incident_id": request.incident_id,
                "scenario_id": request.scenario_id,
                "correlation_id": request.correlation_id,
                "source": request.source,
                "payload": json.dumps(payload),
            },
        )
        logger.info(
            "Published analysis request to stream=%s entry_id=%s incident_id=%s",
            self.stream_name,
            entry_id,
            request.incident_id,
        )
        return QueuePublishResult(stream=self.stream_name, entry_id=entry_id)

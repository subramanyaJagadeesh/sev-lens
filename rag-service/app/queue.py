from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from shared.contracts.analysis_contracts import AnalysisRequestEnvelope, AnalysisResultEnvelope

from .analysis import AnalysisEngine
from .config import (
    ANALYSIS_REQUEST_CONSUMER,
    ANALYSIS_REQUEST_GROUP,
    ANALYSIS_REQUEST_STREAM,
    ANALYSIS_RESULT_STREAM,
    REDIS_URL,
)
from .schemas import AnalyzeIncidentRequest

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QueuePublishResult:
    stream: str
    entry_id: str


class RedisAnalysisResultPublisher:
    def __init__(self, redis_url: str = REDIS_URL, stream_name: str = ANALYSIS_RESULT_STREAM) -> None:
        self.redis_url = redis_url
        self.stream_name = stream_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from redis.asyncio import Redis
            except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError("redis package is required to publish analysis results") from exc
            self._client = Redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def publish(self, result: AnalysisResultEnvelope) -> QueuePublishResult:
        client = self._get_client()
        entry_id = await client.xadd(self.stream_name, result.to_stream_message())
        logger.info(
            "Published analysis result to stream=%s entry_id=%s incident_id=%s status=%s",
            self.stream_name,
            entry_id,
            result.incident_id,
            result.analysis_status,
        )
        return QueuePublishResult(stream=self.stream_name, entry_id=entry_id)


class RedisAnalysisWorker:
    def __init__(
        self,
        analysis_engine: AnalysisEngine | None = None,
        redis_url: str = REDIS_URL,
        request_stream: str = ANALYSIS_REQUEST_STREAM,
        request_group: str = ANALYSIS_REQUEST_GROUP,
        request_consumer: str = ANALYSIS_REQUEST_CONSUMER,
        result_publisher: RedisAnalysisResultPublisher | None = None,
    ) -> None:
        self.analysis_engine = analysis_engine or AnalysisEngine()
        self.redis_url = redis_url
        self.request_stream = request_stream
        self.request_group = request_group
        self.request_consumer = request_consumer
        self.result_publisher = result_publisher or RedisAnalysisResultPublisher(redis_url)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from redis.asyncio import Redis
            except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError("redis package is required to consume analysis requests") from exc
            self._client = Redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def ensure_group(self) -> None:
        client = self._get_client()
        try:
            await client.xgroup_create(self.request_stream, self.request_group, id="0", mkstream=True)
            logger.info("Created Redis request consumer group=%s stream=%s", self.request_group, self.request_stream)
        except Exception as exc:  # noqa: BLE001
            if "BUSYGROUP" not in str(exc):
                raise

    async def run_forever(self) -> None:
        while True:
            try:
                await self.ensure_group()
                client = self._get_client()
                logger.info(
                    "Starting analysis worker group=%s consumer=%s stream=%s",
                    self.request_group,
                    self.request_consumer,
                    self.request_stream,
                )
                while True:
                    messages = await client.xreadgroup(
                        groupname=self.request_group,
                        consumername=self.request_consumer,
                        streams={self.request_stream: ">"},
                        count=10,
                        block=1000,
                    )
                    for _, stream_messages in messages:
                        for stream_id, fields in stream_messages:
                            await self._handle_message(client, stream_id, fields)
            except asyncio.CancelledError:
                logger.info("Stopping analysis worker group=%s consumer=%s", self.request_group, self.request_consumer)
                raise
            except Exception:
                logger.exception("Analysis worker loop error; retrying")
                await asyncio.sleep(2)

    async def _handle_message(self, client, stream_id: str, fields: dict[str, Any]) -> None:
        incident_id = fields.get("incident_id")
        try:
            request = AnalysisRequestEnvelope.from_stream_message(fields)
            logger.info("Processing analysis request incident_id=%s stream_id=%s", request.incident_id, stream_id)

            await self.result_publisher.publish(
                AnalysisResultEnvelope(
                    incident_id=request.incident_id,
                    analysis_status="ANALYZING",
                    analysis_events=[
                        {
                            "event_type": "ANALYSIS_STARTED",
                            "message": "Analysis started for mock incident",
                            "payload": {"scenario_id": request.scenario_id, "source": request.source},
                        }
                    ],
                )
            )

            analysis_request = AnalyzeIncidentRequest(
                incident_id=request.incident_id,
                scenario_id=request.scenario_id,
                service_name=request.service_name,
                severity=request.severity,
                symptom=request.symptom,
                metric_name=request.metric_name,
                metric_value=request.metric_value,
                threshold_value=request.threshold_value,
            )
            analysis_response = await asyncio.to_thread(self.analysis_engine.analyze, analysis_request)
            await self.result_publisher.publish(
                AnalysisResultEnvelope(
                    incident_id=request.incident_id,
                    analysis_status="RECOMMENDATION_READY",
                    recommendation=analysis_response.recommendation.model_dump(mode="json"),
                    analysis_events=[event.model_dump(mode="json") for event in analysis_response.analysis_events],
                )
            )
            await client.xack(self.request_stream, self.request_group, stream_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Analysis worker failed stream_id=%s incident_id=%s", stream_id, incident_id)
            if incident_id:
                try:
                    await self.result_publisher.publish(
                        AnalysisResultEnvelope(
                            incident_id=str(incident_id),
                            analysis_status="FAILED",
                            analysis_events=[
                                {
                                    "event_type": "ANALYSIS_FAILED",
                                    "message": "Analysis failed while processing queued request",
                                    "payload": {"error": str(exc), "stream_id": stream_id},
                                }
                            ],
                            error=str(exc),
                        )
                    )
                except Exception:
                    logger.exception("Failed to publish analysis failure incident_id=%s", incident_id)
            await client.xack(self.request_stream, self.request_group, stream_id)

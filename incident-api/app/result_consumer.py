from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from shared.contracts.analysis_contracts import AnalysisResultEnvelope

from .config import ANALYSIS_RESULT_CONSUMER, ANALYSIS_RESULT_GROUP, ANALYSIS_RESULT_STREAM, REDIS_URL
from .events import EventBus
from .service import IncidentService

logger = logging.getLogger(__name__)


class RedisAnalysisResultConsumer:
    def __init__(
        self,
        incident_service: IncidentService,
        event_bus: EventBus,
        redis_url: str = REDIS_URL,
        stream_name: str = ANALYSIS_RESULT_STREAM,
        group_name: str = ANALYSIS_RESULT_GROUP,
        consumer_name: str = ANALYSIS_RESULT_CONSUMER,
    ) -> None:
        self.incident_service = incident_service
        self.event_bus = event_bus
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from redis.asyncio import Redis
            except ModuleNotFoundError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError("redis package is required to consume analysis results") from exc
            self._client = Redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def ensure_group(self) -> None:
        client = self._get_client()
        try:
            await client.xgroup_create(self.stream_name, self.group_name, id="0", mkstream=True)
            logger.info("Created Redis result consumer group=%s stream=%s", self.group_name, self.stream_name)
        except Exception as exc:  # noqa: BLE001
            if "BUSYGROUP" not in str(exc):
                raise

    async def run_forever(self) -> None:
        while True:
            try:
                await self.ensure_group()
                client = self._get_client()
                logger.info(
                    "Starting result consumer group=%s consumer=%s stream=%s",
                    self.group_name,
                    self.consumer_name,
                    self.stream_name,
                )
                while True:
                    messages = await client.xreadgroup(
                        groupname=self.group_name,
                        consumername=self.consumer_name,
                        streams={self.stream_name: ">"},
                        count=10,
                        block=1000,
                    )
                    for _, stream_messages in messages:
                        for stream_id, fields in stream_messages:
                            await self._handle_message(client, stream_id, fields)
            except asyncio.CancelledError:
                logger.info("Stopping result consumer group=%s consumer=%s", self.group_name, self.consumer_name)
                raise
            except Exception:
                logger.exception("Result consumer loop error; retrying")
                await asyncio.sleep(2)

    async def _handle_message(self, client, stream_id: str, fields: dict[str, Any]) -> None:
        ack_message = False
        try:
            result = AnalysisResultEnvelope.from_stream_message(fields)
            logger.info(
                "Applying analysis result incident_id=%s status=%s stream_id=%s",
                result.incident_id,
                result.analysis_status,
                stream_id,
            )
            applied = self.incident_service.apply_analysis_result(result)
            if applied is None:
                logger.warning("Dropping analysis result for missing incident_id=%s", result.incident_id)
            else:
                for event in applied["events"]:
                    await self.event_bus.publish(event)
            ack_message = True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to apply analysis result stream_id=%s payload=%s", stream_id, fields)
            raise
        finally:
            if ack_message:
                await client.xack(self.stream_name, self.group_name, stream_id)

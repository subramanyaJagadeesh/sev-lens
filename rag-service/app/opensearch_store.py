from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from shared.contracts.incident_contracts import fetch_incident_scenarios

from .config import (
    OPENSEARCH_INDEX,
    OPENSEARCH_PASSWORD,
    OPENSEARCH_TIMEOUT_SECONDS,
    OPENSEARCH_URL,
    OPENSEARCH_USERNAME,
)
from .data_loader import load_scenario_seed
from .schemas import LogEvidenceRecord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpenSearchDocument:
    scenario_id: str
    service_name: str
    severity: str
    time_window: str
    summary: str
    top_errors: list[dict[str, Any]]
    sample_messages: list[str]
    source: str


class OpenSearchLogStore:
    def __init__(
        self,
        base_url: str = OPENSEARCH_URL,
        index_name: str = OPENSEARCH_INDEX,
        username: str | None = OPENSEARCH_USERNAME,
        password: str | None = OPENSEARCH_PASSWORD,
        timeout_seconds: float = OPENSEARCH_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.index_name = index_name
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self._ready = False
        self._seeded = False
        self._seeded_windows: dict[str, str] = {}

    def _auth_header(self) -> str | None:
        if not self.username or self.password is None:
            return None
        token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any] | None:
        url = f"{self.base_url}/{path.lstrip('/')}"
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"}
        auth_header = self._auth_header()
        if auth_header:
            headers["Authorization"] = auth_header
        request = Request(url, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except HTTPError as exc:
            if exc.code == 404:
                raise FileNotFoundError(url) from exc
            raise RuntimeError(f"OpenSearch request failed: {method} {path} -> {exc.code}") from exc
        except URLError as exc:  # pragma: no cover - network failure path
            raise RuntimeError(f"OpenSearch request failed: {method} {path}") from exc

    def ensure_index(self) -> None:
        if self._ready:
            return
        try:
            self._request("HEAD", self.index_name)
            logger.info("OpenSearch index already exists: %s", self.index_name)
        except FileNotFoundError:
            logger.info("Creating OpenSearch index: %s", self.index_name)
            self._request(
                "PUT",
                self.index_name,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                    },
                    "mappings": {
                        "properties": {
                            "scenario_id": {"type": "keyword"},
                            "service_name": {"type": "keyword"},
                            "severity": {"type": "keyword"},
                            "time_window": {"type": "keyword"},
                            "summary": {"type": "text"},
                            "top_errors": {"type": "object", "enabled": True},
                            "sample_messages": {"type": "text"},
                            "source": {"type": "keyword"},
                        }
                    },
                },
            )
        self._ready = True

    def _build_document(self, scenario: dict[str, Any], logs: dict[str, Any]) -> OpenSearchDocument:
        top_errors = list(logs.get("top_errors", []))
        sample_messages = [str(message) for message in logs.get("sample_messages", [])]
        time_window = str(logs.get("window", "last_15_minutes"))
        error_summary = ", ".join(
            f"{error.get('error', 'unknown')} ({error.get('count', 0)})" for error in top_errors[:3]
        )
        message_summary = "; ".join(sample_messages[:3])
        summary = (
            f"{scenario['service_name']} experienced {error_summary or 'elevated log noise'} during {time_window}."
        )
        if message_summary:
            summary = f"{summary} Sample messages: {message_summary}."
        return OpenSearchDocument(
            scenario_id=scenario["scenario_id"],
            service_name=scenario["service_name"],
            severity=scenario["severity"],
            time_window=time_window,
            summary=summary,
            top_errors=top_errors,
            sample_messages=sample_messages,
            source=str(scenario.get("logs", "")),
        )

    def ensure_seeded(self) -> None:
        if self._seeded:
            return
        self.ensure_index()
        for scenario in fetch_incident_scenarios():
            scenario_path = scenario.get("scenario_path")
            if not scenario_path:
                continue
            seeded = load_scenario_seed(str(scenario_path))
            scenario_record = seeded["scenario"]
            logs = seeded["logs"]
            document = self._build_document(scenario_record, logs)
            self._index_document(document)
            self._seeded_windows[document.scenario_id] = document.time_window
        logger.info("Seeded OpenSearch log evidence for %s scenarios", len(self._seeded_windows))
        self._seeded = True

    def _index_document(self, document: OpenSearchDocument) -> None:
        self._request(
            "PUT",
            f"{self.index_name}/_doc/{document.scenario_id}?refresh=wait_for",
            body={
                "scenario_id": document.scenario_id,
                "service_name": document.service_name,
                "severity": document.severity,
                "time_window": document.time_window,
                "summary": document.summary,
                "top_errors": document.top_errors,
                "sample_messages": document.sample_messages,
                "source": document.source,
            },
        )

    def get_time_window_for_scenario(self, scenario_id: str) -> str | None:
        return self._seeded_windows.get(scenario_id)

    def search(self, service_name: str, scenario_id: str, time_window: str | None = None, top_k: int = 3) -> list[LogEvidenceRecord]:
        self.ensure_seeded()
        query_window = time_window or self.get_time_window_for_scenario(scenario_id)
        must_clauses: list[dict[str, Any]] = [
            {"term": {"service_name": service_name}},
            {"term": {"scenario_id": scenario_id}},
        ]
        if query_window:
            must_clauses.append({"term": {"time_window": query_window}})

        response = self._request(
            "POST",
            f"{self.index_name}/_search",
            body={
                "size": top_k,
                "query": {"bool": {"must": must_clauses}},
                "sort": [{"_score": {"order": "desc"}}],
            },
        )
        hits = (response or {}).get("hits", {}).get("hits", [])
        if not hits and query_window:
            response = self._request(
                "POST",
                f"{self.index_name}/_search",
                body={
                    "size": top_k,
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"service_name": service_name}},
                                {"term": {"scenario_id": scenario_id}},
                            ]
                        }
                    },
                    "sort": [{"_score": {"order": "desc"}}],
                },
            )
            hits = (response or {}).get("hits", {}).get("hits", [])

        evidence: list[LogEvidenceRecord] = []
        for hit in hits[:top_k]:
            source = hit.get("_source", {})
            evidence.append(
                LogEvidenceRecord(
                    scenario_id=str(source.get("scenario_id", scenario_id)),
                    service_name=str(source.get("service_name", service_name)),
                    time_window=str(source.get("time_window", query_window or "last_15_minutes")),
                    summary=str(source.get("summary", "")),
                    top_errors=list(source.get("top_errors", [])),
                    sample_messages=[str(message) for message in source.get("sample_messages", [])],
                    source=str(source.get("source", "")),
                    score=float(hit.get("_score") or 1.0),
                )
            )
        return evidence

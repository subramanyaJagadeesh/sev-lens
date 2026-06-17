from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DOCS_DIR, MOCK_DATA_DIR


@dataclass(frozen=True)
class LoadedDocument:
    source: str
    title: str
    doc_type: str
    service: str | None
    tags: list[str]
    text: str


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def load_logs(service_name: str) -> dict[str, Any] | None:
    for filename in (f"{service_name}-logs.json", f"{service_name}.json"):
        path = MOCK_DATA_DIR / "logs" / filename
        if path.exists():
            return _load_json(path)
    return None


def load_metrics(service_name: str) -> dict[str, Any] | None:
    for filename in (f"{service_name}-metrics.json", f"{service_name}.json"):
        path = MOCK_DATA_DIR / "metrics" / filename
        if path.exists():
            return _load_json(path)
    return None


def load_recent_deployments(service_name: str) -> list[dict[str, Any]]:
    path = MOCK_DATA_DIR / "deployments" / "deployments.json"
    deployments = _load_json(path) if path.exists() else []
    return [deployment for deployment in deployments if deployment.get("service") == service_name]


def load_service_metadata(service_name: str) -> dict[str, Any] | None:
    path = MOCK_DATA_DIR / "services" / "service-catalog.json"
    if not path.exists():
        return None
    services = _load_json(path)
    for service in services:
        if service.get("service_name") == service_name:
            return service
    return None


def load_markdown_documents() -> list[LoadedDocument]:
    documents: list[LoadedDocument] = []
    for directory, doc_type in ((DOCS_DIR / "runbooks", "runbook"), (DOCS_DIR / "rcas", "rca")):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else path.stem
            service = "notification-service" if "notification" in path.name or "kafka" in path.name else None
            tags = path.stem.replace("-", " ").split()
            documents.append(
                LoadedDocument(
                    source=str(path),
                    title=title or path.stem,
                    doc_type=doc_type,
                    service=service,
                    tags=tags,
                    text=text,
                )
            )
    return documents


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks

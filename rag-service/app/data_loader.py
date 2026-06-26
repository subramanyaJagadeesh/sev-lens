from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DOCS_DIR, MOCK_DATA_DIR, PROJECT_ROOT


@dataclass(frozen=True)
class LoadedDocument:
    document_id: str
    source: str
    title: str
    doc_type: str
    service: str | None
    tags: list[str]
    text: str
    metadata: dict[str, Any]


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


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
    def slugify(value: str) -> str:
        return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")

    def load_sidecar_metadata(path: Path) -> dict[str, Any]:
        sidecar_path = path.with_suffix(".json")
        if not sidecar_path.exists():
            return {}
        return _load_json(sidecar_path)

    def detect_doc_type(path: Path) -> str:
        folder = path.parent.name.lower()
        if folder == "runbooks":
            return "runbook"
        if folder == "rcas":
            return "rca"
        if folder == "service-docs":
            return "service_doc"
        if folder == "architecture-notes":
            return "architecture_note"
        if folder == "troubleshooting":
            return "troubleshooting"
        if folder == "known-errors":
            return "known_error"
        if folder == "sops":
            return "sop"
        if folder == "escalation-policies":
            return "escalation_policy"
        return folder.replace("-", "_")

    def detect_service(path: Path) -> str | None:
        lowered = " ".join((path.stem, *path.parts)).lower()
        if "notification" in lowered or "kafka" in lowered:
            return "notification-service"
        if "database" in lowered or "connection" in lowered:
            return "database-service"
        if "gateway" in lowered:
            return "api-gateway"
        if "worker" in lowered or "queue" in lowered:
            return "worker-queue"
        return None

    def detect_tags(path: Path) -> list[str]:
        tags = [part.replace("-", " ") for part in path.parts if part not in {"docs", "knowledge"}]
        tags.append(path.stem.replace("-", " "))
        return sorted({tag for tag in tags if tag})

    documents: list[LoadedDocument] = []
    for directory in (DOCS_DIR / "runbooks", DOCS_DIR / "rcas", DOCS_DIR / "knowledge"):
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.md")):
            if path.name.startswith("v2-"):
                continue
            text = path.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else path.stem
            doc_type = detect_doc_type(path)
            metadata = load_sidecar_metadata(path) if doc_type == "rca" else {}
            documents.append(
                LoadedDocument(
                    document_id=slugify(f"{doc_type}-{path.stem}"),
                    source=str(path),
                    title=title or path.stem,
                    doc_type=doc_type,
                    service=detect_service(path),
                    tags=detect_tags(path),
                    text=text,
                    metadata=metadata,
                )
            )
    return documents


def load_scenario_seed(scenario_path: str) -> dict[str, Any]:
    path = PROJECT_ROOT / scenario_path
    if not path.exists():
        raise FileNotFoundError(path)
    scenario = _load_json(path)
    log_path = PROJECT_ROOT / str(scenario["logs"])
    if not log_path.exists():
        raise FileNotFoundError(log_path)
    return {
        "scenario": scenario,
        "logs": _load_json(log_path),
    }


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

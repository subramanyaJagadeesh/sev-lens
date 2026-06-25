from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
SHARED_DIR = PROJECT_ROOT / "shared"
DOCS_DIR = PROJECT_ROOT / "docs"
MOCK_DATA_DIR = SHARED_DIR / "mock-data"


def _load_local_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


_load_local_env_file(BASE_DIR / ".env")

LLM_PROVIDER = os.getenv("RAG_LLM_PROVIDER", "ollama").lower()
LLM_BASE_URL = os.getenv(
    "RAG_LLM_BASE_URL",
    "http://localhost:11434/api" if LLM_PROVIDER == "ollama" else "http://localhost:8000/v1",
)
LLM_API_KEY = os.getenv("RAG_LLM_API_KEY", "ollama" if LLM_PROVIDER == "ollama" else "")
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "qwen3.5:4b" if LLM_PROVIDER == "ollama" else "gpt-4.1-mini")
LLM_TIMEOUT_SECONDS = float(os.getenv("RAG_LLM_TIMEOUT_SECONDS", "300"))
REDIS_URL = os.getenv("SEVLENS_REDIS_URL", "redis://localhost:6379/0")
ANALYSIS_REQUEST_STREAM = os.getenv("SEVLENS_ANALYSIS_REQUEST_STREAM", "sevlens:analysis:requests")
ANALYSIS_REQUEST_GROUP = os.getenv("SEVLENS_ANALYSIS_REQUEST_GROUP", "sevlens:analysis:requests:rag-worker")
ANALYSIS_REQUEST_CONSUMER = os.getenv("SEVLENS_ANALYSIS_REQUEST_CONSUMER", "rag-worker-1")
ANALYSIS_RESULT_STREAM = os.getenv("SEVLENS_ANALYSIS_RESULT_STREAM", "sevlens:analysis:results")
OPENSEARCH_URL = os.getenv("SEVLENS_OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_INDEX = os.getenv("SEVLENS_OPENSEARCH_INDEX", "sevlens-logs")
OPENSEARCH_USERNAME = os.getenv("SEVLENS_OPENSEARCH_USERNAME", "admin")
OPENSEARCH_PASSWORD = os.getenv("SEVLENS_OPENSEARCH_PASSWORD", "admin")
OPENSEARCH_TIMEOUT_SECONDS = float(os.getenv("SEVLENS_OPENSEARCH_TIMEOUT_SECONDS", "10"))

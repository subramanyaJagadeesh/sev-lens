from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.runtime import get_runtime
from .routes import router

LOG_LEVEL = os.getenv("SEVLENS_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger().setLevel(LOG_LEVEL)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="SevLens RAG Service")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("SEVLENS_CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    runtime = get_runtime()
    logger.info(
        "RAG config resolved provider=%s base_url=%s model=%s timeout_seconds=%s",
        os.getenv("RAG_LLM_PROVIDER", "ollama"),
        os.getenv("RAG_LLM_BASE_URL", "http://localhost:11434/api"),
        os.getenv("RAG_LLM_MODEL", "qwen3.5:4b"),
        os.getenv("RAG_LLM_TIMEOUT_SECONDS", "300"),
    )

    @app.on_event("startup")
    def startup_seed_opensearch() -> None:
        runtime.analysis_engine.ensure_log_store_ready()
        logger.info("OpenSearch log store seeded and ready")

    app.include_router(router)
    return app


app = create_app()

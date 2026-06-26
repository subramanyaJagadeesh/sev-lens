from __future__ import annotations

from dataclasses import dataclass

from ..analysis import AnalysisEngine
from ..config import EMBEDDING_PROVIDER, KNOWLEDGE_BACKEND
from ..embedding_provider import EmbeddingProvider, create_embedding_provider
from ..knowledge_backend import KnowledgeBackend, create_knowledge_backend


@dataclass(slots=True)
class RagRuntime:
    embedding_provider: EmbeddingProvider
    knowledge_backend: KnowledgeBackend
    analysis_engine: AnalysisEngine


_EMBEDDING_PROVIDER = create_embedding_provider(EMBEDDING_PROVIDER)
_KNOWLEDGE_BACKEND = create_knowledge_backend(
    backend_name=KNOWLEDGE_BACKEND,
    embedding_provider=_EMBEDDING_PROVIDER,
)
_RUNTIME = RagRuntime(
    embedding_provider=_EMBEDDING_PROVIDER,
    knowledge_backend=_KNOWLEDGE_BACKEND,
    analysis_engine=AnalysisEngine(knowledge_backend=_KNOWLEDGE_BACKEND),
)


def get_runtime() -> RagRuntime:
    return _RUNTIME

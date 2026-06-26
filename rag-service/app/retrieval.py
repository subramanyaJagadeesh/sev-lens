from __future__ import annotations

from .knowledge_backend import (
    DifyKnowledgeBackend,
    KnowledgeBackend,
    KnowledgeContext,
    LocalKnowledgeBackend,
    create_knowledge_backend,
    format_context_for_query,
)

KnowledgeBase = LocalKnowledgeBackend

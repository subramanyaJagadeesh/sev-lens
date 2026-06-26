from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol


class EmbeddingProvider(Protocol):
    provider_name: str

    def embed_text(self, text: str) -> list[float]: ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


@dataclass(slots=True)
class HashingEmbeddingProvider:
    dimensions: int = 128
    provider_name: str = "hashing"

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (len(token) / 10.0)
            vector[bucket] += sign * weight
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def create_embedding_provider(provider_name: str = "hashing") -> EmbeddingProvider:
    selected_provider = provider_name.strip().lower()
    if selected_provider in {"hashing", "local", "default"}:
        return HashingEmbeddingProvider()
    raise ValueError(f"Unknown embedding provider: {provider_name}")

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER, LLM_TIMEOUT_SECONDS


@dataclass(frozen=True)
class LLMResult:
    raw_text: str
    parsed_json: dict[str, Any]


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        base_url: str = LLM_BASE_URL,
        api_key: str = LLM_API_KEY,
        model: str = LLM_MODEL,
        timeout_seconds: float = LLM_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.provider = LLM_PROVIDER
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        if self.provider != "ollama" and not self.api_key:
            raise RuntimeError(
                "RAG_LLM_API_KEY is required for the Stage 3 LLM call. "
                "Set an OpenAI-compatible endpoint and key before running /analyze."
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        if self.provider == "ollama":
            payload["stream"] = False
            payload["format"] = "json"
            request_url = f"{self.base_url.rstrip('/')}/chat"
        else:
            payload["response_format"] = {"type": "json_object"}
            request_url = f"{self.base_url.rstrip('/')}/chat/completions"
        request = urllib.request.Request(
            request_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
            },
            method="POST",
        )

        request_started_at = time.perf_counter()
        self.logger.info(
            "Sending LLM request provider=%s model=%s url=%s prompt_chars=%s timeout_seconds=%s",
            self.provider,
            self.model,
            request_url,
            len(user_prompt),
            self.timeout_seconds,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - external dependency path
            error_body = exc.read().decode("utf-8", errors="replace").strip()
            detail = f"LLM request failed with status {exc.code}"
            if error_body:
                detail = f"{detail}: {error_body}"
            if self.provider == "ollama" and exc.code == 404:
                detail = (
                    f"{detail}. If you are using Ollama, confirm the model exists and is pulled, "
                    f"and that RAG_LLM_BASE_URL points at http://localhost:11434/api."
                )
            raise RuntimeError(detail) from exc
        except urllib.error.URLError as exc:  # pragma: no cover - external dependency path
            raise RuntimeError(f"LLM request failed: {exc.reason}") from exc

        response_json = json.loads(raw_response)
        if self.provider == "ollama":
            content = response_json["message"]["content"]
        else:
            content = response_json["choices"][0]["message"]["content"]
        self.logger.info(
            "LLM response received provider=%s model=%s duration_seconds=%.2f response_chars=%s",
            self.provider,
            self.model,
            time.perf_counter() - request_started_at,
            len(content),
        )
        parsed = json.loads(content)
        return LLMResult(raw_text=content, parsed_json=parsed)

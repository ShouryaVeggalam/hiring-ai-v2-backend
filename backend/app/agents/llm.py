"""LLM client abstraction.

Wraps an OpenAI-compatible chat model (via langchain-openai). When
``LLM_OFFLINE_MODE`` is enabled or no API key is configured, the client
returns deterministic stub responses so the whole system remains runnable
and testable without external dependencies.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """A thin, JSON-oriented wrapper around an OpenAI-compatible chat model."""

    def __init__(self) -> None:
        self.model = settings.LLM_MODEL
        self.offline = settings.LLM_OFFLINE_MODE or not settings.OPENAI_API_KEY
        self._chat: Any | None = None
        if not self.offline:
            self._chat = self._build_chat()

    def _build_chat(self) -> Any | None:
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=self.model,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                timeout=60,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("llm_init_failed", error=str(exc))
            self.offline = True
            return None

    # ---- public API ----
    def complete(self, system: str, user: str) -> str:
        """Return a raw text completion."""
        if self.offline or self._chat is None:
            return self._stub_text(system, user)
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            resp = self._chat.invoke(
                [SystemMessage(content=system), HumanMessage(content=user)]
            )
            return str(resp.content)
        except Exception as exc:  # pragma: no cover
            logger.warning("llm_invoke_failed", error=str(exc))
            return self._stub_text(system, user)

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        default: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a parsed JSON object from the model.

        Falls back to ``default`` (or an empty dict) when the model is offline
        or returns unparsable content.
        """
        if self.offline or self._chat is None:
            return default or self._stub_json(system, user)
        guarded_system = (
            system + "\n\nRespond ONLY with a single valid minified JSON object. "
            "Do not include markdown fences or commentary."
        )
        raw = self.complete(guarded_system, user)
        parsed = self._safe_json(raw)
        if parsed is None:
            logger.warning("llm_json_parse_failed")
            return default or self._stub_json(system, user)
        return parsed

    # ---- helpers ----
    @staticmethod
    def _safe_json(raw: str) -> dict[str, Any] | None:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
        return None

    @staticmethod
    def _stub_text(system: str, user: str) -> str:
        return (
            "[offline-llm] Deterministic stub response. "
            "Configure OPENAI_API_KEY and set LLM_OFFLINE_MODE=false for live generation."
        )

    @staticmethod
    def _stub_json(system: str, user: str) -> dict[str, Any]:
        return {
            "_offline": True,
            "note": "Deterministic offline stub. Engine-computed fields remain authoritative.",
        }


@lru_cache
def get_llm_client() -> LLMClient:
    return LLMClient()

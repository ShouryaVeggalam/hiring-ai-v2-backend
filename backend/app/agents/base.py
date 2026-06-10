"""Base agent abstraction shared by all 11 agents in the network."""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.agents.llm import LLMClient, get_llm_client
from app.core.constants import AgentName
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.schemas.agent import AgentRunResult

logger = get_logger(__name__)


@dataclass
class AgentContext:
    """Execution context passed to every agent."""

    db: Session
    company_id: str | None = None
    actor_id: str | None = None
    llm: LLMClient = field(default_factory=get_llm_client)
    extra: dict[str, Any] = field(default_factory=dict)


class BaseAgent(abc.ABC):
    """Abstract base class enforcing a consistent agent interface."""

    name: AgentName
    description: str = ""

    def __init__(self, ctx: AgentContext) -> None:
        self.ctx = ctx
        self.db = ctx.db
        self.llm = ctx.llm
        self.log = logger.bind(agent=self.name.value)

    @abc.abstractmethod
    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        """Execute the agent's primary function."""

    # ---- convenience helpers for subclasses ----
    def execute(self, payload: dict[str, Any]) -> AgentRunResult:
        """Wrap :meth:`run` with timing, logging, and error handling."""
        started = time.perf_counter()
        self.log.info("agent_run_start", payload_keys=list(payload.keys()))
        try:
            result = self.run(payload)
        except AgentExecutionError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            self.log.error("agent_run_failed", error=str(exc), exc_info=True)
            raise AgentExecutionError(f"{self.name.value} failed: {exc}") from exc
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.log.info("agent_run_done", elapsed_ms=round(elapsed_ms, 1), score=result.score)
        result.model = self.llm.model if not self.llm.offline else "offline-stub"
        return result

    def _result(
        self,
        summary: str,
        *,
        output: dict[str, Any] | None = None,
        recommendations: list[dict[str, Any]] | None = None,
        score: float | None = None,
        confidence: float | None = None,
    ) -> AgentRunResult:
        return AgentRunResult(
            agent=self.name,
            success=True,
            summary=summary,
            output=output or {},
            recommendations=recommendations or [],
            score=score,
            confidence=confidence,
        )

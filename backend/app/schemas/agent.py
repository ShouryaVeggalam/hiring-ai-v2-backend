"""Generic agent run schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import AgentName


class AgentRunResult(BaseModel):
    """Standard envelope returned by every agent."""

    agent: AgentName
    success: bool = True
    summary: str
    output: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    score: float | None = None
    confidence: float | None = None
    model: str | None = None


class WorkforceAnalysisRequest(BaseModel):
    company_id: str
    horizon_months: int = Field(default=6, ge=1, le=36)
    context: str | None = None


class OrchestrationRequest(BaseModel):
    """Kick off the full hiring workflow for a role."""

    company_id: str
    job_title: str
    department_id: str | None = None
    context: str | None = None
    run_async: bool = False


class OrchestrationResult(BaseModel):
    run_id: str
    status: str
    steps: list[dict[str, Any]] = Field(default_factory=list)
    summary: str | None = None

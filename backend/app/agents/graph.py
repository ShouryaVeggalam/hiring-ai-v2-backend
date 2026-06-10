"""LangGraph orchestration of the full Hiring AI Network.

Defines the canonical workflow:

    Workforce → Job → Talent → Candidate → Qualification → Interview →
    Assessment → Reference Verification → Offer → Onboarding → Hiring Chief

If LangGraph is unavailable the same node functions are executed
sequentially by :func:`run_pipeline`, so orchestration always works.
"""
from __future__ import annotations

from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.agents.base import AgentContext
from app.agents.registry import AGENT_PIPELINE, get_agent
from app.core.constants import AgentName
from app.core.logging import get_logger

logger = get_logger(__name__)


class HiringState(TypedDict, total=False):
    """Shared state threaded through the orchestration graph."""

    db: Any
    company_id: str | None
    actor_id: str | None
    job_title: str
    department_id: str | None
    context: str | None
    steps: list[dict[str, Any]]
    job_opening_id: str | None
    errors: list[str]


def _payload_for(agent: AgentName, state: HiringState) -> dict[str, Any]:
    """Build the per-agent payload from the running state."""
    base = {
        "company_id": state.get("company_id"),
        "context": state.get("context"),
    }
    if agent is AgentName.JOB:
        return {**base, "title": state.get("job_title", "Software Engineer")}
    if agent is AgentName.TALENT:
        return {**base, "job_opening_id": state.get("job_opening_id")}
    if agent is AgentName.QUALIFICATION:
        return {**base, "job_opening_id": state.get("job_opening_id")}
    return base


def _make_node(agent_name: AgentName):
    def _node(state: HiringState) -> HiringState:
        db: Session = state["db"]
        ctx = AgentContext(
            db=db, company_id=state.get("company_id"), actor_id=state.get("actor_id")
        )
        agent = get_agent(agent_name, ctx)
        steps = state.get("steps", [])
        errors = state.get("errors", [])
        try:
            result = agent.execute(_payload_for(agent_name, state))
            steps.append(
                {
                    "agent": agent_name.value,
                    "summary": result.summary,
                    "score": result.score,
                    "success": True,
                }
            )
            # Capture the job opening id created by the Job Intelligence Agent.
            if agent_name is AgentName.JOB:
                # The job service persists separately; here we run the agent only.
                state["job_opening_id"] = result.output.get("job_opening_id")
        except Exception as exc:  # pragma: no cover - defensive per-node isolation
            logger.warning("orchestration_node_failed", agent=agent_name.value, error=str(exc))
            errors.append(f"{agent_name.value}: {exc}")
            steps.append({"agent": agent_name.value, "success": False, "error": str(exc)})
        state["steps"] = steps
        state["errors"] = errors
        return state

    return _node


def build_graph():
    """Build and compile the LangGraph state graph (if LangGraph is installed)."""
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(HiringState)
    previous: str | None = None
    for agent_name in AGENT_PIPELINE:
        node_name = agent_name.value
        graph.add_node(node_name, _make_node(agent_name))
        if previous is None:
            graph.add_edge(START, node_name)
        else:
            graph.add_edge(previous, node_name)
        previous = node_name
    if previous:
        graph.add_edge(previous, END)
    return graph.compile()


def run_pipeline(state: HiringState) -> HiringState:
    """Run the full pipeline, preferring LangGraph and falling back to sequential."""
    try:
        compiled = build_graph()
        return compiled.invoke(state)  # type: ignore[return-value]
    except Exception as exc:
        logger.info("langgraph_unavailable_fallback", error=str(exc))
        for agent_name in AGENT_PIPELINE:
            state = _make_node(agent_name)(state)
        return state

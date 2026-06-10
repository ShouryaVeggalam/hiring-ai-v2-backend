"""Agent 1 — Workforce Planning Agent.

Predicts hiring needs from organisational capacity and workload signals.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, RecommendationType
from app.repositories.company import DepartmentRepository
from app.schemas.agent import AgentRunResult


class WorkforcePlanningAgent(BaseAgent):
    name = AgentName.WORKFORCE
    description = "Predicts hiring needs via capacity, workload, and demand forecasting."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        company_id = payload.get("company_id") or self.ctx.company_id
        horizon = int(payload.get("horizon_months", 6))
        dept_repo = DepartmentRepository(self.db)
        departments = (
            dept_repo.list_for_company(company_id) if company_id else dept_repo.list(limit=200)
        )

        forecasts: list[dict] = []
        priority_roles: list[dict] = []
        risks: list[dict] = []
        recommendations: list[dict] = []
        total_gap = 0

        for dept in departments:
            gap = max(0, dept.target_headcount - dept.headcount)
            utilization = self._utilization(dept.headcount, dept.target_headcount)
            total_gap += gap
            forecast = {
                "department_id": dept.id,
                "department": dept.name,
                "current_headcount": dept.headcount,
                "target_headcount": dept.target_headcount,
                "gap": gap,
                "utilization": utilization,
                "projected_hires": self._project_hires(gap, horizon),
            }
            forecasts.append(forecast)

            if gap > 0:
                priority = self._priority(gap, utilization)
                priority_roles.append(
                    {"department": dept.name, "open_positions": gap, "priority": priority}
                )
                recommendations.append(
                    {
                        "type": RecommendationType.PRIORITY_ROLE.value,
                        "title": f"Hire {gap} role(s) in {dept.name}",
                        "rationale": f"Headcount gap of {gap}; utilization at {utilization}%.",
                        "confidence": 0.7 + min(0.25, gap * 0.05),
                        "priority": {"critical": 3, "high": 2, "medium": 1}.get(priority, 0),
                        "payload": forecast,
                    }
                )
            if utilization >= 110:
                risks.append(
                    {
                        "department": dept.name,
                        "risk": "burnout / over-utilization",
                        "severity": "high",
                        "utilization": utilization,
                    }
                )
                recommendations.append(
                    {
                        "type": RecommendationType.HIRING_RISK.value,
                        "title": f"Over-utilization risk in {dept.name}",
                        "rationale": f"Team running at {utilization}% capacity.",
                        "confidence": 0.8,
                        "priority": 3,
                        "payload": {"department": dept.name},
                    }
                )

        # Optional LLM narrative enrichment.
        narrative = self._narrative(payload, forecasts, risks)

        output = {
            "horizon_months": horizon,
            "department_forecasts": forecasts,
            "priority_roles": sorted(
                priority_roles, key=lambda r: r["open_positions"], reverse=True
            ),
            "hiring_risks": risks,
            "total_headcount_gap": total_gap,
            "narrative": narrative,
        }
        score = self._demand_score(total_gap, len(departments))
        return self._result(
            f"Workforce plan across {len(departments)} departments; "
            f"{total_gap} open position(s) forecasted.",
            output=output,
            recommendations=recommendations,
            score=score,
            confidence=0.75,
        )

    @staticmethod
    def _utilization(headcount: int, target: int) -> float:
        if target <= 0:
            return 100.0
        return round(target / max(headcount, 1) * 100.0, 1)

    @staticmethod
    def _project_hires(gap: int, horizon_months: int) -> int:
        if gap <= 0:
            return 0
        return min(gap, max(1, round(gap * (horizon_months / 6))))

    @staticmethod
    def _priority(gap: int, utilization: float) -> str:
        if gap >= 5 or utilization >= 130:
            return "critical"
        if gap >= 2 or utilization >= 110:
            return "high"
        return "medium"

    @staticmethod
    def _demand_score(total_gap: int, dept_count: int) -> float:
        if dept_count == 0:
            return 0.0
        return round(min(100.0, total_gap / dept_count * 25.0), 2)

    def _narrative(self, payload: dict, forecasts: list[dict], risks: list[dict]) -> str:
        system = (
            "You are a workforce planning strategist. Summarise hiring demand and risks "
            "in two concise sentences."
        )
        user = (
            f"Context: {payload.get('context', 'n/a')}\n"
            f"Forecasts: {forecasts}\nRisks: {risks}"
        )
        return self.llm.complete(system, user)

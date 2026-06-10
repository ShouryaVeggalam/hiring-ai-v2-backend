"""Agent 10 — Onboarding Agent.

Manages the joining process: document collection, training tracking,
joining status, onboarding workflow, and progress tracking.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import AgentName, CandidateStage, OnboardingStatus
from app.core.exceptions import NotFoundError
from app.repositories.candidate import CandidateRepository
from app.repositories.onboarding import OnboardingRepository
from app.schemas.agent import AgentRunResult

_DEFAULT_DOCUMENTS = [
    "signed_offer_letter", "government_id", "tax_forms", "bank_details",
    "education_certificates", "employment_proof", "nda",
]
_DEFAULT_TRAINING = [
    "company_orientation", "security_awareness", "role_specific_training",
    "tools_setup", "team_introduction",
]


class OnboardingAgent(BaseAgent):
    name = AgentName.ONBOARDING
    description = "Drives onboarding workflow and tracks completion."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        cand_repo = CandidateRepository(self.db)
        repo = OnboardingRepository(self.db)
        cand = cand_repo.get(payload["candidate_id"]) if payload.get("candidate_id") else None
        if not cand:
            raise NotFoundError("Candidate not found")

        onboarding = repo.get_for_candidate(cand.id)
        if not onboarding:
            onboarding = repo.create(
                candidate_id=cand.id,
                offer_id=payload.get("offer_id"),
                status=OnboardingStatus.DOCUMENTS_PENDING,
                start_date=datetime.now(timezone.utc),
                documents=self._init_items(_DEFAULT_DOCUMENTS),
                training_modules=self._init_items(_DEFAULT_TRAINING),
                checklist=self._init_items(["workspace_provisioned", "accounts_created", "manager_1on1"]),
            )

        # Apply updates from payload (e.g., mark documents/training complete).
        self._apply_updates(onboarding, payload)
        progress = self._progress(onboarding)
        onboarding.completion_percentage = progress
        onboarding.onboarding_score = progress
        onboarding.status = self._status(progress)
        onboarding.workflow = {
            "next_steps": self._next_steps(onboarding),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if progress >= 100:
            onboarding.completed_at = datetime.now(timezone.utc)
            cand.stage = CandidateStage.HIRED
        else:
            cand.stage = CandidateStage.ONBOARDING
        repo.save(onboarding)
        cand_repo.save(cand)

        return self._result(
            f"Onboarding at {round(progress, 1)}% for {cand.full_name}.",
            output={
                "onboarding_id": onboarding.id,
                "completion_percentage": progress,
                "status": onboarding.status.value,
                "documents": onboarding.documents,
                "training_modules": onboarding.training_modules,
                "next_steps": onboarding.workflow["next_steps"],
            },
            score=progress,
            confidence=0.8,
        )

    @staticmethod
    def _init_items(names: list[str]) -> list[dict]:
        return [{"name": n, "completed": False} for n in names]

    @staticmethod
    def _apply_updates(onboarding: Any, payload: dict) -> None:
        completed = set(payload.get("completed_items", []))
        for bucket in ("documents", "training_modules", "checklist"):
            items = getattr(onboarding, bucket) or []
            for item in items:
                if item.get("name") in completed:
                    item["completed"] = True
            setattr(onboarding, bucket, items)

    @staticmethod
    def _progress(onboarding: Any) -> float:
        all_items: list[dict] = []
        for bucket in ("documents", "training_modules", "checklist"):
            all_items += getattr(onboarding, bucket) or []
        if not all_items:
            return 0.0
        done = sum(1 for i in all_items if i.get("completed"))
        return round(done / len(all_items) * 100.0, 2)

    @staticmethod
    def _status(progress: float) -> OnboardingStatus:
        if progress >= 100:
            return OnboardingStatus.COMPLETED
        if progress >= 60:
            return OnboardingStatus.TRAINING
        if progress > 0:
            return OnboardingStatus.IN_PROGRESS
        return OnboardingStatus.DOCUMENTS_PENDING

    @staticmethod
    def _next_steps(onboarding: Any) -> list[str]:
        steps: list[str] = []
        for bucket in ("documents", "training_modules", "checklist"):
            for item in getattr(onboarding, bucket) or []:
                if not item.get("completed"):
                    steps.append(item["name"])
        return steps[:5]

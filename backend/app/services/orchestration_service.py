"""Orchestration service — drives the end-to-end hiring workflow.

Creates a real Job Opening via the Job service, then runs the remaining
agents through the LangGraph pipeline, persisting recommendations and
activity along the way.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.agents.graph import run_pipeline
from app.core.logging import get_logger
from app.schemas.agent import OrchestrationRequest, OrchestrationResult
from app.schemas.job import JobBlueprintRequest
from app.services.common import log_activity
from app.services.job_service import JobService

logger = get_logger(__name__)


class OrchestrationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, req: OrchestrationRequest, actor_id: str | None = None) -> OrchestrationResult:
        run_id = str(uuid.uuid4())
        logger.info("orchestration_start", run_id=run_id, job_title=req.job_title)

        # Step 1: create a concrete job opening (also runs the Job Intelligence Agent).
        job_result, job = JobService(self.db).generate_blueprint(
            JobBlueprintRequest(title=req.job_title, context=req.context),
            company_id=req.company_id,
            department_id=req.department_id,
            actor_id=actor_id,
            persist=True,
        )

        state = {
            "db": self.db,
            "company_id": req.company_id,
            "actor_id": actor_id,
            "job_title": req.job_title,
            "department_id": req.department_id,
            "context": req.context,
            "job_opening_id": job.id if job else None,
            "steps": [
                {
                    "agent": "job_intelligence",
                    "summary": job_result.summary,
                    "score": job_result.score,
                    "success": True,
                }
            ],
            "errors": [],
        }
        final = run_pipeline(state)
        self.db.commit()

        log_activity(
            self.db,
            "orchestration_run",
            description=f"Full hiring workflow executed for '{req.job_title}'",
            company_id=req.company_id,
            actor_id=actor_id,
            meta={"run_id": run_id, "steps": len(final.get("steps", []))},
        )
        self.db.commit()

        status = "completed" if not final.get("errors") else "completed_with_errors"
        return OrchestrationResult(
            run_id=run_id,
            status=status,
            steps=final.get("steps", []),
            summary=f"Executed {len(final.get('steps', []))} agent steps for '{req.job_title}'.",
        )

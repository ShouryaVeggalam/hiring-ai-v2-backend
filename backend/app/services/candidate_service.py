"""Candidate service: CRUD, resume processing, candidate intelligence."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.constants import AgentName
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.engines.resume import ResumeProcessingEngine
from app.models.candidate import Candidate, Resume
from app.repositories.candidate import CandidateRepository, ResumeRepository
from app.schemas.agent import AgentRunResult
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.services.common import log_activity, persist_recommendations, run_agent


class CandidateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CandidateRepository(db)
        self.resumes = ResumeRepository(db)
        self.resume_engine = ResumeProcessingEngine()

    def create(self, data: CandidateCreate, actor_id: str | None = None) -> Candidate:
        cand = self.repo.create(data.model_dump())
        log_activity(
            self.db, "candidate_created", description=f"Candidate '{cand.full_name}' added",
            entity_type="candidate", entity_id=cand.id, actor_id=actor_id,
        )
        self.db.commit()
        return cand

    def get(self, candidate_id: str) -> Candidate:
        cand = self.repo.get(candidate_id)
        if not cand:
            raise NotFoundError("Candidate not found")
        return cand

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[Candidate], int]:
        return self.repo.list(offset=offset, limit=limit), self.repo.count()

    def update(self, candidate_id: str, data: CandidateUpdate) -> Candidate:
        cand = self.get(candidate_id)
        cand = self.repo.update(cand, data.model_dump(exclude_unset=True))
        self.db.commit()
        return cand

    def delete(self, candidate_id: str) -> None:
        cand = self.get(candidate_id)
        self.repo.delete(cand)
        self.db.commit()

    # ---- resume processing ----
    def upload_resume(
        self,
        *,
        content: bytes,
        filename: str,
        candidate_id: str | None = None,
        job_opening_id: str | None = None,
        actor_id: str | None = None,
    ) -> tuple[Candidate, Resume]:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.resume_engine.SUPPORTED:
            raise ValidationFailedError(
                f"Unsupported file type '.{ext}'. Allowed: pdf, docx, txt."
            )
        profile = self.resume_engine.parse(content, ext, filename=filename)

        if candidate_id:
            cand = self.get(candidate_id)
            cand.skills = sorted(set((cand.skills or []) + profile.skills))
            cand.education = cand.education or profile.education
            cand.experience = cand.experience or profile.experience
            cand.projects = cand.projects or profile.projects
            if profile.years_experience and not cand.years_experience:
                cand.years_experience = profile.years_experience
        else:
            cand = self.repo.create(
                full_name=profile.full_name or filename.rsplit(".", 1)[0],
                email=profile.email,
                phone=profile.phone,
                skills=profile.skills,
                education=profile.education,
                experience=profile.experience,
                projects=profile.projects,
                years_experience=profile.years_experience,
                source="resume_upload",
                job_opening_id=job_opening_id,
            )

        resume = self.resumes.create(
            filename=filename,
            file_type=ext,
            raw_text=profile.raw_text,
            parsed_data=profile.to_dict(),
            parse_status="parsed",
            candidate_id=cand.id,
        )
        self.repo.save(cand)
        log_activity(
            self.db, "resume_uploaded", description=f"Resume parsed for {cand.full_name}",
            entity_type="candidate", entity_id=cand.id, actor_id=actor_id,
        )
        self.db.commit()
        return cand, resume

    # ---- candidate intelligence ----
    def analyze(self, candidate_id: str, actor_id: str | None = None) -> AgentRunResult:
        self.get(candidate_id)
        result = run_agent(
            self.db, AgentName.CANDIDATE, {"candidate_id": candidate_id}, actor_id=actor_id
        )
        persist_recommendations(self.db, result)
        log_activity(
            self.db, "candidate_analyzed", description=result.summary,
            entity_type="candidate", entity_id=candidate_id, actor_id=actor_id,
        )
        self.db.commit()
        return result

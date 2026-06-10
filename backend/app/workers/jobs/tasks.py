"""Celery background tasks for scheduled hiring operations."""
from __future__ import annotations

from app.core.constants import ReportType
from app.core.logging import configure_logging, get_logger
from app.database.session import SessionLocal
from app.schemas.report import ReportGenerateRequest
from app.services.candidate_service import CandidateService
from app.services.chief_service import ChiefService
from app.services.qualification_service import QualificationService
from app.services.report_service import ReportService
from app.workers.celery_app import celery_app

configure_logging()
logger = get_logger(__name__)


def _db():
    return SessionLocal()


@celery_app.task(name="app.workers.jobs.candidate_refresh", bind=True, max_retries=3)
def candidate_refresh(self) -> dict:
    """Hourly: re-run candidate intelligence on recently updated candidates."""
    db = _db()
    try:
        from app.repositories.candidate import CandidateRepository

        repo = CandidateRepository(db)
        candidates = repo.list(limit=50)
        refreshed = 0
        for cand in candidates:
            try:
                CandidateService(db).analyze(cand.id)
                refreshed += 1
            except Exception as exc:
                logger.warning("candidate_refresh_skip", id=cand.id, error=str(exc))
        logger.info("candidate_refresh_done", refreshed=refreshed)
        return {"refreshed": refreshed}
    except Exception as exc:
        logger.error("candidate_refresh_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc
    finally:
        db.close()


@celery_app.task(name="app.workers.jobs.qualification_refresh", bind=True, max_retries=3)
def qualification_refresh(self) -> dict:
    """Hourly: refresh qualification scores for open roles."""
    db = _db()
    try:
        from app.repositories.job import JobRepository

        jobs = JobRepository(db).list_open()
        refreshed = 0
        for job in jobs:
            try:
                QualificationService(db).qualify(job.id)
                refreshed += 1
            except Exception as exc:
                logger.warning("qualification_refresh_skip", job_id=job.id, error=str(exc))
        logger.info("qualification_refresh_done", refreshed=refreshed)
        return {"refreshed": refreshed}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc
    finally:
        db.close()


@celery_app.task(name="app.workers.jobs.matching_refresh", bind=True, max_retries=3)
def matching_refresh(self) -> dict:
    """Hourly: recompute match scores via the matching engine."""
    db = _db()
    try:
        from app.engines.matching import MatchingEngine
        from app.repositories.candidate import CandidateRepository
        from app.repositories.job import JobRepository

        engine = MatchingEngine()
        cand_repo = CandidateRepository(db)
        job_repo = JobRepository(db)
        updated = 0
        for job in job_repo.list_open(limit=20):
            for cand in cand_repo.list_for_job(job.id) or cand_repo.list(limit=100):
                result = engine.match(
                    candidate_skills=cand.skills or [],
                    required_skills=job.required_skills or [],
                    preferred_skills=job.preferred_skills or [],
                    candidate_years=cand.years_experience,
                    required_years=job.min_experience_years,
                )
                cand.match_score = result.match_score
                updated += 1
        db.commit()
        logger.info("matching_refresh_done", updated=updated)
        return {"updated": updated}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60) from exc
    finally:
        db.close()


@celery_app.task(name="app.workers.jobs.hiring_summary", bind=True)
def hiring_summary(self) -> dict:
    """Daily: generate a hiring summary report."""
    db = _db()
    try:
        report = ReportService(db).generate(
            ReportGenerateRequest(report_type=ReportType.HIRING)
        )
        return {"report_id": report.id, "title": report.title}
    finally:
        db.close()


@celery_app.task(name="app.workers.jobs.interview_summary", bind=True)
def interview_summary(self) -> dict:
    """Daily: generate an interview summary report."""
    db = _db()
    try:
        report = ReportService(db).generate(
            ReportGenerateRequest(report_type=ReportType.INTERVIEW)
        )
        return {"report_id": report.id, "title": report.title}
    finally:
        db.close()


@celery_app.task(name="app.workers.jobs.hiring_report", bind=True)
def hiring_report(self) -> dict:
    """Weekly: generate a comprehensive hiring report."""
    db = _db()
    try:
        report = ReportService(db).generate(
            ReportGenerateRequest(report_type=ReportType.EXECUTIVE)
        )
        ChiefService(db).report()
        return {"report_id": report.id, "title": report.title}
    finally:
        db.close()


@celery_app.task(name="app.workers.jobs.talent_intelligence_report", bind=True)
def talent_intelligence_report(self) -> dict:
    """Monthly: generate a talent intelligence report."""
    db = _db()
    try:
        report = ReportService(db).generate(
            ReportGenerateRequest(report_type=ReportType.TALENT_INTELLIGENCE)
        )
        return {"report_id": report.id, "title": report.title}
    finally:
        db.close()

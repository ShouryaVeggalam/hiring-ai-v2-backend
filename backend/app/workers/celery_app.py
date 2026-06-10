"""Celery application configuration."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "celestra_hiring",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.jobs.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # ---- Hourly ----
        "candidate-refresh": {
            "task": "app.workers.jobs.candidate_refresh",
            "schedule": crontab(minute=0),  # every hour
        },
        "qualification-refresh": {
            "task": "app.workers.jobs.qualification_refresh",
            "schedule": crontab(minute=15),
        },
        "matching-refresh": {
            "task": "app.workers.jobs.matching_refresh",
            "schedule": crontab(minute=30),
        },
        # ---- Daily ----
        "hiring-summary": {
            "task": "app.workers.jobs.hiring_summary",
            "schedule": crontab(hour=6, minute=0),
        },
        "interview-summary": {
            "task": "app.workers.jobs.interview_summary",
            "schedule": crontab(hour=7, minute=0),
        },
        # ---- Weekly ----
        "hiring-report": {
            "task": "app.workers.jobs.hiring_report",
            "schedule": crontab(hour=8, minute=0, day_of_week="monday"),
        },
        # ---- Monthly ----
        "talent-intelligence-report": {
            "task": "app.workers.jobs.talent_intelligence_report",
            "schedule": crontab(hour=9, minute=0, day_of_month="1"),
        },
    },
)

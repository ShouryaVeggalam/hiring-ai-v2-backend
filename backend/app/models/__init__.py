"""ORM models for the Celestra Hiring AI platform.

Importing this package registers every model on the shared ``Base`` metadata
so that Alembic autogeneration and ``Base.metadata.create_all`` see them all.
"""
from app.models.activity import ActivityLog
from app.models.assessment import Assessment
from app.models.candidate import Candidate, Resume, TalentPool
from app.models.company import Company, Department, Role
from app.models.interview import Interview
from app.models.job import JobOpening
from app.models.notification import Notification
from app.models.offer import Offer
from app.models.onboarding import Onboarding
from app.models.recommendation import HiringRecommendation
from app.models.report import HiringReport
from app.models.user import User
from app.models.verification import ReferenceCheck

__all__ = [
    "ActivityLog",
    "Assessment",
    "Candidate",
    "Resume",
    "TalentPool",
    "Company",
    "Department",
    "Role",
    "Interview",
    "JobOpening",
    "Notification",
    "Offer",
    "Onboarding",
    "HiringRecommendation",
    "HiringReport",
    "User",
    "ReferenceCheck",
]

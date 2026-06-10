"""Repository layer implementing the repository pattern over SQLAlchemy."""
from app.repositories.activity import ActivityRepository
from app.repositories.assessment import AssessmentRepository
from app.repositories.candidate import (
    CandidateRepository,
    ResumeRepository,
    TalentPoolRepository,
)
from app.repositories.company import (
    CompanyRepository,
    DepartmentRepository,
    RoleRepository,
)
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.repositories.notification import NotificationRepository
from app.repositories.offer import OfferRepository
from app.repositories.onboarding import OnboardingRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.report import ReportRepository
from app.repositories.user import UserRepository
from app.repositories.verification import ReferenceRepository

__all__ = [
    "ActivityRepository",
    "AssessmentRepository",
    "CandidateRepository",
    "ResumeRepository",
    "TalentPoolRepository",
    "CompanyRepository",
    "DepartmentRepository",
    "RoleRepository",
    "InterviewRepository",
    "JobRepository",
    "NotificationRepository",
    "OfferRepository",
    "OnboardingRepository",
    "RecommendationRepository",
    "ReportRepository",
    "UserRepository",
    "ReferenceRepository",
]

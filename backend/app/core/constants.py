"""Shared enumerations and constants used across the platform."""
from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """RBAC roles. Order roughly maps to privilege level."""

    ADMIN = "admin"
    FOUNDER = "founder"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    VIEWER = "viewer"


# Privilege ranking (higher == more powerful). Used for hierarchical checks.
ROLE_RANK: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.HIRING_MANAGER: 1,
    UserRole.RECRUITER: 2,
    UserRole.HR_MANAGER: 3,
    UserRole.FOUNDER: 4,
    UserRole.ADMIN: 5,
}


class JobStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    FILLED = "filled"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeniorityLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class CandidateStage(str, Enum):
    """Candidate pipeline stages."""

    DISCOVERED = "discovered"
    SCREENING = "screening"
    QUALIFIED = "qualified"
    INTERVIEWING = "interviewing"
    ASSESSMENT = "assessment"
    REFERENCE_CHECK = "reference_check"
    OFFER = "offer"
    HIRED = "hired"
    ONBOARDING = "onboarding"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class InterviewType(str, Enum):
    SCREENING = "screening"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CULTURE_FIT = "culture_fit"
    FINAL = "final"


class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class InterviewRecommendation(str, Enum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    NEUTRAL = "neutral"
    NO_HIRE = "no_hire"
    STRONG_NO_HIRE = "strong_no_hire"


class AssessmentType(str, Enum):
    CODING = "coding"
    ASSIGNMENT = "assignment"
    CASE_STUDY = "case_study"
    APTITUDE = "aptitude"


class AssessmentStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EVALUATED = "evaluated"
    EXPIRED = "expired"


class ReferenceStatus(str, Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    RECEIVED = "received"
    VERIFIED = "verified"
    FLAGGED = "flagged"


class OfferStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class OnboardingStatus(str, Enum):
    NOT_STARTED = "not_started"
    DOCUMENTS_PENDING = "documents_pending"
    IN_PROGRESS = "in_progress"
    TRAINING = "training"
    COMPLETED = "completed"


class RecommendationType(str, Enum):
    HIRE = "hire"
    SHORTLIST = "shortlist"
    REJECT = "reject"
    HOLD = "hold"
    PRIORITY_ROLE = "priority_role"
    HIRING_RISK = "hiring_risk"


class ReportType(str, Enum):
    HIRING = "hiring"
    CANDIDATE = "candidate"
    INTERVIEW = "interview"
    ASSESSMENT = "assessment"
    OFFER = "offer"
    EXECUTIVE = "executive"
    TALENT_INTELLIGENCE = "talent_intelligence"


class NotificationType(str, Enum):
    INTERVIEW_ALERT = "interview_alert"
    ASSESSMENT_ALERT = "assessment_alert"
    OFFER_ALERT = "offer_alert"
    ONBOARDING_ALERT = "onboarding_alert"
    HIRING_RISK_ALERT = "hiring_risk_alert"
    EXECUTIVE_ALERT = "executive_alert"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    WEBSOCKET = "websocket"


class AgentName(str, Enum):
    """Canonical names of the agents in the Hiring AI Network."""

    WORKFORCE = "workforce_planning"
    JOB = "job_intelligence"
    TALENT = "talent_discovery"
    CANDIDATE = "candidate_intelligence"
    QUALIFICATION = "qualification"
    INTERVIEW = "interview_intelligence"
    ASSESSMENT = "assessment"
    VERIFICATION = "reference_verification"
    OFFER = "offer"
    ONBOARDING = "onboarding"
    CHIEF = "hiring_chief"

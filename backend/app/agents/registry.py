"""Central registry mapping agent names to their implementations."""
from __future__ import annotations

from app.agents.base import AgentContext, BaseAgent
from app.agents.candidate import CandidateIntelligenceAgent
from app.agents.assessment import AssessmentAgent
from app.agents.chief import HiringChiefAgent
from app.agents.interview import InterviewIntelligenceAgent
from app.agents.job import JobIntelligenceAgent
from app.agents.offer import OfferAgent
from app.agents.onboarding import OnboardingAgent
from app.agents.qualification import QualificationAgent
from app.agents.talent import TalentDiscoveryAgent
from app.agents.verification import ReferenceVerificationAgent
from app.agents.workforce import WorkforcePlanningAgent
from app.core.constants import AgentName

AGENT_REGISTRY: dict[AgentName, type[BaseAgent]] = {
    AgentName.WORKFORCE: WorkforcePlanningAgent,
    AgentName.JOB: JobIntelligenceAgent,
    AgentName.TALENT: TalentDiscoveryAgent,
    AgentName.CANDIDATE: CandidateIntelligenceAgent,
    AgentName.QUALIFICATION: QualificationAgent,
    AgentName.INTERVIEW: InterviewIntelligenceAgent,
    AgentName.ASSESSMENT: AssessmentAgent,
    AgentName.VERIFICATION: ReferenceVerificationAgent,
    AgentName.OFFER: OfferAgent,
    AgentName.ONBOARDING: OnboardingAgent,
    AgentName.CHIEF: HiringChiefAgent,
}

# Canonical execution order of the Hiring AI Network.
AGENT_PIPELINE: list[AgentName] = [
    AgentName.WORKFORCE,
    AgentName.JOB,
    AgentName.TALENT,
    AgentName.CANDIDATE,
    AgentName.QUALIFICATION,
    AgentName.INTERVIEW,
    AgentName.ASSESSMENT,
    AgentName.VERIFICATION,
    AgentName.OFFER,
    AgentName.ONBOARDING,
    AgentName.CHIEF,
]


def get_agent(name: AgentName, ctx: AgentContext) -> BaseAgent:
    """Instantiate an agent by name with the given execution context."""
    agent_cls = AGENT_REGISTRY[name]
    return agent_cls(ctx)

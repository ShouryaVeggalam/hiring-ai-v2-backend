"""Agent 6 — Interview Intelligence Agent.

Manages interviews: plan generation, question generation, transcript
analysis, feedback analysis, and hiring-signal detection.
"""
from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.core.constants import (
    AgentName,
    InterviewRecommendation,
    InterviewType,
)
from app.core.exceptions import NotFoundError
from app.repositories.candidate import CandidateRepository
from app.repositories.interview import InterviewRepository
from app.repositories.job import JobRepository
from app.schemas.agent import AgentRunResult
from app.utils import text as T

_POSITIVE = ("excellent", "strong", "clear", "confident", "impressive", "solid",
             "great", "deep", "thorough", "structured", "collaborative")
_NEGATIVE = ("weak", "unclear", "struggled", "confused", "shallow", "hesitant",
             "poor", "lacked", "unable", "vague", "concern")


class InterviewIntelligenceAgent(BaseAgent):
    name = AgentName.INTERVIEW
    description = "Plans interviews and analyses transcripts to produce hiring signals."

    def run(self, payload: dict[str, Any]) -> AgentRunResult:
        action = payload.get("action", "plan")
        if action == "analyze":
            return self._analyze(payload)
        return self._plan(payload)

    # ---- plan + question generation ----
    def _plan(self, payload: dict[str, Any]) -> AgentRunResult:
        cand_repo = CandidateRepository(self.db)
        cand = cand_repo.get(payload["candidate_id"]) if payload.get("candidate_id") else None
        if not cand:
            raise NotFoundError("Candidate not found")
        itype = self._coerce_type(payload.get("interview_type"))
        focus = payload.get("focus_areas") or (cand.skills or [])[:5]
        questions = self._questions(itype, focus, cand)
        plan = {
            "interview_type": itype.value,
            "focus_areas": focus,
            "duration_minutes": 45 if itype != InterviewType.SCREENING else 30,
            "structure": ["intro", "core questions", "candidate questions", "wrap-up"],
        }
        return self._result(
            f"Interview plan generated ({itype.value}) for {cand.full_name}.",
            output={"plan": plan, "questions": questions, "candidate_id": cand.id},
            score=None,
            confidence=0.75,
        )

    # ---- transcript / feedback analysis ----
    def _analyze(self, payload: dict[str, Any]) -> AgentRunResult:
        interview_repo = InterviewRepository(self.db)
        interview = (
            interview_repo.get(payload["interview_id"]) if payload.get("interview_id") else None
        )
        transcript = payload.get("transcript") or (interview.transcript if interview else "")
        if not transcript:
            raise NotFoundError("No transcript provided")

        signal = self._signal_detection(transcript)
        interview_score = signal["score"]
        confidence = signal["confidence"]
        recommendation = self._recommendation(interview_score)
        insights = self._llm_insights(transcript, signal)

        if interview:
            interview.transcript = transcript
            interview.interview_score = interview_score
            interview.confidence_score = confidence
            interview.recommendation = recommendation
            interview.insights = insights
            interview.feedback = {"signal": signal}
            interview_repo.save(interview)

        recommendations = [
            {
                "type": "hire" if interview_score >= 70 else "hold",
                "title": f"Interview signal: {recommendation.value}",
                "rationale": f"Interview score {interview_score}.",
                "confidence": confidence / 100,
                "priority": 2,
                "candidate_id": interview.candidate_id if interview else None,
            }
        ]
        return self._result(
            f"Transcript analysed — {recommendation.value} (score {interview_score}).",
            output={
                "interview_score": interview_score,
                "confidence_score": confidence,
                "recommendation": recommendation.value,
                "insights": insights,
            },
            recommendations=recommendations,
            score=interview_score,
            confidence=confidence / 100,
        )

    # ---- helpers ----
    @staticmethod
    def _coerce_type(value: Any) -> InterviewType:
        if isinstance(value, InterviewType):
            return value
        try:
            return InterviewType(str(value))
        except ValueError:
            return InterviewType.TECHNICAL

    def _questions(self, itype: InterviewType, focus: list[str], cand: Any) -> list[dict]:
        bank = {
            InterviewType.SCREENING: [
                "Walk me through your background and what you're looking for next.",
                "Why are you interested in this role?",
            ],
            InterviewType.TECHNICAL: [
                f"Describe a challenging problem you solved using {focus[0] if focus else 'your core stack'}.",
                "How do you approach testing and code quality?",
            ],
            InterviewType.BEHAVIORAL: [
                "Tell me about a time you handled conflict on a team.",
                "Describe a project you're most proud of and why.",
            ],
            InterviewType.SYSTEM_DESIGN: [
                "Design a scalable service for the described use case. Walk through trade-offs.",
            ],
            InterviewType.CULTURE_FIT: [
                "What kind of team environment helps you do your best work?",
            ],
            InterviewType.FINAL: [
                "What impact would you aim to make in your first 90 days?",
            ],
        }
        base = bank.get(itype, bank[InterviewType.TECHNICAL])
        skill_qs = [f"Go deep on your experience with {s}." for s in focus[:3]]
        out = base + skill_qs
        # Optional LLM enrichment.
        llm = self.llm.complete_json(
            system="Generate interview questions. Return JSON {questions: string[]}.",
            user=f"Type: {itype.value}; Focus: {focus}; Candidate skills: {cand.skills}",
            default={},
        )
        if not llm.get("_offline") and isinstance(llm.get("questions"), list):
            out = list(llm["questions"]) or out
        return [{"question": q, "competency": itype.value} for q in out]

    @staticmethod
    def _signal_detection(transcript: str) -> dict:
        low = transcript.lower()
        pos = sum(low.count(w) for w in _POSITIVE)
        neg = sum(low.count(w) for w in _NEGATIVE)
        total = pos + neg
        if total == 0:
            score = 60.0
            confidence = 40.0
        else:
            score = T.clamp(50.0 + (pos - neg) / total * 50.0)
            confidence = T.clamp(min(100.0, total * 12.0))
        return {"positive": pos, "negative": neg, "score": round(score, 2),
                "confidence": round(confidence, 2)}

    @staticmethod
    def _recommendation(score: float) -> InterviewRecommendation:
        if score >= 85:
            return InterviewRecommendation.STRONG_HIRE
        if score >= 70:
            return InterviewRecommendation.HIRE
        if score >= 50:
            return InterviewRecommendation.NEUTRAL
        if score >= 35:
            return InterviewRecommendation.NO_HIRE
        return InterviewRecommendation.STRONG_NO_HIRE

    def _llm_insights(self, transcript: str, signal: dict) -> dict:
        out = self.llm.complete_json(
            system=(
                "You are an interview analyst. Return JSON with keys: strengths (array), "
                "weaknesses (array), summary (string)."
            ),
            user=f"Transcript: {transcript[:4000]}\nSignals: {signal}",
            default={},
        )
        if out.get("_offline"):
            return {
                "strengths": ["communicates clearly"] if signal["positive"] else [],
                "weaknesses": ["areas of concern noted"] if signal["negative"] else [],
                "summary": f"Detected {signal['positive']} positive and "
                f"{signal['negative']} negative signals.",
            }
        return out

"""Unit tests for the resume, matching, and hiring health engines."""
from __future__ import annotations

from app.engines.hiring_health import HiringHealthEngine
from app.engines.matching import MatchingEngine
from app.engines.resume import ResumeProcessingEngine


class TestResumeEngine:
    def test_parse_txt_resume(self):
        engine = ResumeProcessingEngine()
        raw = """
        Jane Doe
        jane@example.com
        +1 555-123-4567

        SKILLS
        Python FastAPI PostgreSQL Docker Kubernetes

        EXPERIENCE
        Senior Engineer at Acme Corp | 2020 - Present
        8 years of experience

        EDUCATION
        B.Tech Computer Science, MIT University
        """
        profile = engine.parse_text(raw, filename="jane_doe.txt")
        assert profile.full_name is not None
        assert profile.email == "jane@example.com"
        assert "python" in profile.skills
        assert profile.years_experience >= 8.0

    def test_unsupported_type_raises(self):
        engine = ResumeProcessingEngine()
        try:
            engine.extract_text(b"data", "xlsx")
            assert False, "Should have raised"
        except ValueError as exc:
            assert "Unsupported" in str(exc)


class TestMatchingEngine:
    def test_high_skill_match(self):
        engine = MatchingEngine()
        result = engine.match(
            candidate_skills=["python", "fastapi", "postgresql", "docker"],
            required_skills=["python", "fastapi", "postgresql"],
            preferred_skills=["kubernetes"],
            candidate_years=5.0,
            required_years=3.0,
        )
        assert result.match_score >= 70.0
        assert "python" in result.matched_skills
        assert result.skill_match >= 70.0

    def test_low_skill_match(self):
        engine = MatchingEngine()
        result = engine.match(
            candidate_skills=["java"],
            required_skills=["python", "fastapi", "postgresql", "docker"],
            candidate_years=1.0,
            required_years=5.0,
        )
        assert result.match_score < 60.0
        assert len(result.missing_skills) >= 3


class TestHiringHealthEngine:
    def test_compute_health_metrics(self):
        engine = HiringHealthEngine()
        metrics = engine.compute(
            hires=[{"created_at": None, "hired_at": None}],
            interviews=[{"recommendation": "hire", "interview_score": 80}],
            offers=[{"status": "accepted"}, {"status": "declined"}],
            candidate_scores=[75.0, 82.0, 68.0],
            hires_last_30d=2,
            open_roles=3,
        )
        assert 0 <= metrics.hiring_health_score <= 100
        assert metrics.offer_acceptance_rate == 50.0
        assert metrics.candidate_quality_score > 0

"""Resume Processing Engine.

Accepts PDF / DOCX / TXT, extracts raw text, and produces a structured
candidate profile (skills, education, experience, projects).
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.utils import text as T

logger = get_logger(__name__)


@dataclass
class StructuredProfile:
    """The structured candidate profile produced from a resume."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    years_experience: float = 0.0
    raw_text: str = ""

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "education": self.education,
            "experience": self.experience,
            "projects": self.projects,
            "years_experience": self.years_experience,
        }


_SECTION_HEADERS = {
    "education": ["education", "academic", "qualifications"],
    "experience": ["experience", "employment", "work history", "professional experience"],
    "projects": ["projects", "personal projects", "selected projects"],
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
}

_EDU_KEYWORDS = ("university", "college", "institute", "bachelor", "master", "phd",
                 "b.tech", "m.tech", "b.sc", "m.sc", "mba", "degree")


class ResumeProcessingEngine:
    """Parses resume bytes into a :class:`StructuredProfile`."""

    SUPPORTED = {"pdf", "docx", "txt"}

    def extract_text(self, content: bytes, file_type: str) -> str:
        ft = file_type.lower().lstrip(".")
        if ft not in self.SUPPORTED:
            raise ValueError(f"Unsupported resume type: {file_type}")
        if ft == "txt":
            return content.decode("utf-8", errors="ignore")
        if ft == "pdf":
            return self._extract_pdf(content)
        return self._extract_docx(content)

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:  # pragma: no cover
            logger.warning("pypdf_missing")
            return content.decode("utf-8", errors="ignore")
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            import docx
        except ImportError:  # pragma: no cover
            logger.warning("python_docx_missing")
            return content.decode("utf-8", errors="ignore")
        document = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs)

    def parse(self, content: bytes, file_type: str, filename: str | None = None) -> StructuredProfile:
        raw = self.extract_text(content, file_type)
        return self.parse_text(raw, filename=filename)

    def parse_text(self, raw: str, filename: str | None = None) -> StructuredProfile:
        lines = [ln.strip() for ln in (raw or "").splitlines() if ln.strip()]
        profile = StructuredProfile(raw_text=raw)
        profile.email = T.extract_email(raw)
        profile.phone = T.extract_phone(raw)
        profile.skills = T.extract_skills(raw)
        profile.years_experience = T.extract_years_experience(raw)
        profile.full_name = self._guess_name(lines, filename)
        sections = self._split_sections(lines)
        profile.education = self._parse_education(sections.get("education", []))
        profile.experience = self._parse_experience(sections.get("experience", []))
        profile.projects = self._parse_projects(sections.get("projects", []))
        logger.info(
            "resume_parsed",
            skills=len(profile.skills),
            experience=len(profile.experience),
            education=len(profile.education),
        )
        return profile

    # ---- helpers ----
    @staticmethod
    def _guess_name(lines: list[str], filename: str | None) -> str | None:
        for ln in lines[:5]:
            if "@" in ln or any(ch.isdigit() for ch in ln):
                continue
            words = ln.split()
            if 1 < len(words) <= 4 and all(w[0].isupper() for w in words if w[:1].isalpha()):
                return ln.title()
        if filename:
            stem = re.sub(r"[_\-.]+", " ", filename.rsplit(".", 1)[0])
            return stem.title()
        return None

    def _split_sections(self, lines: list[str]) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for ln in lines:
            low = ln.lower().strip(": ")
            matched = next(
                (key for key, names in _SECTION_HEADERS.items()
                 if any(low == n or low.startswith(n) for n in names) and len(low) < 40),
                None,
            )
            if matched:
                current = matched
                sections.setdefault(current, [])
                continue
            if current:
                sections[current].append(ln)
        return sections

    @staticmethod
    def _parse_education(lines: list[str]) -> list[dict]:
        out: list[dict] = []
        for ln in lines:
            if any(k in ln.lower() for k in _EDU_KEYWORDS):
                out.append({"institution": ln, "raw": ln})
        return out

    @staticmethod
    def _parse_experience(lines: list[str]) -> list[dict]:
        out: list[dict] = []
        for ln in lines:
            if re.search(r"\b(19|20)\d{2}\b", ln) or " at " in ln.lower() or "|" in ln:
                out.append({"title": ln, "raw": ln})
        # fall back: treat each line as a bullet
        if not out and lines:
            out = [{"title": lines[0], "raw": " ".join(lines[:5])}]
        return out

    @staticmethod
    def _parse_projects(lines: list[str]) -> list[dict]:
        return [{"name": ln, "raw": ln} for ln in lines if len(ln) > 5][:20]

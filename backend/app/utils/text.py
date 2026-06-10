"""Lightweight, dependency-free text utilities used by the engines.

These deterministic helpers keep the matching / resume engines functional
even when no LLM is configured (offline mode).
"""
from __future__ import annotations

import re

# A pragmatic skills taxonomy used for keyword-based skill extraction.
SKILL_TAXONOMY: set[str] = {
    # languages
    "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++",
    "c#", "ruby", "php", "kotlin", "swift", "scala", "r", "sql",
    # web / frameworks
    "fastapi", "django", "flask", "react", "vue", "angular", "node", "nodejs",
    "express", "spring", "spring boot", "rails", "next.js", "svelte", "graphql",
    # data / ml
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "machine learning", "deep learning", "nlp", "llm", "langchain", "langgraph",
    "data science", "data engineering", "spark", "hadoop", "airflow", "dbt",
    # infra / devops
    "docker", "kubernetes", "terraform", "ansible", "aws", "gcp", "azure",
    "ci/cd", "jenkins", "github actions", "linux", "redis", "kafka", "rabbitmq",
    "celery", "nginx",
    # databases
    "postgresql", "postgres", "mysql", "mongodb", "elasticsearch", "dynamodb",
    "sqlite", "cassandra", "snowflake", "bigquery",
    # practices
    "microservices", "rest", "api design", "system design", "tdd", "agile",
    "scrum", "leadership", "mentoring", "architecture", "distributed systems",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]*")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
_YEARS_RE = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years|yrs|year)", re.IGNORECASE)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def extract_skills(text: str) -> list[str]:
    """Extract known skills from free text using the taxonomy."""
    if not text:
        return []
    blob = " " + normalize(text) + " "
    found: list[str] = []
    for skill in SKILL_TAXONOMY:
        needle = f" {skill} "
        if needle in blob or blob.find(f" {skill},") != -1 or blob.find(f" {skill}.") != -1:
            found.append(skill)
    return sorted(set(found))


def extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text or "")
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = _PHONE_RE.search(text or "")
    return match.group(0).strip() if match else None


def extract_years_experience(text: str) -> float:
    """Best-effort extraction of total years of experience."""
    matches = _YEARS_RE.findall(text or "")
    if not matches:
        return 0.0
    return max(float(m) for m in matches)


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two sets in the range [0, 1]."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def coverage(required: set[str], candidate: set[str]) -> float:
    """Fraction of required items covered by the candidate set."""
    if not required:
        return 1.0
    return len(required & candidate) / len(required)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))

# Celestra Hiring AI

**Your AI Hiring Department**

An autonomous hiring operating system — not an ATS, not a resume storage system, not a recruitment CRM. Celestra finds, evaluates, selects, hires, and onboards talent with minimal recruiter involvement.

---

## Architecture

```
Hiring AI Network
├── Workforce Planning Agent      → /workforce
├── Job Intelligence Agent        → /job
├── Talent Discovery Agent        → /talent
├── Candidate Intelligence Agent  → /candidate
├── Qualification Agent           → /qualification
├── Interview Intelligence Agent  → /interview
├── Assessment Agent              → /assessment
├── Reference Verification Agent  → /verification
├── Offer Agent                   → /offer
├── Onboarding Agent              → /onboarding
└── Hiring Chief Agent            → /chief
```

**Engines:** Resume Processing · Candidate Matching · Hiring Health

**Infrastructure:** FastAPI · PostgreSQL · Redis · Celery · LangGraph · JWT Auth

---

## Quick Start

### 1. Clone & configure

```bash
cd backend
cp .env.example .env
# Edit .env as needed (LLM_OFFLINE_MODE=true works without an API key)
```

### 2. Run with Docker (recommended)

```bash
docker compose up --build
```

Services:
| Service  | URL                        |
|----------|----------------------------|
| API      | http://localhost:8000      |
| Docs     | http://localhost:8000/api/v1/docs |
| Metrics  | http://localhost:8000/metrics     |
| Postgres | localhost:5432             |
| Redis    | localhost:6379             |

### 3. Run locally (without Docker)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Default admin credentials

```
Email:    admin@celestra.ai
Password: Admin@12345
```

---

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/login` | JWT login |
| `POST /api/v1/auth/refresh` | Refresh token |
| `GET  /api/v1/dashboard` | Hiring KPIs (single endpoint) |
| `POST /api/v1/workforce/analyze` | Workforce planning |
| `POST /api/v1/job/blueprint` | Job Intelligence Agent |
| `POST /api/v1/talent/discover` | Talent discovery |
| `POST /api/v1/candidate/resume` | Resume upload (PDF/DOCX/TXT) |
| `POST /api/v1/candidate/{id}/analyze` | Candidate dossier |
| `POST /api/v1/qualification/rank` | Candidate ranking |
| `POST /api/v1/interview/plan` | Interview plan generation |
| `POST /api/v1/assessment/{id}/evaluate` | Assessment evaluation |
| `POST /api/v1/verification/{id}/verify` | Reference verification |
| `POST /api/v1/offer/generate` | Offer generation |
| `POST /api/v1/onboarding/run` | Onboarding workflow |
| `GET  /api/v1/chief/report` | Executive briefing |
| `POST /api/v1/chief/orchestrate` | Full hiring workflow |
| `POST /api/v1/reports/generate` | Report generation |
| `WS   /api/v1/ws/hiring` | Real-time alerts |

---

## Background Jobs

| Schedule | Job |
|----------|-----|
| Hourly | Candidate refresh, Qualification refresh, Matching refresh |
| Daily | Hiring summary, Interview summary |
| Weekly | Hiring report |
| Monthly | Talent intelligence report |

Start workers:
```bash
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

---

## Database Migrations

```bash
# Generate migration from ORM models
alembic revision --autogenerate -m "describe change"

# Apply migrations
alembic upgrade head
```

---

## Testing

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Project Structure

```
backend/
├── app/
│   ├── agents/          # 11 AI agents + LangGraph orchestration
│   ├── api/             # FastAPI routers
│   ├── core/            # Config, security, logging, exceptions
│   ├── database/        # SQLAlchemy engine & session
│   ├── engines/         # Resume, Matching, Hiring Health engines
│   ├── models/          # 17 ORM models
│   ├── repositories/    # Repository pattern
│   ├── schemas/         # Pydantic DTOs
│   ├── services/        # Business logic layer
│   ├── utils/           # Text processing utilities
│   └── workers/         # Celery background jobs
├── alembic/             # Database migrations
├── tests/               # Unit + integration tests
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Roles (RBAC)

| Role | Access |
|------|--------|
| Admin | Full access |
| Founder | Executive + all hiring |
| HR Manager | Workforce, offers, chief, reports |
| Recruiter | Candidates, interviews, assessments |
| Hiring Manager | View + interview feedback |
| Viewer | Read-only dashboard |

---

## AI Configuration

Set in `.env`:
```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_OFFLINE_MODE=false
```

With `LLM_OFFLINE_MODE=true` (default), all agents run deterministically without external API calls — ideal for development and testing.

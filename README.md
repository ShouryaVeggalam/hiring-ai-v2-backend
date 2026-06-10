# Celestra Hiring AI — v2

**Your AI Hiring Department.** An autonomous hiring operating system that finds, evaluates, selects, hires, and onboards talent with minimal recruiter involvement.

This repository contains the **backend**. The **frontend** lives in a separate repository.

| Layer | Repository |
|-------|------------|
| Backend (this repo) | https://github.com/ShouryaVeggalam/hiring-ai-v2-backend |
| Frontend | https://github.com/ShouryaVeggalam/hiring-ai-v2-frontend |

---

## Repository layout

```
hiring-ai-v2-backend/
└── backend/        # FastAPI backend (see backend/README.md)
```

Full backend documentation: [`backend/README.md`](backend/README.md).

---

## Full-stack setup

### 1. Backend

```bash
cd backend
cp .env.example .env
docker compose up --build
```

Backend runs at `http://localhost:8000` with API docs at `http://localhost:8000/api/v1/docs`.

### 2. Frontend

```bash
git clone https://github.com/ShouryaVeggalam/hiring-ai-v2-frontend.git
cd hiring-ai-v2-frontend
npm install
npm run dev
```

The frontend dev server typically runs at `http://localhost:5173` (Vite) or `http://localhost:3000` (Next.js).

---

## Connecting frontend → backend

The frontend should call the backend at:

```
API base URL:  http://localhost:8000/api/v1
WebSocket:     ws://localhost:8000/api/v1/ws/hiring
```

Set this in the frontend environment (e.g. `.env`):

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
# or, for Next.js:
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

The backend's CORS is pre-configured to allow `http://localhost:3000` and `http://localhost:5173`.
To add more origins, edit `BACKEND_CORS_ORIGINS` in `backend/.env`:

```
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","https://your-frontend.example.com"]
```

### Default admin credentials

```
Email:    admin@celestra.ai
Password: Admin@12345
```

---

## Tech stack

Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy · Alembic · Redis · Celery · LangGraph · LangChain · JWT · Docker

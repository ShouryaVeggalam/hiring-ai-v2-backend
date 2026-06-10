# Deployment Guide — Celestra Hiring AI

| Component | Platform | URL |
|-----------|----------|-----|
| Backend | **Render** (free) | `https://celestra-hiring-api.onrender.com` |
| Frontend | **Vercel** (free) | `https://hiring-ai-v2-frontend.vercel.app` |

---

## Backend on Render

### If deploy keeps failing — update these manually

Go to **Render Dashboard → celestra-hiring-api → Settings** and set:

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements-prod.txt` |
| **Start Command** | `uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --workers 1` |
| **Health Check Path** | `/api/v1/health` |

**Environment variables** (required):

| Key | Value |
|-----|-------|
| `RENDER` | `true` |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `LLM_OFFLINE_MODE` | `true` |
| `AUTO_CREATE_TABLES` | `true` |
| `DATABASE_URL` | *(link to Postgres — Internal URL)* |
| `SECRET_KEY` | *(generate random 64-char string)* |
| `BACKEND_CORS_ORIGINS` | `*` |
| `FIRST_SUPERUSER_EMAIL` | `admin@celestra.ai` |
| `FIRST_SUPERUSER_PASSWORD` | *(pick a strong password)* |

> **Important:** `BACKEND_CORS_ORIGINS` must be `*` or comma-separated URLs — **not** JSON like `["*"]`.

Remove unused Redis env vars (`REDIS_URL`, `CELERY_BROKER_URL`) if you're not running workers.

### First-time Blueprint deploy

1. [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint**
2. Select repo `hiring-ai-v2-backend`
3. Click **Apply**

### Verify backend is live

```
GET https://<your-service>.onrender.com/api/v1/health
GET https://<your-service>.onrender.com/api/v1/docs
```

---

## Frontend on Vercel

Your frontend is deployed at:
**https://hiring-ai-v2-frontend.vercel.app**

> **Note:** The frontend currently uses **mock data** (`src/lib/mock-data.ts`). It does not call the backend API yet. The UI works standalone; connecting it to Render is a separate step.

When you're ready to connect the frontend to Render, add this env var in **Vercel → Project → Settings → Environment Variables**:

```
NEXT_PUBLIC_API_BASE_URL = https://<your-render-service>.onrender.com/api/v1
```

Then update `BACKEND_CORS_ORIGINS` on Render to include your Vercel URL:
```
https://hiring-ai-v2-frontend.vercel.app,https://hiring-ai-v2-frontend-shouryaveggalams-projects.vercel.app
```

---

## Why previous deploys failed

| Error | Cause | Fix |
|-------|-------|-----|
| `SettingsError: BACKEND_CORS_ORIGINS` | pydantic tried to JSON-decode `*` as a list | Fixed — field is now a plain string |
| `Exited with status 1` (startup) | App blocked on DB init before binding PORT | Fixed — DB init runs in background |
| `bash start.sh` failure | Windows CRLF line endings | Removed — direct uvicorn command |
| Heavy deps OOM | LangChain/Celery on free tier | Fixed — `requirements-prod.txt` is slim |

---

## Default admin (after backend is live)

```
Email:    admin@celestra.ai
Password: value of FIRST_SUPERUSER_PASSWORD in Render env
```

# Deployment Guide — Celestra Hiring AI

Free deployment using **Render** (backend) and **Vercel** (frontend).

| Component | Platform | Repo |
|-----------|----------|------|
| Backend (FastAPI + Postgres + Redis) | Render | https://github.com/ShouryaVeggalam/hiring-ai-v2-backend |
| Frontend | Vercel | https://github.com/ShouryaVeggalam/hiring-ai-v2-frontend |

---

## Part 1 — Backend on Render (free)

The repo ships a [`render.yaml`](render.yaml) Blueprint that provisions everything on Render's free tier:
- a **web service** (FastAPI),
- a **PostgreSQL** database,
- a **Key Value (Redis)** instance.

### Steps

1. Go to <https://dashboard.render.com> and sign in with GitHub.
2. Click **New → Blueprint**.
3. Select the **`hiring-ai-v2-backend`** repository.
4. Render reads `render.yaml` and shows the services to create. Click **Apply**.
5. Wait for the build to finish (~3–5 min). Tables are created automatically on first boot (`AUTO_CREATE_TABLES=true`).

Your API will be live at:

```
https://celestra-hiring-api.onrender.com
```

(the exact subdomain is shown in the dashboard).

Verify:
```
GET https://celestra-hiring-api.onrender.com/api/v1/health
Docs: https://celestra-hiring-api.onrender.com/api/v1/docs
```

### Default admin
- Email: `admin@celestra.ai`
- Password: auto-generated — copy it from the web service's **Environment** tab (`FIRST_SUPERUSER_PASSWORD`).

> **Free-tier note:** the web service sleeps after ~15 min of inactivity and cold-starts on the next request (a few seconds). The free PostgreSQL instance expires ~30 days after creation. Background Celery workers are not included on the free tier (see comments in `render.yaml`); the API runs fully without them.

---

## Part 2 — Frontend on Vercel (free)

1. Go to <https://vercel.com> and sign in with GitHub.
2. Click **Add New → Project** and import **`hiring-ai-v2-frontend`**.
3. Vercel auto-detects the framework (Vite / Next.js).
4. Add an **Environment Variable** pointing at the Render backend:

   For **Vite**:
   ```
   VITE_API_BASE_URL = https://celestra-hiring-api.onrender.com/api/v1
   ```
   For **Next.js**:
   ```
   NEXT_PUBLIC_API_BASE_URL = https://celestra-hiring-api.onrender.com/api/v1
   ```
   (Use the exact variable name your frontend reads.)

5. Click **Deploy**. Your frontend will be live at:
   ```
   https://hiring-ai-v2-frontend.vercel.app
   ```

---

## Part 3 — Connect the two (CORS)

After the frontend is live, allow its origin on the backend:

1. In Render → `celestra-hiring-api` → **Environment**, set:
   ```
   BACKEND_CORS_ORIGINS = ["https://hiring-ai-v2-frontend.vercel.app"]
   ```
   (Add any Vercel preview URLs you use too.)
2. Save — Render redeploys automatically.

The API uses **bearer tokens** (not cookies), so requests work cross-origin once the origin is allowlisted.

---

## Endpoint summary

| Purpose | URL |
|---------|-----|
| API base | `https://celestra-hiring-api.onrender.com/api/v1` |
| Swagger docs | `https://celestra-hiring-api.onrender.com/api/v1/docs` |
| Health check | `https://celestra-hiring-api.onrender.com/api/v1/health` |
| WebSocket | `wss://celestra-hiring-api.onrender.com/api/v1/ws/hiring` |

---

## Alternative: deploy backend via Docker on Render

The repo also has a `backend/Dockerfile`. Instead of the Python runtime you can
create a web service with **Runtime = Docker**, **Root Directory = `backend`**,
and the same environment variables as in `render.yaml`.

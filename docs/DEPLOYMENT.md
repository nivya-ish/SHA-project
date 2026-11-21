# Deployment Guide (Public URL: Render + Supabase)

This project is prepared for public deployment without requiring end users to install Python, VS Code, Docker, or Kubernetes.

**Target architecture**
- **Frontend:** React + Vite on **Render Static Site**
- **Backend:** FastAPI on **Render Web Service**
- **Database:** **Supabase PostgreSQL**
- **AI:** Google **Gemini API** (backend-only)
- **RAG:** ChromaDB with bundled curated medical docs and startup reconstruction + keyword fallback strategy

> **Important:** No public URL was deployed or tested from this coding environment. Complete the steps below with your own Render/Supabase/Gemini accounts and verify the live URL before sharing.  
> **Credentials/access checklist:** see [`docs/CREDENTIALS_NEEDED.md`](CREDENTIALS_NEEDED.md) for the exact values/accounts you must provide (no secrets included).  
> **Verification status:** see [`docs/TEST_REPORT.md`](TEST_REPORT.md).

## 1. Prerequisites / What You Must Provide
- A Render account (and this repository pushed to GitHub/GitLab or connected to Render)
- A Supabase project and PostgreSQL connection string (`DATABASE_URL`)
- (Optional but recommended) A Gemini API key (`GEMINI_API_KEY`) for live AI explanations
  - If omitted, the app still works with safe rule-based fallback explanations (no fabricated Gemini output)

## 2. Prepare Supabase PostgreSQL
1. Create a Supabase project.
2. Get the Postgres connection string from Supabase (Database settings).
3. Use a SQLAlchemy-compatible URL. Recommended:
   - `postgresql+psycopg2://USER:PASSWORD@HOST:PORT/postgres?sslmode=require`
4. Set it as `DATABASE_URL` in the Render backend service environment.
5. Tables: the backend performs best-effort `create_all` on startup; Alembic migration `backend/alembic/versions/0001_create_analysis_records.py` is also included for managed migrations.

## 3. Deploy Backend (Render Web Service)
You can use `render.yaml` (Blueprint) or configure manually.

### Key backend settings
- **Root Directory:** repository root (`.`)
- **Build Command:** `pip install --upgrade pip && pip install -r backend/requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
- **Health Check Path:** `/health`

### Required/important backend environment variables
- `APP_ENV=production`
- `DEBUG=false`
- `API_V1_PREFIX=/api/v1`
- `DATABASE_URL=<your Supabase Postgres URL>` (backend normalizes common `postgres://`/`postgresql://` forms)
- `CORS_ORIGINS=https://<your-frontend>.onrender.com` (comma-separated if multiple; no trailing slash)
- `GEMINI_API_KEY=<your key>` (optional; leave empty to use fallback)
- `GEMINI_ENABLED=true` (or `false` to force fallback)
- `GEMINI_MODEL=gemini-1.5-flash` (or your preferred supported model)
- `CHROMA_PERSIST_DIR=rag/chroma_db`
- `MEDICAL_DOCS_DIR=data/medical_docs`
- `MODEL_ARTIFACT_DIR=ml/artifacts`
- `TRAIN_DATA_PATH=data/raw/Training.csv`
- `TEST_DATA_PATH=data/raw/Testing.csv`

After deploy, verify:
- `https://<backend>.onrender.com/health` returns `{"status":"ok",...}`
- `https://<backend>.onrender.com/api/v1/health` reports component readiness

## 4. Deploy Frontend (Render Static Site)
### Key frontend settings
- **Root Directory:** `frontend`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`

### Frontend environment variable
- `VITE_API_BASE_URL=https://<your-backend>.onrender.com/api/v1`

### SPA routing (required for React Router)
- `frontend/public/_redirects` is included with:
  ```
  /* /index.html 200
  ```
- `render.yaml` also defines a rewrite route to `/index.html` for static hosting.

Redeploy/rebuild frontend after setting/changing `VITE_API_BASE_URL` (Vite embeds env vars at build time).

## 5. CORS and Frontend-Backend Communication
- Set backend `CORS_ORIGINS` to the exact deployed frontend origin(s), e.g. `https://smart-health-assistant-frontend.onrender.com`
- Do not use `localhost` origins in production unless needed for testing.
- Frontend uses `VITE_API_BASE_URL` (no hardcoded production localhost dependency).

## 6. RAG / ChromaDB Persistence & Reconstruction Strategy
- Curated medical reference documents are bundled in `data/medical_docs/` and shipped with the backend.
- On startup, the backend attempts best-effort ingestion/index setup for ChromaDB (`CHROMA_PERSIST_DIR`).
- **Render/ephemeral filesystem note:** persistent disk may not be available on all plans/instances. If Chroma persistence is unavailable or reset, the app can reconstruct from bundled docs and/or use **keyword retrieval fallback over bundled medical documents** so medical information retrieval remains available.
- `POST /api/v1/rag/reindex` can be used to reingest/reindex docs when needed.
- `GET /api/v1/rag/status` reports readiness/counts/fallback mode.

## 7. Security & Secrets
- Keep `GEMINI_API_KEY` and `DATABASE_URL` in server-side environment variables only (Render dashboard / secret env vars). Never put them in frontend code or `VITE_*` variables.
- `.env.example` files are provided; `.gitignore` excludes `.env`, `.env.*` (except examples), keys, logs, local DB files, etc.
- Use HTTPS public URLs in production.

## 8. Post-Deploy Verification Checklist (you must perform on your live URL)
- [ ] Frontend public URL loads (Render Static Site)
- [ ] Backend `/health` and `/api/v1/health` are healthy
- [ ] Symptom analysis works end-to-end (NLP -> ML possible conditions -> RAG info -> Gemini/fallback explanation)
- [ ] Duration-only input is rejected and does **not** trigger prediction
- [ ] Results show possible conditions, supporting symptoms, explanations, medical info/sources, follow-up questions, safe next steps, and disclaimer/emergency guidance
- [ ] History save/list/detail/delete works with Supabase DB
- [ ] CORS allows frontend-to-backend requests without browser errors
- [ ] Gemini live response works (if key configured) or safe fallback works (if not)

## 9. Local Development (optional)
```powershell
# Backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
copy .env.example .env
cd backend
py -m pytest tests -q
uvicorn app.main:app --reload --app-dir . --host 0.0.0.0 --port 8000

# Frontend (requires Node.js/npm)
cd frontend
npm install
# set VITE_API_BASE_URL=http://localhost:8000/api/v1 in frontend/.env for local dev
npm run dev
```

## 10. Known Deployment Limitations
- This environment did **not** perform an actual Render/Supabase deployment or public URL test.
- Live Supabase connectivity and live Gemini responses depend on credentials you provide.
- Semantic embedding quality/performance for RAG depends on runtime availability of embedding dependencies/models; keyword fallback over curated docs is available as a resilience strategy.
- This is an academic/experimental healthcare decision-support prototype, not a clinically validated diagnostic system.

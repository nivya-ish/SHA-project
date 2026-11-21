# Testing & Verification

**Final consolidated test report:** see [`docs/TEST_REPORT.md`](TEST_REPORT.md) for the complete pass/fail/partial/untested matrix, exact commands, results, and limitations.

## Automated Tests Actually Executed (in this environment)

### Backend (pytest) — PASSED
**Command run (from `backend/`):**
```powershell
py -m pytest tests -q
```
**Result (actual):** `19 passed, 0 failed, 1 warning` (exit code 0)  
**Warning:** `chromadb` telemetry deprecation warning on Python 3.14 (`asyncio.iscoroutinefunction`), non-functional.

**Coverage includes:**
- Dataset loading/cleaning/preprocessing, duplicate header handling, binary features, feature mapping consistency
- NLP symptom extraction/normalization/mapping, duration extraction (separate), empty input rejection, **duration-only rejection with no invented symptoms and no ML prediction**, embedded duration handling, unsupported symptoms reporting, invalid/gibberish rejection
- ML artifact loading, training/inference feature consistency, prediction output structure
- RAG chunking and retrieval fallback over local curated medical documents
- Database CRUD (SQLite test configuration)
- API health, validation, response structure, error/invalid-input handling, history endpoints
- End-to-end analysis workflow via FastAPI `TestClient`

Prior run logs are also saved at `docs/backend_test_run.log` and `docs/backend_test_run_initial.log` (existing in workspace).

### Backend startup/import sanity check — PASSED
**Command run:**
```powershell
cd backend
$env:PYTHONPATH=(Get-Location).Path
py -c "from app.main import app; print('app-import-ok')"
```
**Result (actual):** `app-import-ok` (exit code 0)

## Checks Not Fully Executable in This Environment

### Frontend startup/build/tests — NOT RUN (tooling unavailable)
- Node.js/npm were **not installed** in this environment, so the following were **not executed** here:
  - `npm install`
  - `npm run dev` (frontend startup)
  - `npm run build` (production build for Render Static Site)
  - frontend tests (e.g. Vitest), if configured
- Frontend code/config is present and updated for env-based API URL (`VITE_API_BASE_URL`), SPA routing (`frontend/public/_redirects`), and existing components/pages were preserved/improved.

### Live Gemini API integration — NOT RUN (credential unavailable)
- Gemini integration is implemented backend-only with safe fallback (`GEMINI_API_KEY`, env config). No API key was provided in this environment, so live Gemini responses were **not tested**; fallback explanations are implemented and covered by service/test logic paths.

### Live Supabase PostgreSQL connection — NOT RUN (credential/service unavailable)
- Database layer is implemented (SQLAlchemy, Alembic, normalized Postgres URL support for Supabase/Render). Automated DB tests passed using SQLite. A live Supabase/PostgreSQL connection/migration against a real instance was **not tested** because credentials/service were not provided.

### RAG semantic embeddings (sentence-transformers) — PARTIALLY VERIFIED
- RAG service, curated medical docs (`data/medical_docs/`), ChromaDB integration, ingestion/reindex, and retrieval are implemented.
- Automated RAG tests passed (keyword fallback over local docs).
- `sentence-transformers` embedding model runtime was not installed/validated in this environment; retrieval gracefully falls back to keyword search over bundled curated documents when embeddings/vector query are unavailable. Full semantic embedding indexing should be verified in a deployed/runtime environment with dependencies/models available.

### Docker/Kubernetes runtime — NOT RUN
- Docker/Compose and Kubernetes manifests are present, but Docker/daemon and kubectl/cluster were unavailable in this environment; container builds and cluster deployments were **not executed** here. Public deployment target for this task is Render + Supabase (no Docker Desktop/K8s required).

### Public URL end-to-end deployment — NOT TESTED
- Render/Supabase deployment configuration and instructions were prepared (`render.yaml`, env templates, docs), but an actual public URL was **not deployed or browser-tested** in this environment. Do **not** consider the app publicly deployed until you deploy with your credentials and verify the live URL.

## How to Re-run Tests Locally

### Backend
```powershell
# from project root
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
py -m pytest tests -q
```

### Frontend (requires Node.js/npm)
```powershell
cd frontend
npm install
npm run dev      # local dev
npm run build    # production build check
```

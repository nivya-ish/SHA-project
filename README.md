# Smart Health Assistant

AI-powered healthcare decision-support web application (**academic/experimental, not clinically validated**).

The system lets a user enter symptoms in natural language plus a separate duration, validates/processes the input with NLP, predicts **possible conditions (unconfirmed)** using a model trained on the provided dataset, retrieves relevant curated medical information via RAG (ChromaDB), and generates a cautious explanation using Gemini (backend-only) with a safe fallback when unavailable.

> **Medical disclaimer:** This is a student prototype for decision support and education only. It does **not** provide confirmed diagnoses, prescriptions, or emergency medical services. Always consult a qualified healthcare professional.

## End-to-End Workflow
1. User enters symptoms in natural language and provides duration separately.
2. NLP extracts symptoms, normalizes/maps them to dataset features, and extracts duration (duration is never a symptom).
3. Validation rejects empty input, irrelevant/unmappable input, and duration-only input (no invented symptoms, no ML prediction).
4. ML model predicts possible conditions from the actual provided dataset/artifacts.
5. RAG retrieves relevant information from curated medical reference documents (`data/medical_docs/`) using ChromaDB with a resilience/fallback strategy.
6. Gemini (backend-only) generates an understandable, cautious explanation from actual ML + retrieved context; safe fallback is used if Gemini is unavailable.
7. UI displays possible conditions, supporting symptoms, explanations, medical information/sources, follow-up questions, safe next steps, and medical/emergency disclaimers.
8. Completed analyses can be saved to history (database-backed when configured).

## Tech Stack
- **Frontend:** React + Vite (JavaScript, responsive UI)
- **Backend:** FastAPI (Python), REST APIs, Pydantic validation
- **ML:** scikit-learn, pandas, NumPy (artifacts in `ml/artifacts/`, retrain via `train_model.py`)
- **NLP:** Rule-based extraction/normalization/mapping + duration parsing and input validation
- **RAG:** ChromaDB + curated medical docs, startup reconstruction and keyword fallback for resilience
- **LLM:** Google Gemini API (server-side only, env-configured, safe fallback)
- **Database:** SQLAlchemy + Alembic; PostgreSQL (Supabase) for production, SQLite supported for local/dev/tests
- **Deployment target:** Render Static Site (frontend) + Render Web Service (backend) + Supabase PostgreSQL

## Repository Highlights
- `backend/` - FastAPI app, services (NLP/ML/RAG/Gemini), DB models/migrations, tests
- `frontend/` - React/Vite UI (landing, dashboard, symptom analysis, results, history)
- `data/raw/` - provided dataset (`Training.csv`, `Testing.csv`)
- `data/medical_docs/` - curated RAG knowledge base
- `ml/artifacts/` - trained model, feature columns, labels, metrics/reports
- `docs/` - dataset/model/API/testing/deployment/medical safety documentation
- `render.yaml`, `runtime.txt` - Render deployment configuration

See `docs/PROJECT_STRUCTURE.md` for full structure.

## Dataset & Model (Actual)
- Dataset: `Training.csv` (4920 rows, 132 symptom features + `prognosis`, 41 conditions, duplicate `fluid_overload` header handled) and `Testing.csv` (42 rows)
- Cleaning/feature alignment implemented in `backend/app/ml/data_utils.py`
- Selected model: **LogisticRegression** (from saved artifacts/metadata)
- Reported metrics (from existing executed training artifacts): train/test accuracy, precision, recall, F1 weighted = **1.0** on provided split (not clinically validated)

Details: `docs/DATASET.md`, `docs/MODEL_TRAINING.md`, `docs/dataset_analysis.json`, `ml/artifacts/metadata.json`

## Local Development

### Backend
```powershell
# from project root
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
copy .env.example .env
# edit .env as needed (DATABASE_URL, CORS_ORIGINS, GEMINI_API_KEY optional)

# run tests (recommended)
cd backend
py -m pytest tests -q

# start API
uvicorn app.main:app --reload --app-dir . --host 0.0.0.0 --port 8000
```
- Health: `http://localhost:8000/health`
- API: `http://localhost:8000/api/v1`

### Frontend (requires Node.js/npm)
```powershell
cd frontend
npm install
copy .env.example .env
# set VITE_API_BASE_URL=http://localhost:8000/api/v1 for local dev
npm run dev
# npm run build
```
> Node.js/npm were not available in this execution environment, so frontend install/dev/build could not be executed here. Render Static Site can build it using the provided configuration.

### Model Retraining
```powershell
py train_model.py --train data/raw/Training.csv --test data/raw/Testing.csv --artifacts ml/artifacts
```

## Environment Variables (summary)
Configure via `.env` (local backend), Render service env vars, and frontend `VITE_API_BASE_URL`.
- `DATABASE_URL` - SQLite local fallback or Supabase PostgreSQL URL (`postgres://`/`postgresql://` normalized automatically)
- `CORS_ORIGINS` - allowed frontend origin(s), comma-separated
- `GEMINI_API_KEY`, `GEMINI_ENABLED`, `GEMINI_MODEL` - backend-only Gemini config (optional; fallback available)
- `PORT` - injected by Render (backend binds `0.0.0.0:$PORT` via start command)
- `VITE_API_BASE_URL` - frontend -> backend API base (e.g. `https://<backend>.onrender.com/api/v1`)

Templates: `.env.example`, `frontend/.env.example`. **Never commit secrets.**

## Public Deployment (Render + Supabase, no Docker/Kubernetes required)
Prepared for:
- **Frontend:** Render Static Site (`frontend/`, build `npm install && npm run build`, publish `dist`, SPA rewrite via `frontend/public/_redirects` and `render.yaml`)
- **Backend:** Render Web Service (`uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`, health check `/health`)
- **Database:** Supabase PostgreSQL (`DATABASE_URL`)
- **Gemini:** backend env var `GEMINI_API_KEY`
- **RAG:** bundled curated docs with Chroma startup reconstruction and keyword fallback for hosted resilience

Full step-by-step instructions and verification checklist: **`docs/DEPLOYMENT.md`**

**Important:** No public URL was deployed or live-tested from this coding environment. You must deploy with your own Render/Supabase/(optional) Gemini credentials and verify the public URL end-to-end before sharing.

## API, Testing, and Safety Docs
- `docs/API.md` - endpoints, request/response, behavior
- `docs/TESTING.md` - actual executed tests and environment limitations
- `docs/DEPLOYMENT.md` - Render + Supabase deployment guide
- `docs/MEDICAL_SAFETY.md` - disclaimers, safety constraints, limitations

## Final Documentation & Deliverables (workspace)
- **Consolidated test report:** [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) (pass/fail/partial/untested matrix, exact commands/results, limitations)
- **Testing details/logs:** [`docs/TESTING.md`](docs/TESTING.md)
- **Deployment guide:** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- **Credentials/access required from you:** [`docs/CREDENTIALS_NEEDED.md`](docs/CREDENTIALS_NEEDED.md) (no secrets included/invented)
- **Local env placeholders (no real secrets):** `.env`, `frontend/.env` and templates `.env.example`, `frontend/.env.example`
- **Final package (latest project state, verified):** `Smart-Health-Assistant-Final.zip` (see delivery note/path in handoff; clean deployable archive excludes caches/venv/node_modules/local runtime DBs/logs; includes docs, source, configs, data, ML artifacts, and placeholder env templates/files as present)

## Verified in This Environment (actual)
- Backend tests: **19 passed, 0 failed, 1 warning** (`cd backend; py -m pytest tests -q`)
- Backend app import/startup sanity: **passed** (`app-import-ok`)
- Backend API smoke (local TestClient, fresh SQLite, Gemini disabled): **passed** — `/health`, `/api/v1/health`, valid analyze (predictions + retrieved sources + fallback explanation + history record), duration-only/empty rejection with no prediction/no record, RAG status (`keyword-over-medical-docs` fallback), history listing
- Critical safety: duration-only/empty/invalid inputs rejected with **no symptom invention and no ML prediction** (tests + smoke)
- RAG retrieval over bundled curated medical docs: **available** (keyword fallback verified); semantic embedding runtime not fully validated locally
- UI/UX source finalized in-place: symptom+separate duration flow, examples/validation/loading/error states, results sections (possible unconfirmed conditions, supporting symptoms, NLP/ML/RAG/AI separation, medical info/sources, follow-ups, safe next steps, urgency/emergency guidance, disclaimer), and “start new analysis”

## Not Executed Here (limitations)
- Frontend `npm install/dev/build/test` (Node.js/npm unavailable)
- Live Supabase PostgreSQL connection/migrations against a real instance (no credentials)
- Live Gemini API calls (no `GEMINI_API_KEY`)
- Full semantic embedding model runtime validation for RAG (`sentence-transformers` not installed locally; fallback available)
- Docker/Kubernetes runtime deployment (not required for target public deployment)
- **Actual public URL deployment/browser testing** — **no public HTTPS URL was deployed or live-tested** in this environment. Public deployment is prepared but not complete until you deploy with your credentials/access and verify the live URL.

## Security Notes
- API keys and DB credentials are server-side env vars only (never in frontend code)
- CORS is environment-configurable
- Pydantic request/response validation and safe error handling included
- Secrets protected by `.gitignore` and example env templates

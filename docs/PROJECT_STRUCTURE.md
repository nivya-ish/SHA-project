# Project Structure

```text
.
├── backend/                     # FastAPI backend, ML/NLP/RAG/Gemini services, DB, tests
│   ├── app/
│   │   ├── api/v1/              # API router/endpoints
│   │   ├── core/                # Settings/config (env, CORS, DB URL normalization, paths)
│   │   ├── db/                  # SQLAlchemy engine/session/base
│   │   ├── ml/                  # Dataset loading/cleaning/feature alignment utilities
│   │   ├── models/              # ORM models (analysis history)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   └── services/            # NLP, ML inference, RAG, Gemini, orchestration
│   ├── alembic/                 # DB migrations
│   ├── tests/                   # pytest suite (dataset/NLP/ML/RAG/DB/API/E2E)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # React + Vite frontend (Render Static Site ready)
│   ├── public/                  # SPA redirects for static hosting
│   ├── src/
│   │   ├── api/                 # API client (VITE_API_BASE_URL)
│   │   ├── components/          # UI components (layout, results, disclaimer, etc.)
│   │   ├── pages/               # Landing, Dashboard, Analyze, History
│   │   └── styles/              # Responsive healthcare-themed styling
│   ├── .env.example
│   └── package.json
├── data/
│   ├── raw/                     # Uploaded dataset copies (Training.csv, Testing.csv)
│   ├── medical_docs/            # Curated medical reference docs for RAG
│   └── processed/
├── ml/
│   ├── artifacts/               # Trained model + feature/label/metrics artifacts
│   └── training_run.log
├── rag/
│   └── chroma_db/               # Chroma persistence directory (reconstructable from bundled docs)
├── docs/                        # Dataset/model/API/testing/deployment/safety docs
├── k8s/                         # Kubernetes manifests (optional, preserved)
├── scripts/                     # Utility scripts placeholder
├── train_model.py               # Reusable ML training/evaluation/artifact generation
├── render.yaml                  # Render Blueprint (backend web service + frontend static site)
├── runtime.txt                  # Python runtime hint for Render
├── docker-compose.yml           # Local/container stack (optional, preserved)
├── .env.example                 # Root environment template (no secrets)
└── README.md
```

## Key Runtime Flow
1. Frontend collects symptoms + separate duration and calls backend API.
2. NLP validates/extracts/maps symptoms (duration never treated as symptom).
3. ML predicts possible conditions from trained dataset artifacts.
4. RAG retrieves relevant curated medical info (ChromaDB/embeddings when available; keyword fallback supported).
5. Gemini (backend-only) or safe fallback generates cautious explanation.
6. Results and history are returned/displayed with disclaimers and emergency guidance.

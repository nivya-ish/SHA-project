# API Documentation

Base URLs
- Local backend: `http://localhost:8000`
- API prefix: `/api/v1` (configurable via `API_V1_PREFIX`)
- Public deployment example: `https://<your-backend>.onrender.com` and `https://<your-backend>.onrender.com/api/v1`

## Core Endpoints

### `GET /`
Basic root/status response confirming the backend is running.

### `GET /health`
Lightweight health check for hosting platforms (Render health check path).
- Response: `{ "status": "ok", "app": "Smart Health Assistant" }`

### `GET /api/v1/health`
Detailed service health/readiness.
- Response fields:
  - `status`: overall API status
  - `app`: app name
  - `ml_ready`: ML artifacts loaded/available
  - `rag_ready`: RAG retrieval available (Chroma and/or bundled-doc keyword fallback)
  - `gemini_configured`: Gemini enabled and API key present
  - `database_ok`: database connectivity check

### `POST /api/v1/analyze`
Runs the end-to-end symptom analysis workflow.

**Request (JSON):**
```json
{
  "symptoms_text": "I have fever and cough",
  "duration_text": "3 days"
}
```
- `symptoms_text` (string): natural-language symptom description
- `duration_text` (string|null): separate duration field (kept separate from symptoms)

**Behavior:**
1. NLP extracts/normalizes symptoms and extracts duration separately.
2. Validation rejects empty input, irrelevant/unmappable symptom-only gibberish, and duration-only input (no symptom invention, no ML prediction for invalid cases).
3. ML predicts **possible conditions** from mapped dataset features (actual trained model artifacts).
4. RAG retrieves relevant curated medical information (ChromaDB/embeddings when available; keyword fallback over bundled medical docs when not).
5. Gemini generates a cautious explanation using ML results and retrieved context when configured; otherwise a safe rule-based fallback explanation is returned.
6. Completed analyses are persisted to the database (history) when DB is available.

**Response (JSON, simplified):**
```json
{
  "status": "completed | invalid_input | error",
  "message": "...",
  "nlp": {
    "extracted_symptoms": ["..."],
    "normalized_symptoms": ["..."],
    "mapped_features": ["..."],
    "unsupported_symptoms": ["..."],
    "duration": "3 days",
    "notes": ["..."]
  },
  "predictions": [
    {
      "condition": "Possible condition name",
      "probability": 0.82,
      "confidence_label": "higher model confidence",
      "supporting_symptoms": ["fever", "cough"]
    }
  ],
  "retrieved_sources": [
    {
      "title": "...",
      "source": "data/medical_docs/...",
      "snippet": "...",
      "score": 0.75
    }
  ],
  "explanation": {
    "summary": "...",
    "predicted_conditions_explained": [],
    "retrieved_medical_information": [],
    "safe_next_steps": [],
    "follow_up_questions": [],
    "emergency_guidance": [],
    "disclaimer": "...",
    "generator": "gemini|fallback|validation",
    "limitations": []
  },
  "disclaimer": "...",
  "record_id": 1
}
```

**Important safety/validation examples (required behavior):**
- `symptoms_text=""`, `duration_text="3 days"` → `status="invalid_input"`, message asks user to enter symptoms, no prediction
- `symptoms_text="3 days"`, `duration_text=""` → `status="invalid_input"` (duration-only), no invented symptoms, no prediction
- `symptoms_text="fever and cough"`, `duration_text="3 days"` → valid processing with mapped symptoms and separate duration

### `GET /api/v1/history?limit=20`
Returns recent saved analysis records (max 100).

### `GET /api/v1/history/{record_id}`
Returns full stored details for one analysis record.

### `DELETE /api/v1/history/{record_id}`
Deletes one analysis record.

### `GET /api/v1/rag/status`
Returns RAG/Chroma/docs status (collection, document counts, fallback mode, errors if any).

### `POST /api/v1/rag/reindex`
Ingests/reindexes bundled medical documents into ChromaDB.
- Note: in ephemeral hosts, the semantic index may be reconstructed on startup or retrieval may fall back to keyword search over bundled docs.

## Error/Response Notes
- The API returns **possible conditions only** (never confirmed diagnoses).
- Predictions come from the actual trained ML model and dataset-derived features; retrieved information comes from curated local medical documents; AI explanation is Gemini-generated when configured or a safe fallback otherwise.
- CORS is configurable via `CORS_ORIGINS` for local and deployed frontends.
- Gemini API keys and database credentials are backend-only environment variables and must never be sent to/exposed by the frontend.

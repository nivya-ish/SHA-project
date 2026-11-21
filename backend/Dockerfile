# Backend Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for scientific libs/psycopg2-binary runtime needs (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

# Copy project (includes data, ml artifacts, rag docs as needed)
COPY backend /app/backend
COPY data /app/data
COPY ml /app/ml
COPY rag /app/rag
COPY train_model.py /app/train_model.py
COPY .env.example /app/.env.example

ENV PYTHONPATH=/app/backend
WORKDIR /app

EXPOSE 8000

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]

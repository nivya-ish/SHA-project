from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.base import Base
from app.models import analysis  # noqa: F401  ensure models registered
from app.services.ml_service import ml_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort startup initialization for local/dev and hosted prototype deployments.
    # Failures are logged but should not prevent the API from starting so /health can report status.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning("Database table initialization failed at startup: %s", e)

    try:
        if not ml_service.ready:
            ml_service.load()
    except Exception as e:
        logger.warning("ML model load failed at startup: %s", e)

    try:
        # Reconstruct/ensure RAG index from bundled medical docs when possible.
        # Retrieval also falls back to keyword search over local docs, so this is best-effort.
        rag_service.ingest_documents(reindex=False)
    except Exception as e:
        logger.warning("RAG startup ingestion failed: %s", e)

    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    def root():
        return {
            "status": "ok",
            "app": settings.app_name,
            "message": "Smart Health Assistant backend is running.",
            "health": "/health",
            "api": settings.api_v1_prefix,
        }

    @app.get("/health")
    def health():
        return {"status": "ok", "app": settings.app_name}

    return app


app = create_app()

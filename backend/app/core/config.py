"""Core configuration."""
from __future__ import annotations

from pathlib import Path
from typing import List
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str | List[str]) -> List[str]:
    if isinstance(value, list):
        return value
    return [v.strip() for v in value.split(",") if v.strip()]


def _normalize_database_url(url: str) -> str:
    """Normalize common hosted Postgres URL forms for SQLAlchemy + psycopg2.

    - Render/Supabase often provide postgres:// or postgresql://
    - This project pins psycopg2-binary, so prefer postgresql+psycopg2:// when no driver is specified.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Smart Health Assistant", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    cors_origins: str | List[str] = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )
    port: int = Field(default=8000, alias="PORT")  # Hosting platforms (Render) inject PORT

    database_url: str = Field(default="sqlite:///./smarthealth.db", alias="DATABASE_URL")

    train_data_path: str = Field(default="data/raw/Training.csv", alias="TRAIN_DATA_PATH")
    test_data_path: str = Field(default="data/raw/Testing.csv", alias="TEST_DATA_PATH")
    model_artifact_dir: str = Field(default="ml/artifacts", alias="MODEL_ARTIFACT_DIR")
    model_metadata_path: str = Field(default="ml/artifacts/metadata.json", alias="MODEL_METADATA_PATH")

    chroma_persist_dir: str = Field(default="rag/chroma_db", alias="CHROMA_PERSIST_DIR")
    chroma_collection: str = Field(default="medical_knowledge", alias="CHROMA_COLLECTION")
    medical_docs_dir: str = Field(default="data/medical_docs", alias="MEDICAL_DOCS_DIR")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    rag_top_k: int = Field(default=4, alias="RAG_TOP_K")

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    gemini_timeout_seconds: int = Field(default=20, alias="GEMINI_TIMEOUT_SECONDS")
    gemini_enabled: bool = Field(default=True, alias="GEMINI_ENABLED")

    @property
    def normalized_database_url(self) -> str:
        return _normalize_database_url(self.database_url)

    @property
    def cors_origins_list(self) -> List[str]:
        origins = _split_csv(self.cors_origins)
        # Allow wildcard only when explicitly configured; avoid accidental wide-open defaults.
        if any(o == "*" for o in origins):
            return ["*"]
        return origins

    @property
    def cors_allow_credentials(self) -> bool:
        # Browsers reject credentials with wildcard origins; disable when "*" is used.
        return "*" not in self.cors_origins_list

    @property
    def project_root(self) -> Path:
        # backend/app/core/config.py -> project root
        return Path(__file__).resolve().parents[3]

    def resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        return p if p.is_absolute() else (self.project_root / p)


settings = Settings()

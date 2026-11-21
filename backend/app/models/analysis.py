from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False, index=True)
    symptoms_text: Mapped[str] = mapped_column(Text, nullable=False)
    duration_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_symptoms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    normalized_symptoms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    mapped_features: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    unsupported_symptoms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    predictions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retrieved_sources: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

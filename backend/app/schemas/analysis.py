"""Pydantic schemas for API requests/responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    symptoms_text: str = Field(default="", description="Natural language symptom description")
    duration_text: Optional[str] = Field(default=None, description="Separate duration field")


class PredictionItem(BaseModel):
    condition: str
    probability: float
    confidence_label: str
    supporting_symptoms: List[str] = []


class NLPResult(BaseModel):
    extracted_symptoms: List[str]
    normalized_symptoms: List[str]
    mapped_features: List[str]
    unsupported_symptoms: List[str]
    duration: Optional[str] = None
    notes: List[str] = []


class SourceItem(BaseModel):
    title: str
    source: str
    snippet: str
    score: Optional[float] = None


class ExplanationResult(BaseModel):
    summary: str
    predicted_conditions_explained: List[dict] = []
    retrieved_medical_information: List[dict] = []
    safe_next_steps: List[str] = []
    follow_up_questions: List[str] = []
    emergency_guidance: List[str] = []
    disclaimer: str
    generator: str = "fallback"
    limitations: List[str] = []


class AnalyzeResponse(BaseModel):
    status: str
    message: str
    nlp: NLPResult
    predictions: List[PredictionItem]
    retrieved_sources: List[SourceItem]
    explanation: ExplanationResult
    disclaimer: str
    record_id: Optional[int] = None


class HistoryItem(BaseModel):
    id: int
    created_at: datetime
    symptoms_text: str
    duration_text: Optional[str]
    normalized_symptoms: List[str]
    predictions: List[dict]
    status: str


class HealthResponse(BaseModel):
    status: str
    app: str
    ml_ready: bool
    rag_ready: bool
    gemini_configured: bool
    database_ok: bool

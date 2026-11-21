"""Analysis orchestration and persistence."""
from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.analysis import AnalysisRecord
from app.services.nlp_service import SymptomNLPProcessor
from app.services.ml_service import ml_service
from app.services.rag_service import rag_service
from app.services.gemini_service import gemini_service, DISCLAIMER


def run_analysis(db: Session, symptoms_text: str, duration_text: str | None, nlp_processor: SymptomNLPProcessor) -> Dict[str, Any]:
    nlp = nlp_processor.process(symptoms_text, duration_text)
    if not nlp.valid_for_prediction:
        return {
            "status": "invalid_input",
            "message": nlp.validation_message or "Invalid input.",
            "nlp": nlp,
            "predictions": [],
            "retrieved_sources": [],
            "explanation": {
                "summary": "Analysis was not run because valid symptoms were not provided.",
                "predicted_conditions_explained": [],
                "retrieved_medical_information": [],
                "safe_next_steps": ["Enter specific symptoms in plain language (e.g., fever, cough, headache) and try again."],
                "follow_up_questions": [],
                "emergency_guidance": [
                    "If you are experiencing severe or rapidly worsening symptoms, seek urgent medical care immediately."
                ],
                "disclaimer": DISCLAIMER,
                "generator": "validation",
                "limitations": nlp.notes,
            },
            "disclaimer": DISCLAIMER,
            "record_id": None,
        }

    # ML prediction (required for completed analysis)
    try:
        predictions = ml_service.predict(nlp.mapped_features, top_k=5)
    except Exception as e:
        return {
            "status": "error",
            "message": "Symptoms were processed, but the ML prediction service is currently unavailable. Please try again later or contact the administrator.",
            "nlp": nlp,
            "predictions": [],
            "retrieved_sources": [],
            "explanation": {
                "summary": "Prediction could not be completed because the ML model is unavailable.",
                "predicted_conditions_explained": [],
                "retrieved_medical_information": [],
                "safe_next_steps": ["Try again later. If symptoms are concerning or worsening, consult a qualified healthcare professional."],
                "follow_up_questions": [],
                "emergency_guidance": [
                    "Seek urgent medical care immediately for severe chest pain, trouble breathing, confusion, fainting, signs of stroke, severe bleeding, or rapidly worsening symptoms."
                ],
                "disclaimer": DISCLAIMER,
                "generator": "validation",
                "limitations": nlp.notes + [f"ML service error: {e}"],
            },
            "disclaimer": DISCLAIMER,
            "record_id": None,
        }

    try:
        supporting = ml_service.feature_importance_for_conditions([p["condition"] for p in predictions], nlp.mapped_features)
    except Exception:
        supporting = {}
    for p in predictions:
        p["supporting_symptoms"] = [s.replace("_", " ") for s in supporting.get(p["condition"], [])]

    # RAG retrieval (best-effort)
    try:
        query = " ".join(nlp.normalized_symptoms + ([nlp.duration] if nlp.duration else []))
        retrieved = rag_service.retrieve(query, top_k=4) or []
    except Exception:
        retrieved = []

    # Gemini / fallback explanation (service already falls back safely)
    try:
        explanation = gemini_service.generate(nlp.normalized_symptoms, nlp.duration, predictions, retrieved, notes=nlp.notes)
    except Exception:
        explanation = {
            "summary": "A safe fallback explanation is shown because AI explanation generation failed.",
            "predicted_conditions_explained": [],
            "retrieved_medical_information": [{"title": s.get("title"), "source": s.get("source"), "summary": s.get("snippet")} for s in (retrieved or [])[:4]],
            "safe_next_steps": ["Consult a qualified healthcare professional for personalized advice."],
            "follow_up_questions": [],
            "emergency_guidance": ["Seek urgent care immediately for severe or rapidly worsening symptoms."],
            "disclaimer": DISCLAIMER,
            "generator": "fallback",
            "limitations": nlp.notes + ["Explanation generation failed unexpectedly."],
        }

    record = AnalysisRecord(
        symptoms_text=symptoms_text or "",
        duration_text=nlp.duration,
        extracted_symptoms=nlp.extracted_symptoms,
        normalized_symptoms=nlp.normalized_symptoms,
        mapped_features=nlp.mapped_features,
        unsupported_symptoms=nlp.unsupported_symptoms,
        predictions=predictions,
        explanation=explanation,
        retrieved_sources=retrieved,
        status="completed",
        notes="; ".join(nlp.notes) if nlp.notes else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "status": "completed",
        "message": "Analysis completed. Results show possible conditions only, not a confirmed diagnosis.",
        "nlp": nlp,
        "predictions": predictions,
        "retrieved_sources": retrieved,
        "explanation": explanation,
        "disclaimer": DISCLAIMER,
        "record_id": record.id,
    }


def list_history(db: Session, limit: int = 20) -> List[AnalysisRecord]:
    stmt = select(AnalysisRecord).order_by(desc(AnalysisRecord.created_at)).limit(limit)
    return list(db.scalars(stmt).all())


def get_history_item(db: Session, record_id: int) -> AnalysisRecord | None:
    return db.get(AnalysisRecord, record_id)


def delete_history_item(db: Session, record_id: int) -> bool:
    rec = db.get(AnalysisRecord, record_id)
    if not rec:
        return False
    db.delete(rec)
    db.commit()
    return True

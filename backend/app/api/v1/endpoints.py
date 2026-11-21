from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, NLPResult, PredictionItem, SourceItem, ExplanationResult, HistoryItem, HealthResponse
from app.services.analysis_service import run_analysis, list_history, get_history_item, delete_history_item
from app.services.nlp_service import SymptomNLPProcessor
from app.services.ml_service import ml_service
from app.services.rag_service import rag_service
from app.services.gemini_service import gemini_service, DISCLAIMER
from app.core.config import settings

router = APIRouter()

_nlp_processor: SymptomNLPProcessor | None = None

def get_nlp_processor() -> SymptomNLPProcessor:
    global _nlp_processor
    if _nlp_processor is None:
        # Ensure model/feature columns available; fallback to dataset-derived features if needed
        if not ml_service.ready:
            ml_service.load()
        if ml_service.ready and ml_service.bundle:
            features = ml_service.bundle.feature_columns
        else:
            # fallback: derive from training csv at runtime
            try:
                from app.ml.data_utils import load_dataset_csv
                bundle = load_dataset_csv(settings.resolve_path(settings.train_data_path))
                features = bundle.feature_columns
            except Exception:
                features = []
        _nlp_processor = SymptomNLPProcessor(features)
    return _nlp_processor


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    if not ml_service.ready:
        ml_service.load()
    rag_status = rag_service.status()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        ml_ready=ml_service.ready,
        rag_ready=bool(rag_status.get("ready")),
        gemini_configured=gemini_service.configured,
        database_ok=db_ok,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    processor = get_nlp_processor()
    result = run_analysis(db, req.symptoms_text, req.duration_text, processor)
    nlp_obj = result["nlp"]
    return AnalyzeResponse(
        status=result["status"],
        message=result["message"],
        nlp=NLPResult(
            extracted_symptoms=nlp_obj.extracted_symptoms,
            normalized_symptoms=nlp_obj.normalized_symptoms,
            mapped_features=nlp_obj.mapped_features,
            unsupported_symptoms=nlp_obj.unsupported_symptoms,
            duration=nlp_obj.duration,
            notes=nlp_obj.notes,
        ),
        predictions=[PredictionItem(**p) for p in result.get("predictions", [])],
        retrieved_sources=[SourceItem(**s) for s in result.get("retrieved_sources", [])],
        explanation=ExplanationResult(**result.get("explanation", {})),
        disclaimer=result.get("disclaimer", DISCLAIMER),
        record_id=result.get("record_id"),
    )


@router.get("/history", response_model=list[HistoryItem])
def history(limit: int = 20, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 100))
    items = list_history(db, limit=limit)
    return [
        HistoryItem(
            id=i.id,
            created_at=i.created_at,
            symptoms_text=i.symptoms_text,
            duration_text=i.duration_text,
            normalized_symptoms=i.normalized_symptoms or [],
            predictions=i.predictions or [],
            status=i.status,
        ) for i in items
    ]


@router.get("/history/{record_id}", response_model=dict)
def history_detail(record_id: int, db: Session = Depends(get_db)):
    item = get_history_item(db, record_id)
    if not item:
        raise HTTPException(status_code=404, detail="History record not found")
    return {
        "id": item.id,
        "created_at": item.created_at,
        "symptoms_text": item.symptoms_text,
        "duration_text": item.duration_text,
        "extracted_symptoms": item.extracted_symptoms,
        "normalized_symptoms": item.normalized_symptoms,
        "mapped_features": item.mapped_features,
        "unsupported_symptoms": item.unsupported_symptoms,
        "predictions": item.predictions,
        "explanation": item.explanation,
        "retrieved_sources": item.retrieved_sources,
        "status": item.status,
        "notes": item.notes,
    }


@router.delete("/history/{record_id}")
def history_delete(record_id: int, db: Session = Depends(get_db)):
    ok = delete_history_item(db, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="History record not found")
    return {"status": "deleted", "id": record_id}


@router.get("/rag/status")
def rag_status():
    return rag_service.status()


@router.post("/rag/reindex")
def rag_reindex():
    return rag_service.ingest_documents(reindex=True)

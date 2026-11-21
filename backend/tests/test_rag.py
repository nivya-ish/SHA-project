from pathlib import Path
from app.services.rag_service import rag_service, chunk_text
from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_chunk_text_basic():
    chunks = chunk_text("This is a test. " * 200, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(chunks)


def test_rag_status_and_retrieve_keyword_fallback():
    # ensure docs dir points to project docs if settings resolved oddly
    rag_service.docs_dir = settings.resolve_path(settings.medical_docs_dir)
    status = rag_service.status()
    assert isinstance(status, dict)
    # should be able to retrieve from local medical docs via keyword/semantic fallback
    results = rag_service.retrieve("fever cough breathing emergency", top_k=3)
    assert isinstance(results, list)
    assert len(results) >= 1
    assert "title" in results[0]
    assert "source" in results[0]
    assert "snippet" in results[0]

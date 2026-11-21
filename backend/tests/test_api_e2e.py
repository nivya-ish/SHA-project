import os
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Configure env for tests before app import
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("GEMINI_ENABLED", "false")
os.environ.setdefault("MODEL_ARTIFACT_DIR", str(PROJECT_ROOT / "ml" / "artifacts"))
os.environ.setdefault("TRAIN_DATA_PATH", str(PROJECT_ROOT / "data" / "raw" / "Training.csv"))
os.environ.setdefault("TEST_DATA_PATH", str(PROJECT_ROOT / "data" / "raw" / "Testing.csv"))
os.environ.setdefault("MEDICAL_DOCS_DIR", str(PROJECT_ROOT / "data" / "medical_docs"))
os.environ.setdefault("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "rag" / "chroma_db"))

from app.main import app  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.db.base import Base  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_endpoint():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "ml_ready" in data


def test_analyze_rejects_duration_only_without_prediction():
    r = client.post("/api/v1/analyze", json={"symptoms_text": "3 days", "duration_text": ""})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "invalid_input"
    assert data["predictions"] == []
    assert data["nlp"]["mapped_features"] == []
    assert data["nlp"]["normalized_symptoms"] == []
    assert data["record_id"] is None


def test_analyze_rejects_empty_symptoms_with_duration():
    r = client.post("/api/v1/analyze", json={"symptoms_text": "", "duration_text": "3 days"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "invalid_input"
    assert data["predictions"] == []
    assert "Please enter your symptoms" in data["message"]


def test_analyze_valid_symptoms_returns_predictions_and_explanation():
    r = client.post("/api/v1/analyze", json={"symptoms_text": "fever and cough", "duration_text": "3 days"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["nlp"]["duration"] == "3 days"
    assert len(data["nlp"]["mapped_features"]) >= 1
    assert len(data["predictions"]) >= 1
    assert "disclaimer" in data
    assert "explanation" in data
    assert data["explanation"]["disclaimer"]
    assert isinstance(data["retrieved_sources"], list)
    assert data["record_id"] is not None


def test_history_endpoints():
    # create
    r = client.post("/api/v1/analyze", json={"symptoms_text": "itching and skin rash", "duration_text": "2 days"})
    assert r.status_code == 200
    rec_id = r.json()["record_id"]
    assert rec_id is not None

    r = client.get("/api/v1/history?limit=10")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(i["id"] == rec_id for i in items)

    r = client.get(f"/api/v1/history/{rec_id}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["id"] == rec_id

    r = client.delete(f"/api/v1/history/{rec_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

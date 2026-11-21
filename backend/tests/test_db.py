from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.analysis import AnalysisRecord


def test_database_crud_sqlite_tmp(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSession()
    try:
        rec = AnalysisRecord(
            symptoms_text="fever and cough",
            duration_text="3 days",
            extracted_symptoms=["fever", "cough"],
            normalized_symptoms=["high fever", "cough"],
            mapped_features=["high_fever", "cough"],
            unsupported_symptoms=[],
            predictions=[{"condition": "Common Cold", "probability": 0.5}],
            explanation={"summary": "test"},
            retrieved_sources=[],
            status="completed",
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        assert rec.id is not None

        # read
        got = db.get(AnalysisRecord, rec.id)
        assert got is not None
        assert got.symptoms_text == "fever and cough"

        # update
        got.status = "reviewed"
        db.commit()
        got2 = db.get(AnalysisRecord, rec.id)
        assert got2.status == "reviewed"

        # delete
        db.delete(got2)
        db.commit()
        assert db.get(AnalysisRecord, rec.id) is None
    finally:
        db.close()

from app.db.base import Base
# Import models so SQLAlchemy registers tables for metadata/create_all
from app.models.analysis import AnalysisRecord  # noqa: F401

__all__ = ["Base", "AnalysisRecord"]

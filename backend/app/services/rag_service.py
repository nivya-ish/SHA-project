"""RAG service using ChromaDB and medical documents.

Document ingestion is explicit via ingest_documents()/reindex; query degrades
gracefully to keyword retrieval over local medical docs if embeddings/vector
search are unavailable.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import hashlib
import json
import re

from app.core.config import settings


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


class RAGService:
    def __init__(self):
        self.persist_dir = settings.resolve_path(settings.chroma_persist_dir)
        self.docs_dir = settings.resolve_path(settings.medical_docs_dir)
        self.collection_name = settings.chroma_collection
        self.embedding_model_name = settings.embedding_model
        self._client = None
        self._collection = None
        self._embedding_model = None
        self.init_error: str | None = None

    @property
    def ready(self) -> bool:
        return self._ensure_client() is not None

    def _load_embedding_model(self):
        if self._embedding_model is not None:
            return self._embedding_model
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
            return self._embedding_model
        except Exception as e:
            self.init_error = f"Embedding model unavailable: {e}"
            return None

    def _ensure_client(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb  # type: ignore
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            self._collection = self._client.get_or_create_collection(name=self.collection_name)
            return self._collection
        except Exception as e:
            self.init_error = f"ChromaDB unavailable: {e}"
            self._collection = None
            return None

    def status(self) -> Dict[str, Any]:
        col = self._ensure_client()
        count = None
        if col is not None:
            try:
                count = col.count()
            except Exception:
                count = None
        # Keyword fallback can retrieve directly from bundled medical docs even if Chroma/embeddings are unavailable.
        docs_available = False
        try:
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            docs_available = any(p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"} for p in self.docs_dir.rglob("*"))
        except Exception:
            docs_available = False
        return {
            "ready": bool(col is not None or docs_available),
            "collection": self.collection_name,
            "persist_dir": str(self.persist_dir),
            "documents_dir": str(self.docs_dir),
            "document_count": count,
            "documents_available": docs_available,
            "error": self.init_error,
            "embedding_model": self.embedding_model_name,
            "fallback_mode": "keyword-over-medical-docs" if docs_available else "none",
        }

    def _read_document(self, path: Path) -> str:
        suffix = path.suffix.lower()
        try:
            if suffix in {".txt", ".md"}:
                return path.read_text(encoding="utf-8", errors="ignore")
            if suffix == ".json":
                data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                if isinstance(data, dict):
                    return "\n".join(f"{k}: {v}" for k, v in data.items())
                if isinstance(data, list):
                    return "\n".join(json.dumps(x, ensure_ascii=False) for x in data)
                return str(data)
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _iter_doc_chunks(self):
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        files = [p for p in sorted(self.docs_dir.rglob("*")) if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"}]
        for path in files:
            text = self._read_document(path)
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                yield path, i, chunk, files
        # if called as generator consumer expecting files count separately, handled below

    def ingest_documents(self, reindex: bool = False) -> Dict[str, Any]:
        col = self._ensure_client()
        if col is None:
            # Chroma may be unavailable in ephemeral hosts, but bundled docs still support keyword fallback retrieval.
            self.docs_dir.mkdir(parents=True, exist_ok=True)
            files = [p for p in sorted(self.docs_dir.rglob("*")) if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"}]
            return {
                "ok": bool(files),
                "error": self.init_error,
                "ingested_chunks": 0,
                "documents": len(files),
                "embeddings": False,
                "fallback_mode": "keyword-over-medical-docs" if files else "none",
                "message": "ChromaDB unavailable; keyword retrieval over bundled medical documents is still available." if files else "No medical documents found and ChromaDB unavailable.",
            }
        if reindex:
            try:
                if self._client is not None:
                    self._client.delete_collection(self.collection_name)
            except Exception:
                pass
            try:
                self._collection = self._client.get_or_create_collection(name=self.collection_name) if self._client else None
                col = self._collection
            except Exception as e:
                return {"ok": False, "error": str(e), "ingested_chunks": 0, "documents": 0}

        self.docs_dir.mkdir(parents=True, exist_ok=True)
        files = [p for p in sorted(self.docs_dir.rglob("*")) if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"}]
        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        for path in files:
            text = self._read_document(path)
            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                base = f"{path.relative_to(self.docs_dir)}::{i}"
                cid = hashlib.sha1(base.encode("utf-8")).hexdigest()
                ids.append(cid)
                docs.append(chunk)
                try:
                    rel_source = str(path.relative_to(settings.project_root))
                except Exception:
                    rel_source = str(path)
                metas.append({
                    "title": path.stem.replace("_", " ").title(),
                    "source": rel_source,
                    "file_name": path.name,
                    "chunk_index": i,
                })
        if not docs:
            return {"ok": True, "ingested_chunks": 0, "documents": len(files), "message": "No medical documents found to ingest."}

        emb_model = self._load_embedding_model()
        if emb_model is None:
            # Store docs without embeddings for keyword fallback if possible
            try:
                if hasattr(col, "upsert"):
                    col.upsert(ids=ids, documents=docs, metadatas=metas)
                else:
                    col.add(ids=ids, documents=docs, metadatas=metas)
                return {"ok": True, "ingested_chunks": len(docs), "documents": len(files), "embeddings": False, "warning": self.init_error}
            except Exception as e:
                return {"ok": False, "error": f"{self.init_error}; store failed: {e}", "ingested_chunks": 0, "documents": len(files)}

        try:
            embeddings = emb_model.encode(docs, show_progress_bar=False, normalize_embeddings=True).tolist()
            if hasattr(col, "upsert"):
                col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
            else:
                col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
            return {"ok": True, "ingested_chunks": len(docs), "documents": len(files), "embeddings": True}
        except Exception as e:
            # fallback store without embeddings
            try:
                if hasattr(col, "upsert"):
                    col.upsert(ids=ids, documents=docs, metadatas=metas)
                else:
                    col.add(ids=ids, documents=docs, metadatas=metas)
                return {"ok": True, "ingested_chunks": len(docs), "documents": len(files), "embeddings": False, "warning": str(e)}
            except Exception:
                return {"ok": False, "error": str(e), "ingested_chunks": 0, "documents": len(files)}

    def _keyword_retrieve_from_files(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        q_tokens = [t for t in re.findall(r"[a-z0-9_]+", query.lower()) if len(t) > 2]
        if not q_tokens:
            q_tokens = [t for t in re.findall(r"[a-z0-9_]+", query.lower()) if t]
        scored = []
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        files = [p for p in sorted(self.docs_dir.rglob("*")) if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json"}]
        for path in files:
            text = self._read_document(path)
            for i, chunk in enumerate(chunk_text(text)):
                low = chunk.lower()
                score = 0.0
                for tok in q_tokens:
                    score += low.count(tok)
                if score > 0:
                    try:
                        rel_source = str(path.relative_to(settings.project_root))
                    except Exception:
                        rel_source = str(path)
                    scored.append({
                        "title": path.stem.replace("_", " ").title(),
                        "source": rel_source,
                        "snippet": chunk[:600],
                        "score": float(score),
                        "_i": i,
                    })
        scored.sort(key=lambda x: x["score"], reverse=True)
        # normalize simple score
        out = []
        max_s = scored[0]["score"] if scored else 1.0
        for item in scored[:top_k]:
            item["score"] = round(float(item["score"] / max_s), 6) if max_s else None
            item.pop("_i", None)
            out.append(item)
        return out

    def _keyword_retrieve_from_collection(self, col, query: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            data = col.get(include=["documents", "metadatas"])
            docs = data.get("documents") or []
            metas = data.get("metadatas") or []
            q_tokens = [t for t in re.findall(r"[a-z0-9_]+", query.lower()) if len(t) > 2] or re.findall(r"[a-z0-9_]+", query.lower())
            scored = []
            for doc, meta in zip(docs, metas):
                low = (doc or "").lower()
                score = 0.0
                for tok in q_tokens:
                    score += low.count(tok)
                if score > 0:
                    meta = meta or {}
                    scored.append({
                        "title": meta.get("title") or meta.get("file_name") or "Medical document",
                        "source": meta.get("source") or meta.get("file_name") or "local medical knowledge base",
                        "snippet": (doc or "")[:600],
                        "score": float(score),
                    })
            scored.sort(key=lambda x: x["score"], reverse=True)
            if not scored:
                return []
            max_s = scored[0]["score"]
            for item in scored[:top_k]:
                item["score"] = round(float(item["score"] / max_s), 6) if max_s else None
            return scored[:top_k]
        except Exception:
            return []

    def retrieve(self, query: str, top_k: int | None = None) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []
        top_k = top_k or settings.rag_top_k
        col = self._ensure_client()

        emb_model = self._load_embedding_model()
        if col is not None and emb_model is not None:
            try:
                count = col.count() if hasattr(col, "count") else 0
                if count == 0:
                    # try on-the-fly keyword fallback from files if nothing indexed yet
                    return self._keyword_retrieve_from_files(query, top_k)
                q_emb = emb_model.encode([query], show_progress_bar=False, normalize_embeddings=True).tolist()
                res = col.query(query_embeddings=q_emb, n_results=top_k, include=["documents", "metadatas", "distances"])
                docs = (res.get("documents") or [[]])[0]
                metas = (res.get("metadatas") or [[]])[0]
                dists = (res.get("distances") or [[]])[0]
                out = []
                for doc, meta, dist in zip(docs, metas, dists):
                    meta = meta or {}
                    score = None
                    try:
                        score = float(1.0 / (1.0 + float(dist))) if dist is not None else None
                    except Exception:
                        score = None
                    out.append({
                        "title": meta.get("title") or meta.get("file_name") or "Medical document",
                        "source": meta.get("source") or meta.get("file_name") or "local medical knowledge base",
                        "snippet": (doc or "")[:600],
                        "score": score,
                    })
                if out:
                    return out
            except Exception:
                pass

        # keyword fallback: prefer collection docs, then files
        if col is not None:
            items = self._keyword_retrieve_from_collection(col, query, top_k)
            if items:
                return items
        return self._keyword_retrieve_from_files(query, top_k)


rag_service = RAGService()

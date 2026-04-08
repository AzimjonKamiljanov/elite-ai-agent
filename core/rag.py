"""
RAG (Retrieval Augmented Generation) tizimi.
Lokal hujjatlarni indekslash va ulardan ma'lumot qidirish.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional


_SUPPORTED_EXTENSIONS = {".txt", ".py", ".md", ".json", ".csv", ".pdf"}
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Matnni bo'laklarga ajratish."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


class RAGEngine:
    """RAG tizimi — hujjatlarni indekslash va qidirish."""

    def __init__(
        self,
        collection_name: str = "jarvis_docs",
        persist_dir: str = "./data/memory",
    ) -> None:
        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._collection: Any = None
        self._use_chroma = False
        self._fallback_store: list[dict] = []
        self._init_storage()

    def _init_storage(self) -> None:
        """ChromaDB ni ishga tushirish."""
        try:
            import chromadb  # type: ignore

            client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except ImportError:
            self._use_chroma = False
        except Exception:
            self._use_chroma = False

    def ingest_file(self, path: str, allowed_base: str | None = None) -> int:
        """Faylni indekslash.

        Args:
            path: Path to the file to ingest.
            allowed_base: If provided, the file must be within this directory (path traversal protection).

        Returns:
            Qo'shilgan bo'laklar soni
        """
        # Resolve to absolute path to prevent traversal
        try:
            file_path = Path(path).resolve(strict=False)
        except (ValueError, OSError) as exc:
            raise ValueError("Invalid file path.") from exc

        # Restrict to allowed base directory when provided (e.g., from API callers)
        if allowed_base is not None:
            base = Path(allowed_base).resolve(strict=False)
            if not str(file_path).startswith(str(base) + os.sep) and file_path != base:
                raise ValueError("Access to this path is not allowed.")

        if not file_path.exists():
            raise FileNotFoundError(f"Fayl topilmadi: {file_path.name}")

        suffix = file_path.suffix.lower()
        if suffix not in _SUPPORTED_EXTENSIONS:
            raise ValueError(f"Qo'llab-quvvatlanmaydigan fayl turi: {suffix}")

        # PDF ni o'qish
        if suffix == ".pdf":
            return self._ingest_pdf(file_path)

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            raise OSError("Fayl o'qishda xato") from exc

        chunks = _chunk_text(text)
        self._store_chunks(chunks, source=str(file_path))
        return len(chunks)

    def _ingest_pdf(self, path: Path) -> int:
        """PDF faylni o'qish (PyMuPDF bo'lsa)."""
        try:
            import fitz  # type: ignore — PyMuPDF

            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            chunks = _chunk_text(text)
            self._store_chunks(chunks, source=str(path))
            return len(chunks)
        except ImportError:
            raise ImportError("PDF o'qish uchun PyMuPDF o'rnating: pip install pymupdf")

    def ingest_directory(self, path: str) -> int:
        """Katalogdagi barcha hujjatlarni indekslash.

        Returns:
            Jami qo'shilgan bo'laklar soni
        """
        dir_path = Path(path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Katalog topilmadi: {path}")

        total = 0
        for file_path in dir_path.rglob("*"):
            if file_path.suffix.lower() in _SUPPORTED_EXTENSIONS:
                try:
                    total += self.ingest_file(str(file_path))
                except Exception:
                    continue
        return total

    def _store_chunks(self, chunks: list[str], source: str) -> None:
        """Bo'laklarni saqlash."""
        if not chunks:
            return

        if self._use_chroma and self._collection is not None:
            try:
                import uuid

                ids = [str(uuid.uuid4()) for _ in chunks]
                metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]
                self._collection.add(documents=chunks, metadatas=metadatas, ids=ids)
                return
            except Exception:
                pass

        # Fallback
        for i, chunk in enumerate(chunks):
            self._fallback_store.append(
                {"content": chunk, "metadata": {"source": source, "chunk_index": i}}
            )

    def query(self, question: str, k: int = 5) -> list[dict]:
        """Savolga mos bo'laklarni qidirish.

        Returns:
            [{"content": str, "source": str, "score": float}]
        """
        if not question.strip():
            return []

        if self._use_chroma and self._collection is not None:
            try:
                count = self._collection.count()
                if count == 0:
                    return []
                results = self._collection.query(
                    query_texts=[question],
                    n_results=min(k, count),
                )
                if not results or not results.get("documents"):
                    return []
                docs = results["documents"][0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                return [
                    {
                        "content": d,
                        "source": m.get("source", ""),
                        "score": 1 - dist,
                    }
                    for d, m, dist in zip(docs, metas, distances)
                ]
            except Exception:
                pass

        # Fallback: keyword search
        q_lower = question.lower()
        results = []
        for item in self._fallback_store:
            if q_lower in item["content"].lower():
                results.append(
                    {
                        "content": item["content"],
                        "source": item["metadata"].get("source", ""),
                        "score": 0.5,
                    }
                )
        return results[:k]

    def get_stats(self) -> dict:
        """RAG statistikasi."""
        if self._use_chroma and self._collection is not None:
            try:
                count = self._collection.count()
                return {"chunks": count, "backend": "chromadb"}
            except Exception:
                pass
        return {"chunks": len(self._fallback_store), "backend": "in-memory"}

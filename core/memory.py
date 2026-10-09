"""
Xotira tizimi — qisqa muddatli va uzoq muddatli xotira.
ChromaDB bo'lmasa, in-memory fallback ishlatiladi.
"""

from __future__ import annotations

from typing import Any


class MemoryManager:
    """Qisqa va uzoq muddatli xotira boshqaruvchisi."""

    def __init__(
        self,
        short_term_limit: int = 50,
        collection_name: str = "jarvis_memory",
        persist_dir: str = "./data/memory",
    ) -> None:
        self._short_term: list[dict] = []
        self._short_term_limit = short_term_limit
        self._collection_name = collection_name
        self._persist_dir = persist_dir
        self._chroma_client: Any = None
        self._collection: Any = None
        self._in_memory_store: list[dict] = []
        self._use_chroma = False
        self._init_long_term()

    def _init_long_term(self) -> None:
        """ChromaDB ni ishga tushirish (bo'lmasa in-memory ishlatiladi)."""
        try:
            import chromadb  # type: ignore

            self._chroma_client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = self._chroma_client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except ImportError:
            self._use_chroma = False
        except Exception:
            self._use_chroma = False

    # === Qisqa muddatli xotira ===

    def add_to_short_term(self, role: str, content: str) -> None:
        """Suhbat tarixiga xabar qo'shish."""
        self._short_term.append({"role": role, "content": content})
        if len(self._short_term) > self._short_term_limit:
            # Eng eskisini o'chirish (system xabardan keyin)
            self._short_term = self._short_term[-self._short_term_limit :]

    def get_conversation_history(self) -> list[dict]:
        """Suhbat tarixini qaytarish."""
        return list(self._short_term)

    def clear_short_term(self) -> None:
        """Qisqa muddatli xotirani tozalash."""
        self._short_term = []

    # === Uzoq muddatli xotira ===

    def add_to_long_term(self, content: str, metadata: dict | None = None) -> None:
        """Uzoq muddatli xotiraga ma'lumot qo'shish."""
        if not content.strip():
            return

        meta = metadata or {}

        if self._use_chroma and self._collection is not None:
            try:
                import uuid

                doc_id = str(uuid.uuid4())
                self._collection.add(
                    documents=[content],
                    metadatas=[meta],
                    ids=[doc_id],
                )
                return
            except Exception:
                pass

        # Fallback: in-memory
        self._in_memory_store.append({"content": content, "metadata": meta})
        if len(self._in_memory_store) > 1000:
            self._in_memory_store = self._in_memory_store[-1000:]

    def search_long_term(self, query: str, k: int = 5) -> list[dict]:
        """Uzoq muddatli xotiradan qidiruv.

        Returns:
            [{"content": str, "metadata": dict, "distance": float}]
        """
        if not query.strip():
            return []

        if self._use_chroma and self._collection is not None:
            try:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(k, self._collection.count()),
                )
                if not results or not results.get("documents"):
                    return []
                docs = results["documents"][0]
                metas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                return [
                    {"content": d, "metadata": m, "distance": dist}
                    for d, m, dist in zip(docs, metas, distances)
                ]
            except Exception:
                pass

        # Fallback: simple keyword search
        query_lower = query.lower()
        results = []
        for item in self._in_memory_store:
            if query_lower in item["content"].lower():
                results.append(
                    {"content": item["content"], "metadata": item["metadata"], "distance": 0.5}
                )
        return results[:k]

    def get_stats(self) -> dict:
        """Xotira statistikasi."""
        long_term_count = 0
        if self._use_chroma and self._collection is not None:
            try:
                long_term_count = self._collection.count()
            except Exception:
                long_term_count = len(self._in_memory_store)
        else:
            long_term_count = len(self._in_memory_store)

        return {
            "short_term_messages": len(self._short_term),
            "short_term_limit": self._short_term_limit,
            "long_term_entries": long_term_count,
            "storage_backend": "chromadb" if self._use_chroma else "in-memory",
        }

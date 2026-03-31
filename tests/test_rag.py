"""Tests for the RAG engine."""

from __future__ import annotations

import os
import tempfile

import pytest

from core.rag import RAGEngine


@pytest.fixture
def rag(tmp_path) -> RAGEngine:
    return RAGEngine(
        collection_name="test_rag",
        persist_dir=str(tmp_path / "rag_test"),
    )


def test_rag_init(rag: RAGEngine) -> None:
    stats = rag.get_stats()
    assert "chunks" in stats
    assert stats["chunks"] == 0


def test_rag_ingest_text_file(rag: RAGEngine, tmp_path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("JARVIS is an AI assistant. It is intelligent and helpful.", encoding="utf-8")
    chunks = rag.ingest_file(str(test_file))
    assert chunks >= 1


def test_rag_ingest_markdown(rag: RAGEngine, tmp_path) -> None:
    md_file = tmp_path / "test.md"
    md_file.write_text("# JARVIS\nThis is a test document.", encoding="utf-8")
    chunks = rag.ingest_file(str(md_file))
    assert chunks >= 1


def test_rag_ingest_python_file(rag: RAGEngine, tmp_path) -> None:
    py_file = tmp_path / "test.py"
    py_file.write_text("def hello():\n    return 'Hello, World!'\n", encoding="utf-8")
    chunks = rag.ingest_file(str(py_file))
    assert chunks >= 1


def test_rag_ingest_nonexistent_file(rag: RAGEngine) -> None:
    with pytest.raises(FileNotFoundError):
        rag.ingest_file("/nonexistent/path/file.txt")


def test_rag_ingest_unsupported_extension(rag: RAGEngine, tmp_path) -> None:
    bad_file = tmp_path / "test.xyz"
    bad_file.write_text("content")
    with pytest.raises(ValueError):
        rag.ingest_file(str(bad_file))


def test_rag_query_empty(rag: RAGEngine) -> None:
    results = rag.query("who is JARVIS")
    assert isinstance(results, list)


def test_rag_query_after_ingest(rag: RAGEngine, tmp_path) -> None:
    test_file = tmp_path / "doc.txt"
    test_file.write_text(
        "JARVIS is a highly intelligent AI assistant created to help Tony Stark. "
        "JARVIS can analyze data, control systems, and answer questions.",
        encoding="utf-8",
    )
    rag.ingest_file(str(test_file))
    results = rag.query("What is JARVIS?", k=3)
    assert isinstance(results, list)
    if results:
        assert "content" in results[0]
        assert "source" in results[0]


def test_rag_ingest_directory(rag: RAGEngine, tmp_path) -> None:
    (tmp_path / "a.txt").write_text("Document A content.", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Document B content.", encoding="utf-8")
    (tmp_path / "c.md").write_text("# Document C\nMarkdown content.", encoding="utf-8")
    total = rag.ingest_directory(str(tmp_path))
    assert total >= 3


def test_rag_query_empty_string(rag: RAGEngine) -> None:
    results = rag.query("")
    assert results == []

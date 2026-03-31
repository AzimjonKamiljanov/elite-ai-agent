"""Tests for FastAPI endpoints — /api/chat, /api/health, /api/system/stats, /api/voice/status."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_orchestrator():
    """Return a mock orchestrator that doesn't need real API keys."""
    orc = MagicMock()
    orc.initialize = AsyncMock()
    orc.process_message = AsyncMock(return_value={
        "response": "Online. How may I assist you, Mr. Stark?",
        "model_used": "llama-3.1-8b-instant",
        "response_time": 0.123,
        "mode": "pro",
    })
    orc.get_available_providers = MagicMock(return_value=["groq"])
    orc.get_memory_count = MagicMock(return_value=0)
    orc.get_mode = MagicMock(return_value="pro")
    orc.set_mode = MagicMock(return_value=True)
    # Async generator for streaming
    async def _stream_gen(*args, **kwargs):
        yield "Hello"
        yield " Mr."
        yield " Stark."
    orc.process_stream = MagicMock(side_effect=lambda *a, **kw: _stream_gen())
    return orc


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.query = MagicMock(return_value=[
        {"content": "JARVIS is an AI.", "source": "doc.txt", "score": 0.9}
    ])
    rag.ingest_file = MagicMock(return_value=5)
    return rag


@pytest.fixture
def client(mock_orchestrator, mock_rag):
    """TestClient with mocked orchestrator and RAG."""
    import apps.api.main as api_module

    with TestClient(api_module.app) as c:
        # Override after lifespan startup so we control the backends
        api_module._orchestrator = mock_orchestrator
        api_module._rag = mock_rag
        yield c


# ── /api/health ────────────────────────────────────────────────────────────────

def test_health_returns_operational(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "operational"
    assert "providers" in data
    assert "memory_entries" in data
    assert "current_mode" in data


# ── /api/system/stats ─────────────────────────────────────────────────────────

def test_system_stats_returns_dict(client: TestClient) -> None:
    resp = client.get("/api/system/stats")
    assert resp.status_code == 200
    data = resp.json()
    # psutil may or may not be available
    assert isinstance(data, dict)


# ── /api/chat ─────────────────────────────────────────────────────────────────

def test_chat_basic(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "Hello JARVIS"})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "session_id" in data
    assert "model_used" in data
    assert "response_time" in data
    assert "mode" in data


def test_chat_with_mode(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "Hello", "mode": "fast"})
    assert resp.status_code == 200


def test_chat_with_session_id(client: TestClient) -> None:
    resp = client.post(
        "/api/chat",
        json={"message": "Hello", "session_id": "test-session-123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "test-session-123"


def test_chat_force_offline(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "Hello", "force_offline": True})
    assert resp.status_code == 200


def test_chat_streaming(client: TestClient) -> None:
    resp = client.get("/api/chat/stream?message=Hello")
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


# ── /api/voice/status ─────────────────────────────────────────────────────────

def test_voice_status(client: TestClient) -> None:
    resp = client.get("/api/voice/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "stt" in data
    assert "tts" in data
    assert "microphone" in data
    assert isinstance(data["stt"], bool)
    assert isinstance(data["tts"], bool)
    assert isinstance(data["microphone"], bool)


# ── /api/rag/query ────────────────────────────────────────────────────────────

def test_rag_query(client: TestClient) -> None:
    resp = client.post("/api/rag/query", json={"question": "Who is JARVIS?", "k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "count" in data


def test_rag_ingest(client: TestClient) -> None:
    resp = client.post("/api/rag/ingest", json={"path": "/some/file.txt"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


# ── /api/life/* ───────────────────────────────────────────────────────────────

def test_life_schedule(client: TestClient) -> None:
    resp = client.get("/api/life/schedule")
    assert resp.status_code == 200
    data = resp.json()
    assert "schedule" in data


def test_life_homework_list(client: TestClient) -> None:
    resp = client.get("/api/life/homework")
    assert resp.status_code == 200
    data = resp.json()
    assert "homework" in data

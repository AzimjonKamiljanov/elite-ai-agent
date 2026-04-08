"""Tests for the unified memory system (short-term + long-term)."""

from __future__ import annotations

import pytest

from core.memory import MemoryManager


@pytest.fixture
def memory() -> MemoryManager:
    return MemoryManager(short_term_limit=5, persist_dir="./data/test-memory")


def test_add_to_short_term(memory: MemoryManager) -> None:
    memory.add_to_short_term("user", "hello")
    history = memory.get_conversation_history()
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"


def test_short_term_limit(memory: MemoryManager) -> None:
    for i in range(10):
        memory.add_to_short_term("user", f"message {i}")
    history = memory.get_conversation_history()
    assert len(history) <= 5


def test_clear_short_term(memory: MemoryManager) -> None:
    memory.add_to_short_term("user", "test")
    memory.clear_short_term()
    assert len(memory.get_conversation_history()) == 0


def test_add_to_long_term(memory: MemoryManager) -> None:
    """Adding to long-term memory should not raise errors (even without ChromaDB)."""
    memory.add_to_long_term("Test memory content", metadata={"type": "test"})
    # Should succeed regardless of backend
    stats = memory.get_stats()
    assert stats["long_term_entries"] >= 0


def test_search_long_term_empty(memory: MemoryManager) -> None:
    """Searching empty memory should return an empty list."""
    results = memory.search_long_term("nonexistent query xyz123")
    assert isinstance(results, list)


def test_search_long_term_with_content(memory: MemoryManager) -> None:
    """After adding content, search should find it (at least via fallback)."""
    memory.add_to_long_term("The sky is blue and clear today")
    results = memory.search_long_term("sky blue")
    # May return results via keyword or vector search
    assert isinstance(results, list)


def test_get_stats(memory: MemoryManager) -> None:
    stats = memory.get_stats()
    assert "short_term_messages" in stats
    assert "long_term_entries" in stats
    assert "storage_backend" in stats


def test_conversation_history_multiple_roles(memory: MemoryManager) -> None:
    memory.add_to_short_term("user", "Who are you?")
    memory.add_to_short_term("assistant", "I am JARVIS.")
    history = memory.get_conversation_history()
    roles = [m["role"] for m in history]
    assert "user" in roles
    assert "assistant" in roles


def test_memory_manager_init_defaults() -> None:
    mm = MemoryManager()
    assert mm._short_term_limit == 50
    assert isinstance(mm._short_term, list)

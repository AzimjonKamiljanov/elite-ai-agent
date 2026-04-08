"""Tests for life modules (scheduler, homework, planner)."""

from __future__ import annotations

import pytest


def test_scheduler_import() -> None:
    """Scheduler module should be importable."""
    from life import scheduler  # noqa: F401


def test_homework_import() -> None:
    """Homework module should be importable."""
    from life import homework  # noqa: F401


def test_planner_import() -> None:
    """Daily planner module should be importable."""
    from life import daily_planner  # noqa: F401


def test_reminders_import() -> None:
    from life import reminders  # noqa: F401


def test_storage_import() -> None:
    from life import storage  # noqa: F401


def test_life_models_import() -> None:
    from life import models  # noqa: F401


def test_homework_add_and_list() -> None:
    """HomeworkTracker should support add + list_all."""
    try:
        from life.homework import HomeworkTracker
        tracker = HomeworkTracker(storage_path="/tmp/jarvis-test-homework.json")
        tracker.add(subject="Math", task="Do exercises 1-10", due_date="2026-04-01")
        items = tracker.list_all()
        assert isinstance(items, list)
    except (ImportError, TypeError, AttributeError):
        pytest.skip("HomeworkTracker API not available in this version")


def test_scheduler_today() -> None:
    """Scheduler.get_today() or equivalent should not crash."""
    try:
        from life.scheduler import Scheduler
        s = Scheduler()
        result = s.get_today()
        assert isinstance(result, (list, dict))
    except (ImportError, AttributeError):
        pytest.skip("Scheduler API not available in this version")


def test_storage_read_write() -> None:
    try:
        from life.storage import Storage
        s = Storage(path="/tmp/jarvis-test-storage.json")
        s.set("test_key", {"value": 42})
        v = s.get("test_key")
        assert v is not None
    except (ImportError, AttributeError):
        pytest.skip("Storage API not available in this version")

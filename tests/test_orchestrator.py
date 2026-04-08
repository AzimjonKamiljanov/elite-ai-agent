"""Tests for the orchestrator — modes, provider fallback, offline mode."""

from __future__ import annotations

import asyncio

import pytest

from core.model_router import ModelConfig, ModelRouter
from core.orchestrator import JarvisOrchestrator
from core.modes import ModeManager


# ── ModeManager ───────────────────────────────────────────────────────────────

def test_mode_manager_defaults() -> None:
    mm = ModeManager()
    assert mm.get_current_mode_name() == "pro"


def test_mode_manager_set_valid() -> None:
    mm = ModeManager()
    assert mm.set_mode("fast") is True
    assert mm.get_current_mode_name() == "fast"


def test_mode_manager_set_invalid() -> None:
    mm = ModeManager()
    assert mm.set_mode("nonexistent_mode") is False
    assert mm.get_current_mode_name() == "pro"  # unchanged


def test_mode_manager_list_modes() -> None:
    mm = ModeManager()
    modes = mm.list_modes()
    for required in ("fast", "code", "pro", "study", "planner"):
        assert required in modes


def test_mode_manager_system_prompt_contains_jarvis() -> None:
    mm = ModeManager()
    prompt = mm.get_system_prompt()
    assert "JARVIS" in prompt


def test_mode_manager_all_modes_have_prompts() -> None:
    mm = ModeManager()
    for mode in mm.list_modes():
        mm.set_mode(mode)
        prompt = mm.get_system_prompt()
        assert len(prompt) > 10, f"Mode '{mode}' has an empty system prompt"


# ── Orchestrator (with stubs) ─────────────────────────────────────────────────

class _OfflineOnlyRouter(ModelRouter):
    """Router that always selects the first offline-capable model."""

    def select_model(self, user_input: str, force_offline: bool = False, **kwargs) -> ModelConfig:
        for m in self._registry:
            if m.offline_capable:
                return m
        raise RuntimeError("No offline model")


@pytest.mark.asyncio
async def test_orchestrator_mode_switching() -> None:
    orc = JarvisOrchestrator()
    assert orc.get_mode() == "pro"
    assert orc.set_mode("fast") is True
    assert orc.get_mode() == "fast"
    assert orc.set_mode("code") is True
    assert orc.get_mode() == "code"
    assert orc.set_mode("unknown") is False
    assert orc.get_mode() == "code"  # unchanged


@pytest.mark.asyncio
async def test_orchestrator_get_available_providers() -> None:
    """get_available_providers should always return a list."""
    orc = JarvisOrchestrator()
    await orc.initialize()
    providers = orc.get_available_providers()
    assert isinstance(providers, list)


@pytest.mark.asyncio
async def test_orchestrator_process_message_no_providers() -> None:
    """When no providers have keys, process_message should return a graceful error message."""
    orc = JarvisOrchestrator()
    await orc.initialize()

    # Clear all providers so nothing is available
    for p in orc._providers.values():
        p._client = None  # type: ignore
        try:
            p._api_key = None  # type: ignore
        except AttributeError:
            pass
        try:
            p._base_url = "http://localhost:0"  # guarantee offline failure
        except AttributeError:
            pass

    result = await orc.process_message("Hello", session_id="test")
    # Should return something (not crash)
    assert "response" in result
    assert isinstance(result["response"], str)


@pytest.mark.asyncio
async def test_orchestrator_memory_persists() -> None:
    orc = JarvisOrchestrator(short_term_limit=10)
    # Simulate adding to short-term memory
    orc._memory.add_to_short_term("user", "first message")
    orc._memory.add_to_short_term("assistant", "first reply")
    history = orc._memory.get_conversation_history()
    assert len(history) == 2


@pytest.mark.asyncio
async def test_orchestrator_set_router() -> None:
    orc = JarvisOrchestrator()
    new_router = _OfflineOnlyRouter()
    orc.set_router(new_router)
    assert orc._router is new_router


# ── CLI mode commands ─────────────────────────────────────────────────────────

def test_cli_mode_commands_map() -> None:
    """Verify all mode commands map to valid modes."""
    from apps.cli.main import _MODE_COMMANDS
    mm = ModeManager()
    valid = mm.list_modes()
    for cmd, mode in _MODE_COMMANDS.items():
        assert mode in valid, f"Command '{cmd}' maps to unknown mode '{mode}'"


# ── Offline mode stub ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_model_router_offline_only() -> None:
    """force_offline should only route to Ollama models."""
    router = ModelRouter()
    model = router.select_model("hi", force_offline=True)
    assert model.offline_capable is True
    assert model.provider == "ollama"

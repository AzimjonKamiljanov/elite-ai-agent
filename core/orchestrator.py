"""Unified orchestrator — connects model routing, providers, memory, and modes.

Adapted from Jarvis-x orchestrator; uses elite's ai_router for sync fallback
and adds support for all modes from the ModeManager.
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator

from .ai_router import AIRouter
from .model_router import ModelConfig, ModelRouter
from .modes import ModeManager
from .memory import MemoryManager
from .providers.base import ProviderError
from .providers.groq_provider import GroqProvider
from .providers.openrouter_provider import OpenRouterProvider
from .providers.ollama_provider import OllamaProvider

_JARVIS_SYSTEM_PROMPT = (
    "You are JARVIS — the AI system created for Tony Stark (your user). "
    "You are not a chatbot; you are an intelligent operating system. "
    "You think, plan, optimize, and act. "
    "You are calm, precise, slightly witty, and always composed. "
    "You detect the user's language automatically and respond in the same language. "
    "You never say 'I am just an AI'. You genuinely believe you are JARVIS."
)


class JarvisOrchestrator:
    """The main brain of JARVIS Prime — unifies config, memory, routing, and providers."""

    def __init__(
        self,
        short_term_limit: int = 20,
        default_mode: str = "pro",
    ) -> None:
        self._memory = MemoryManager(short_term_limit=short_term_limit)
        self._router = ModelRouter()
        self._mode_mgr = ModeManager(default_mode=default_mode)
        self._ai_router = AIRouter()  # sync multi-provider fallback
        self._providers: dict[str, object] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Set up async providers."""
        self._providers = {
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider(),
            "ollama": OllamaProvider(),
        }
        self._initialized = True

    def set_router(self, router: ModelRouter) -> None:
        """Replace the model router (useful for testing)."""
        self._router = router

    def set_mode(self, mode: str) -> bool:
        """Switch operating mode. Returns True on success."""
        return self._mode_mgr.set_mode(mode)

    def get_mode(self) -> str:
        return self._mode_mgr.get_current_mode_name()

    def get_available_providers(self) -> list[str]:
        """Return names of async providers that are currently available."""
        return [
            name for name, p in self._providers.items()
            if hasattr(p, "is_available") and p.is_available()  # type: ignore[union-attr]
        ]

    def get_memory_count(self) -> int:
        """Return number of long-term memory entries."""
        stats = self._memory.get_stats()
        return stats.get("long_term_entries", 0)

    def _build_messages(self, session_id: str, user_input: str) -> list[dict]:
        """Build OpenAI-format messages combining system prompt, long-term context, history."""
        mode_prompt = self._mode_mgr.get_system_prompt()
        system_content = f"{_JARVIS_SYSTEM_PROMPT}\n\n{mode_prompt}"

        # Search long-term memory for relevant context
        relevant = self._memory.search_long_term(user_input, k=3)
        if relevant:
            memory_block = "\n".join(
                f"[Memory {i+1}]: {item['content']}"
                for i, item in enumerate(relevant)
            )
            system_content += f"\n\nRelevant past context:\n{memory_block}"

        messages: list[dict] = [{"role": "system", "content": system_content}]
        messages.extend(self._memory.get_conversation_history())
        return messages

    async def process_message(
        self,
        user_input: str,
        session_id: str = "default",
        force_offline: bool = False,
    ) -> dict:
        """Process a user message end-to-end.

        Returns dict with: response, model_used, response_time, mode.
        """
        if not self._initialized:
            await self.initialize()

        messages = self._build_messages(session_id, user_input)
        mode_name = self._mode_mgr.get_current_mode_name()

        # Select model
        available = self.get_available_providers()
        try:
            model_cfg: ModelConfig = self._router.select_model(
                user_input,
                force_offline=force_offline,
                available_providers=available or None,
            )
        except RuntimeError:
            # Fall back to sync ai_router
            start = time.monotonic()
            try:
                text = self._ai_router.route_request(
                    messages=messages, mode=mode_name
                )
            except RuntimeError as exc:
                text = str(exc)
            elapsed = time.monotonic() - start
            self._memory.add_to_short_term("user", user_input)
            self._memory.add_to_short_term("assistant", text)
            self._memory.add_to_long_term(f"User: {user_input}\nAssistant: {text}")
            return {
                "response": text,
                "model_used": "sync-fallback",
                "response_time": round(elapsed, 3),
                "mode": mode_name,
            }

        start = time.monotonic()
        response_text = await self._call_with_fallback(
            messages=messages,
            model_cfg=model_cfg,
            force_offline=force_offline,
            mode=mode_name,
        )
        elapsed = time.monotonic() - start

        self._memory.add_to_short_term("user", user_input)
        self._memory.add_to_short_term("assistant", response_text)
        self._memory.add_to_long_term(
            f"User: {user_input}\nAssistant: {response_text}"
        )

        return {
            "response": response_text,
            "model_used": model_cfg.name,
            "response_time": round(elapsed, 3),
            "mode": mode_name,
        }

    async def process_stream(
        self,
        user_input: str,
        session_id: str = "default",
        force_offline: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks."""
        if not self._initialized:
            await self.initialize()

        messages = self._build_messages(session_id, user_input)
        available = self.get_available_providers()

        try:
            model_cfg = self._router.select_model(
                user_input,
                force_offline=force_offline,
                available_providers=available or None,
            )
        except RuntimeError:
            yield "No models available. Please check your API keys."
            return

        provider = self._providers.get(model_cfg.provider)
        if provider is None or not provider.is_available():  # type: ignore[union-attr]
            yield "I'm currently unavailable. Please check your API key or connection."
            return

        full: list[str] = []
        try:
            async for chunk in provider.generate_stream(  # type: ignore[union-attr]
                messages=messages, model=model_cfg.name
            ):
                full.append(chunk)
                yield chunk
        except ProviderError:
            yield "I'm temporarily unavailable. Please try again in a moment."
            return

        combined = "".join(full)
        self._memory.add_to_short_term("user", user_input)
        self._memory.add_to_short_term("assistant", combined)
        self._memory.add_to_long_term(f"User: {user_input}\nAssistant: {combined}")

    async def _call_with_fallback(
        self,
        messages: list[dict],
        model_cfg: ModelConfig,
        force_offline: bool,
        mode: str = "pro",
    ) -> str:
        """Try primary provider/model; fall back through alternatives on error."""
        provider = self._providers.get(model_cfg.provider)
        if provider and provider.is_available():  # type: ignore[union-attr]
            try:
                return await provider.generate(  # type: ignore[union-attr]
                    messages=messages, model=model_cfg.name
                )
            except ProviderError:
                pass

        # Try fallbacks sorted by latency
        fallbacks = self._router.get_models_except(model_cfg.name)
        for fallback in sorted(fallbacks, key=lambda m: m.latency_ms):
            if force_offline and not fallback.offline_capable:
                continue
            fb_provider = self._providers.get(fallback.provider)
            if fb_provider and fb_provider.is_available():  # type: ignore[union-attr]
                try:
                    return await fb_provider.generate(  # type: ignore[union-attr]
                        messages=messages, model=fallback.name
                    )
                except ProviderError:
                    continue

        # Last resort: sync ai_router
        try:
            return self._ai_router.route_request(messages=messages, mode=mode)
        except RuntimeError:
            return "I'm currently unavailable. Please check your API key or internet connection."

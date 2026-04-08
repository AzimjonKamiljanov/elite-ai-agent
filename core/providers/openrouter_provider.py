"""OpenRouter async provider using httpx for async HTTP requests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from .base import BaseProvider, ProviderError

_API_BASE = "https://openrouter.ai/api/v1"


class OpenRouterProvider(BaseProvider):
    """AI provider backed by OpenRouter (supports many models via one API)."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/AzimjonKamiljanov/elite-ai-agent",
            "X-Title": "JARVIS Prime",
        }

    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not set.")
        try:
            import httpx  # type: ignore[import]
        except ImportError:
            raise ProviderError("httpx is required: pip install httpx")

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{_API_BASE}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code == 429:
                raise ProviderError("OpenRouter rate limit reached.")
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"] or ""

    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        if not self._api_key:
            raise ProviderError("OPENROUTER_API_KEY is not set.")
        try:
            import httpx  # type: ignore[import]
        except ImportError:
            raise ProviderError("httpx is required: pip install httpx")

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{_API_BASE}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as resp:
                if resp.status_code == 429:
                    raise ProviderError("OpenRouter rate limit reached.")
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue

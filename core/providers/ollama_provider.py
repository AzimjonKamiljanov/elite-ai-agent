"""Ollama provider for offline/local model inference."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from .base import BaseProvider, ProviderError

_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(BaseProvider):
    """AI provider backed by Ollama (local/offline models)."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or _DEFAULT_BASE_URL
        ).rstrip("/")

    def is_available(self) -> bool:
        """Check if Ollama server is reachable synchronously."""
        try:
            import urllib.request
            req = urllib.request.urlopen(f"{self._base_url}/api/tags", timeout=2)
            return req.status == 200
        except Exception:
            return False

    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        try:
            import httpx  # type: ignore[import]
        except ImportError:
            raise ProviderError("httpx is required: pip install httpx")

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
            except Exception as exc:
                raise ProviderError(f"Ollama error: {exc}") from exc

    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        try:
            import httpx  # type: ignore[import]
            import json
        except ImportError:
            raise ProviderError("httpx is required: pip install httpx")

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                async with client.stream(
                    "POST", f"{self._base_url}/api/chat", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                delta = chunk.get("message", {}).get("content", "")
                                if delta:
                                    yield delta
                            except Exception:
                                continue
            except Exception as exc:
                raise ProviderError(f"Ollama streaming error: {exc}") from exc

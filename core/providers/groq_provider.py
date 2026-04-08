"""Groq async provider — wraps the official groq Python client."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from .base import BaseProvider, ProviderError


class GroqProvider(BaseProvider):
    """AI provider backed by the Groq API."""

    def __init__(self, api_key: str | None = None) -> None:
        # Support both GROQ_API_KEY (new) and legacy env names
        key = api_key or os.environ.get("GROQ_API_KEY")
        self._client = None
        if key:
            try:
                from groq import AsyncGroq  # type: ignore[import]
                self._client = AsyncGroq(api_key=key)
            except ImportError:
                pass

    def is_available(self) -> bool:
        return self._client is not None

    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        if not self._client:
            raise ProviderError("GROQ_API_KEY is not set or groq package missing.")
        try:
            from groq import RateLimitError  # type: ignore[import]
            completion = await self._client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return completion.choices[0].message.content or ""
        except Exception as exc:
            if "rate" in str(exc).lower():
                raise ProviderError("Groq rate limit reached. Please wait a moment.") from exc
            raise ProviderError(f"Groq API error: {exc}") from exc

    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        if not self._client:
            raise ProviderError("GROQ_API_KEY is not set or groq package missing.")
        try:
            async with self._client.chat.completions.stream(
                model=model,
                messages=messages,  # type: ignore[arg-type]
            ) as stream:
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
        except Exception as exc:
            raise ProviderError(f"Groq streaming error: {exc}") from exc

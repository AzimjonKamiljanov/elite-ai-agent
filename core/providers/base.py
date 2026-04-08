"""Abstract base class for async AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class ProviderError(Exception):
    """Raised when an AI provider encounters an error."""


class BaseProvider(ABC):
    """Abstract base that all async AI providers must implement."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Generate a full response."""

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict],
        model: str,
    ) -> AsyncGenerator[str, None]:
        """Stream response chunks."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if provider is configured and ready."""

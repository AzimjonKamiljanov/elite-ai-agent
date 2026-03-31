"""Model router — selects the best model for a given task complexity.

Unified from Jarvis-x model_router + elite-ai-agent mode system.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskComplexity(Enum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class ModelConfig:
    name: str
    provider: str
    latency_ms: int
    quality_score: float
    offline_capable: bool


# Pre-configured registry of available models (all three providers)
_MODEL_REGISTRY: list[ModelConfig] = [
    # Groq models — fastest online inference
    ModelConfig("llama-3.1-8b-instant", "groq", 300, 0.80, False),
    ModelConfig("mixtral-8x7b-32768", "groq", 600, 0.88, False),
    ModelConfig("llama-3.3-70b-versatile", "groq", 800, 0.95, False),
    # OpenRouter models — broad model coverage
    ModelConfig("google/gemini-2.0-flash-exp:free", "openrouter", 400, 0.85, False),
    ModelConfig("meta-llama/llama-3.3-70b-instruct:free", "openrouter", 500, 0.90, False),
    ModelConfig("deepseek/deepseek-r1:free", "openrouter", 2000, 0.93, False),
    ModelConfig("anthropic/claude-sonnet-4", "openrouter", 700, 0.96, False),
    # Ollama — local/offline models
    ModelConfig("phi3:mini", "ollama", 3000, 0.65, True),
    ModelConfig("mistral:7b", "ollama", 5000, 0.75, True),
    ModelConfig("qwen2.5:3b", "ollama", 4000, 0.60, True),
]

# Keywords that indicate a complex task (bilingual: English + Uzbek)
_COMPLEX_KEYWORDS = {
    "explain", "analyze", "compare", "summarize", "write", "create",
    "generate", "design", "implement", "solve", "tushuntir", "tahlil",
    "solishtir", "yoz", "yaratish", "ishlab chiq", "qanday qilib",
    "nima uchun", "why", "how", "difference", "pros and cons",
}

# Keywords that indicate a trivial/greeting message (bilingual: English + Uzbek)
_TRIVIAL_KEYWORDS = {
    "hi", "hello", "salom", "assalomu alaykum", "hey", "thanks",
    "rahmat", "ok", "yes", "no", "ha", "yo'q", "bye", "xayr",
}


class ModelRouter:
    """Chooses the right model based on task complexity and provider availability."""

    def __init__(self, registry: list[ModelConfig] | None = None) -> None:
        self._registry = registry or _MODEL_REGISTRY

    def get_models_except(self, model_name: str) -> list[ModelConfig]:
        """Return all registered models except the named one (for fallback)."""
        return [m for m in self._registry if m.name != model_name]

    def classify_task(self, user_input: str) -> TaskComplexity:
        """Keyword-based heuristic to classify task complexity."""
        import re
        text = user_input.lower().strip()
        words = set(re.findall(r"\b\w+\b", text))

        def _any_match(keywords: set) -> bool:
            # Check whole-word matches only to avoid false substrings ("hi" in "architectures")
            for kw in keywords:
                kw_words = kw.split()
                if len(kw_words) > 1:
                    # Multi-word phrase check
                    if kw in text:
                        return True
                elif kw in words:
                    return True
            return False

        if len(text.split()) <= 3 and _any_match(_TRIVIAL_KEYWORDS):
            return TaskComplexity.TRIVIAL

        if _any_match(_TRIVIAL_KEYWORDS) and not _any_match(_COMPLEX_KEYWORDS):
            return TaskComplexity.SIMPLE

        if _any_match(_COMPLEX_KEYWORDS) or len(text.split()) > 20:
            return TaskComplexity.COMPLEX

        if len(text.split()) > 8:
            return TaskComplexity.MODERATE

        return TaskComplexity.SIMPLE

    def select_model(
        self,
        user_input: str,
        force_offline: bool = False,
        available_providers: list[str] | None = None,
    ) -> ModelConfig:
        """Select the best model for the given input.

        Args:
            user_input: The user's message.
            force_offline: Only consider offline-capable models.
            available_providers: If given, restrict to these providers.

        Returns:
            The chosen ModelConfig.

        Raises:
            RuntimeError: If no suitable model is found.
        """
        complexity = self.classify_task(user_input)
        candidates = list(self._registry)

        if available_providers is not None:
            candidates = [m for m in candidates if m.provider in available_providers]
            if not candidates:
                raise RuntimeError(
                    f"No models available for providers: {available_providers}"
                )

        if force_offline:
            candidates = [m for m in candidates if m.offline_capable]
            if not candidates:
                raise RuntimeError("No offline-capable models available.")

        if complexity in (TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE):
            return min(candidates, key=lambda m: m.latency_ms)

        return max(candidates, key=lambda m: m.quality_score)

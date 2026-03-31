"""Tests for the unified model router."""

from __future__ import annotations

import pytest

from core.model_router import ModelConfig, ModelRouter, TaskComplexity


@pytest.fixture
def router() -> ModelRouter:
    return ModelRouter()


def test_classify_trivial(router: ModelRouter) -> None:
    assert router.classify_task("hi") == TaskComplexity.TRIVIAL
    assert router.classify_task("salom") == TaskComplexity.TRIVIAL
    assert router.classify_task("hello") == TaskComplexity.TRIVIAL


def test_classify_simple(router: ModelRouter) -> None:
    assert router.classify_task("yes thanks") in (TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE)


def test_classify_complex(router: ModelRouter) -> None:
    c = router.classify_task("explain the difference between transformers and RNNs in detail")
    assert c == TaskComplexity.COMPLEX


def test_classify_moderate(router: ModelRouter) -> None:
    c = router.classify_task("what is machine learning and how does it work")
    assert c in (TaskComplexity.MODERATE, TaskComplexity.COMPLEX)


def test_select_model_trivial_is_fastest(router: ModelRouter) -> None:
    """For trivial tasks, the fastest (lowest latency) model should be chosen."""
    model = router.select_model("hi")
    candidates = router._registry
    min_latency = min(m.latency_ms for m in candidates)
    assert model.latency_ms == min_latency


def test_select_model_complex_is_best_quality(router: ModelRouter) -> None:
    """For complex tasks, the highest quality model should be chosen."""
    model = router.select_model(
        "analyze and compare transformer and mamba architectures in depth"
    )
    candidates = router._registry
    max_quality = max(m.quality_score for m in candidates)
    assert model.quality_score == max_quality


def test_select_model_force_offline(router: ModelRouter) -> None:
    """force_offline should only return offline-capable models."""
    model = router.select_model("hi", force_offline=True)
    assert model.offline_capable is True


def test_select_model_available_providers(router: ModelRouter) -> None:
    """Restricting providers should only use models from those providers."""
    model = router.select_model("hi", available_providers=["groq"])
    assert model.provider == "groq"


def test_select_model_no_providers_raises(router: ModelRouter) -> None:
    with pytest.raises(RuntimeError, match="No models available"):
        router.select_model("hi", available_providers=["nonexistent"])


def test_select_model_no_offline_raises(router: ModelRouter) -> None:
    # Force offline with a custom registry that has no offline models
    online_only_registry = [
        ModelConfig("test-model", "groq", 300, 0.8, False)
    ]
    custom_router = ModelRouter(registry=online_only_registry)
    with pytest.raises(RuntimeError, match="No offline-capable"):
        custom_router.select_model("hi", force_offline=True)


def test_get_models_except(router: ModelRouter) -> None:
    name = router._registry[0].name
    rest = router.get_models_except(name)
    assert all(m.name != name for m in rest)
    assert len(rest) == len(router._registry) - 1


def test_custom_registry(router: ModelRouter) -> None:
    custom = [
        ModelConfig("fast-model", "groq", 100, 0.6, False),
        ModelConfig("slow-model", "groq", 5000, 0.99, False),
    ]
    r = ModelRouter(registry=custom)
    fast = r.select_model("hi")
    assert fast.name == "fast-model"
    slow = r.select_model("explain quantum mechanics in detail and compare interpretations")
    assert slow.name == "slow-model"

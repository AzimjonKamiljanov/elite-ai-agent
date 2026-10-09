from unittest.mock import MagicMock, patch

import pytest

from core.ai_router import AIRouter


@pytest.fixture
def mock_openai():
    with patch("core.ai_router.OpenAI") as mock:
        yield mock


def test_router_initialization():
    router = AIRouter()
    assert router._config is not None


def test_set_provider():
    router = AIRouter()

    with pytest.raises(ValueError):
        router.set_provider("invalid_provider")

    router.set_provider("gemini")
    assert router.get_current_provider() == "gemini"

    router.reset_auto()
    assert router.get_current_provider() is None


def test_set_model():
    router = AIRouter()
    router.set_model("gpt-4")
    assert router.get_current_model() == "gpt-4"


@patch("core.ai_router.AIRouter._get_client")
def test_route_request_forced_provider(mock_get_client):
    router = AIRouter()
    # Mock API keys
    router._api_keys = {"gemini": "test_key"}
    router.set_provider("gemini")

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test response"
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    mock_get_client.return_value = mock_client

    response = router.route_request([{"role": "user", "content": "Hello"}])
    assert response == "Test response"


@patch("core.ai_router.AIRouter._get_client")
def test_route_request_fallback(mock_get_client):
    router = AIRouter()
    router._api_keys = {"gemini": "test_key", "deepseek": "test_key2"}

    # Simulate first provider failing
    mock_client_fail = MagicMock()
    mock_client_fail.chat.completions.create.side_effect = Exception("API Error")

    mock_client_success = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Fallback response"
    mock_client_success.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    # Return fail first, then success
    mock_get_client.side_effect = [mock_client_fail, mock_client_success]

    response = router.route_request([{"role": "user", "content": "Hello"}])
    assert response == "Fallback response"

    # Should have called both
    assert mock_get_client.call_count == 2

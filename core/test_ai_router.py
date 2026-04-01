import pytest
from core.ai_router import AIRouter

def test_set_provider_invalid_name():
    router = AIRouter()
    invalid_name = "invalid_provider_name"

    with pytest.raises(ValueError) as excinfo:
        router.set_provider(invalid_name)

    assert f"Noto'g'ri provayder: '{invalid_name}'" in str(excinfo.value)
    assert "Mavjud:" in str(excinfo.value)

def test_set_provider_valid_name():
    router = AIRouter()
    # Using 'gemini' as it is a default provider
    router.set_provider("gemini")
    assert router.get_current_provider() == "gemini"

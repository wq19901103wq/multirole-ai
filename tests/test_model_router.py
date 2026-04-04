import pytest
from model_router import ProviderRegistry, KimiProvider, OpenAIProvider, AnthropicProvider


def test_provider_registry():
    ProviderRegistry.register("kimi", KimiProvider)
    ProviderRegistry.register("openai", OpenAIProvider)
    ProviderRegistry.register("anthropic", AnthropicProvider)

    assert ProviderRegistry.get("kimi") is KimiProvider
    assert ProviderRegistry.get("openai") is OpenAIProvider
    assert ProviderRegistry.get("anthropic") is AnthropicProvider


def test_provider_registry_unknown():
    with pytest.raises(ValueError):
        ProviderRegistry.get("unknown")

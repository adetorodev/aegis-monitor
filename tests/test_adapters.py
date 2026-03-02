"""Tests for adapters."""

import pytest
import asyncio

from aegis.adapters.mock_adapter import MockAdapter
from aegis.adapters.openai_adapter import OpenAIAdapter
from aegis.adapters.registry import AdapterRegistry


@pytest.mark.asyncio
async def test_mock_adapter_generate():
    """Test mock adapter generation."""
    adapter = MockAdapter("test-model")
    response = await adapter.generate("Hello, world!")

    assert response.text is not None
    assert response.input_tokens > 0
    assert response.output_tokens > 0
    assert response.latency_ms > 0
    assert response.model == "test-model"


@pytest.mark.asyncio
async def test_mock_adapter_with_system_prompt():
    """Test mock adapter with system prompt."""
    adapter = MockAdapter("test-model")
    response = await adapter.generate(
        prompt="What is 2+2?",
        system_prompt="You are a math tutor"
    )

    assert response.text is not None
    assert response.raw_metadata["is_mock"] is True


def test_mock_adapter_provider_name():
    """Test adapter provider name."""
    adapter = MockAdapter("test-model")
    assert adapter.provider_name == "mock"


def test_mock_adapter_validate_config():
    """Test adapter config validation."""
    adapter = MockAdapter("test-model")
    assert adapter.validate_config() is True


def test_adapter_registry():
    """Test adapter registry."""
    registry = AdapterRegistry()

    # Register adapter
    registry.register("test", MockAdapter)
    assert registry.is_registered("test")

    # Get adapter
    adapter_class = registry.get("test")
    assert adapter_class == MockAdapter

    # List providers
    providers = registry.list_providers()
    assert "test" in providers


def test_adapter_registry_duplicate():
    """Test registering duplicate adapter."""
    registry = AdapterRegistry()
    registry.register("test", MockAdapter)

    with pytest.raises(ValueError):
        registry.register("test", MockAdapter)


def test_openai_adapter_provider_name():
    """OpenAI adapter should report openai provider name."""
    adapter = OpenAIAdapter("gpt-4", api_key="test-key")
    assert adapter.provider_name == "openai"


def test_openai_adapter_validate_config_missing_key(monkeypatch):
    """Missing API key should fail fast on config validation."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    adapter = OpenAIAdapter("gpt-4", api_key=None)

    with pytest.raises(ValueError):
        adapter.validate_config()

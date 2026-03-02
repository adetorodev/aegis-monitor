# Creating Custom Adapters

This guide explains how to create a custom LLM adapter for Aegis Monitor.

## Overview

An adapter is a plugin that integrates a specific LLM provider into Aegis Monitor. Adapters abstract away provider-specific details (API calls, token counting, response formats) behind a common interface.

## Architecture

All adapters inherit from `BaseModelAdapter`:

```python
from aegis.adapters.base import BaseModelAdapter, ModelResponse

class MyCustomAdapter(BaseModelAdapter):
    """Adapter for MyProvider LLM."""

    async def call(self, prompt: str, **kwargs) -> ModelResponse:
        """Execute a prompt and return response."""
        pass

    def validate_connection(self) -> bool:
        """Verify API connectivity."""
        pass

    def get_model_info(self) -> dict:
        """Return model metadata."""
        pass
```

## Step 1: Create Your Adapter File

Create `aegis/adapters/myprovider_adapter.py`:

```python
"""Adapter for MyProvider LLM service."""

import logging
from typing import Any, Optional

from aegis.adapters.base import BaseModelAdapter, ModelResponse

logger = logging.getLogger(__name__)


class MyProviderAdapter(BaseModelAdapter):
    """Adapter for MyProvider API."""

    PRICING = {
        "myprovider-large": {"input": 0.01, "output": 0.05},
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "myprovider-large"):
        """Initialize adapter.

        Args:
            api_key: API key for provider (defaults to env var).
            model: Model name to use.
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        # Initialize your HTTP client, etc.

    async def call(self, prompt: str, **kwargs: Any) -> ModelResponse:
        """Call the model.

        Args:
            prompt: Input prompt text.
            **kwargs: Additional parameters (temperature, max_tokens, etc).

        Returns:
            ModelResponse with output and metadata.
        """
        # Call your provider's API
        response = await self._call_api(prompt, **kwargs)

        # Parse response and extract:
        # - text: the generated output
        # - input_tokens: tokens used in prompt
        # - output_tokens: tokens used in response
        # - latency_ms: time to complete
        # - model: model name used
        # - raw_metadata: any provider-specific data

        return ModelResponse(
            text=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            model=self.model,
            raw_metadata={"request_id": response.request_id},
        )

    def validate_connection(self) -> bool:
        """Test API connectivity.

        Returns:
            True if API is accessible.
        """
        try:
            # Try a minimal API call
            response = self._call_api("test")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Return model metadata.

        Returns:
            Dictionary with model details including pricing.
        """
        pricing = self.PRICING.get(self.model, {"input": 0.0, "output": 0.0})

        return {
            "model": self.model,
            "provider": "myprovider",
            "pricing": {
                "input_per_1k_tokens": pricing["input"],
                "output_per_1k_tokens": pricing["output"],
            },
            "context_window": 4096,
            "supports_async": True,
        }

    async def _call_api(self, prompt: str, **kwargs) -> Any:
        """Implementation-specific API call."""
        # Your code here
        pass
```

## Step 2: Register Your Adapter

Add your adapter to the registry in `aegis/adapters/registry.py`:

```python
def get_adapter(model: str, **kwargs) -> BaseModelAdapter:
    """Get adapter for model.

    Args:
        model: Model identifier (e.g., "gpt-4", "claude-3-opus").
        **kwargs: Additional arguments for adapter.

    Returns:
        Initialized adapter instance.

    Raises:
        ValueError: If model not found.
    """
    if model.startswith("gpt-"):
        from aegis.adapters.openai_adapter import OpenAIAdapter
        return OpenAIAdapter(model=model, **kwargs)

    elif model.startswith("claude-"):
        from aegis.adapters.anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(model=model, **kwargs)

    elif model.startswith("myprovider-"):  # ADD THIS
        from aegis.adapters.myprovider_adapter import MyProviderAdapter
        return MyProviderAdapter(model=model, **kwargs)

    else:
        raise ValueError(f"Unknown model: {model}")
```

## Step 3: Write Tests

Create `tests/test_myprovider_adapter.py`:

```python
"""Tests for MyProvider adapter."""

from unittest.mock import MagicMock, patch
import pytest

from aegis.adapters.myprovider_adapter import MyProviderAdapter
from aegis.adapters.base import ModelResponse


class TestMyProviderAdapter:
    """Test MyProvider adapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        adapter = MyProviderAdapter(api_key="test-key")
        assert adapter.model == "myprovider-large"
        assert adapter.api_key == "test-key"

    def test_get_model_info(self):
        """Test model info retrieval."""
        adapter = MyProviderAdapter(api_key="test-key")
        info = adapter.get_model_info()

        assert info["provider"] == "myprovider"
        assert "pricing" in info
        assert info["supports_async"] is True

    @pytest.mark.asyncio
    async def test_call(self):
        """Test making a call."""
        adapter = MyProviderAdapter(api_key="test-key")

        # Mock the API response
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_response.input_tokens = 10
        mock_response.output_tokens = 20

        with patch.object(
            adapter, "_call_api", return_value=mock_response
        ):
            response = await adapter.call("test prompt")

            assert isinstance(response, ModelResponse)
            assert response.text == "Test response"
            assert response.input_tokens == 10
            assert response.output_tokens == 20

    def test_validate_connection(self):
        """Test connection validation."""
        adapter = MyProviderAdapter(api_key="test-key")

        with patch.object(adapter, "_call_api"):
            assert adapter.validate_connection() is True
```

## Step 4: Document Your Adapter

Add documentation in your adapter docstring:

```python
class MyProviderAdapter(BaseModelAdapter):
    """Adapter for MyProvider LLM service.

    MyProvider is a high-performance LLM service designed for production use.

    ## Models Supported

    - `myprovider-large`: Full capability model
    - `myprovider-medium`: Balanced performance
    - `myprovider-lite`: Cost-optimized

    ## Authentication

    Set `MYPROVIDER_API_KEY` environment variable or pass `api_key` parameter.

    ## Usage

    ```python
    from aegis.adapters.myprovider_adapter import MyProviderAdapter

    adapter = MyProviderAdapter(model="myprovider-large")
    response = await adapter.call("What is AI?")
    print(response.text)
    ```

    ## Pricing

    See `PRICING` class variable for current rates.

    ## Limitations

    - Maximum context window: 4096 tokens
    - Rate limit: 100 requests/minute

    ## Resources

    - [MyProvider API Docs](https://docs.myprovider.com)
    - [Example Projects](../examples)
    """
```

## Best Practices

### 1. Token Counting

Always use the provider's reported token counts, not estimates:

```python
# ✅ Good: Use provider's token count
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens

# ❌ Bad: Estimate token count
input_tokens = len(prompt.split())  # Inaccurate!
```

### 2. API Key Management

Use environment variables for sensitive data:

```python
import os

api_key = api_key or os.getenv("MYPROVIDER_API_KEY")
if not api_key:
    raise ValueError("API key required. Set MYPROVIDER_API_KEY env var.")
```

### 3. Error Handling

Handle API errors gracefully:

```python
try:
    response = await self._call_api(prompt)
except RateLimitError as e:
    logger.warning(f"Rate limited: {e}")
    raise
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 4. Latency Measurement

Always measure end-to-end latency:

```python
import time

start = time.time()
response = await self._call_api(prompt)
latency_ms = (time.time() - start) * 1000

return ModelResponse(latency_ms=latency_ms, ...)
```

### 5. Metadata Preservation

Keep provider-specific metadata for debugging:

```python
return ModelResponse(
    text=response.text,
    ...,
    raw_metadata={
        "request_id": response.request_id,
        "model_version": response.model_version,
        "finish_reason": response.finish_reason,
    },
)
```

## Testing

Run adapter tests:

```bash
pytest tests/test_myprovider_adapter.py -v
```

Run integration tests with your adapter:

```bash
aegis eval run \
  --dataset examples/qa_sample.yaml \
  --model myprovider-large
```

## Troubleshooting

### "Unknown model" error

Ensure your adapter is registered in `registry.py` and model name matches pattern.

### Token count mismatch

Some providers report tokens differently. Check the provider's documentation for token calculation method.

### Performance issues

Profile your adapter:

```python
import cProfile
import pstats
from io import StringIO

pr = cProfile.Profile()
pr.enable()
await adapter.call(prompt)
pr.disable()

s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
ps.print_stats()
print(s.getvalue())
```

## Submitting Your Adapter

To contribute your adapter to Aegis Monitor:

1. Create a feature branch: `git checkout -b adapter/myprovider`
2. Add adapter, tests, and documentation
3. Achieve 80%+ code coverage
4. Submit pull request with example usage
5. Get community feedback and merge!

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

---

**Questions?** Open an issue on [GitHub](https://github.com/yourusername/aegis-ai/issues).

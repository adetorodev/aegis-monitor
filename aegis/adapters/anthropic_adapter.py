"""Anthropic Claude adapter for Aegis AI."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from aegis.adapters.base import BaseModelAdapter, ModelResponse

logger = logging.getLogger(__name__)

try:
    from anthropic import Anthropic, AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class AnthropicAdapter(BaseModelAdapter):
    """Adapter for Anthropic Claude models."""

    PRICING = {
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3.5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
        **kwargs: Any,
    ) -> None:
        """Initialize Anthropic adapter.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var).
            model: Model to use.
            **kwargs: Additional parameters passed to Anthropic client.

        Raises:
            ImportError: If anthropic package not installed.
        """
        if not HAS_ANTHROPIC:
            raise ImportError(
                "anthropic package not installed. "
                'Install with: pip install "aegis-ai[anthropic]"'
            )

        super().__init__()
        self.model = model
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
        self.async_client = (
            AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()
        )

    async def call(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> ModelResponse:
        """Call Claude model asynchronously.

        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum output tokens.
            **kwargs: Additional parameters.

        Returns:
            ModelResponse with output and metrics.
        """
        start_time = time.time()

        try:
            # Use async client
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract text from response
            text = response.content[0].text

            # Extract token counts
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            return ModelResponse(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                model=self.model,
                raw_metadata={
                    "id": response.id,
                    "stop_reason": response.stop_reason,
                },
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def call_sync(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> ModelResponse:
        """Call Claude model synchronously.

        Args:
            prompt: Input prompt text.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum output tokens.
            **kwargs: Additional parameters.

        Returns:
            ModelResponse with output and metrics.
        """
        start_time = time.time()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            latency_ms = (time.time() - start_time) * 1000

            # Extract text from response
            text = response.content[0].text

            # Extract token counts
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            return ModelResponse(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                model=self.model,
                raw_metadata={
                    "id": response.id,
                    "stop_reason": response.stop_reason,
                },
            )

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def validate_connection(self) -> bool:
        """Verify connection to Anthropic API.

        Returns:
            True if API is accessible.
        """
        try:
            # Try a minimal API call to verify connection
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            Dictionary with model details.
        """
        pricing = self.PRICING.get(
            self.model,
            {"input": 0.0, "output": 0.0},
        )

        return {
            "model": self.model,
            "provider": "anthropic",
            "pricing": {
                "input_per_1k_tokens": pricing["input"],
                "output_per_1k_tokens": pricing["output"],
            },
            "context_window": self._get_context_window(),
            "supports_async": True,
        }

    def _get_context_window(self) -> int:
        """Get context window for model.

        Returns:
            Context window size in tokens.
        """
        if "opus" in self.model:
            return 200000
        elif "sonnet" in self.model:
            return 200000
        elif "haiku" in self.model:
            return 200000
        else:
            return 100000

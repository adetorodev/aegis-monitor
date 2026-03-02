"""Mock adapter for testing without external APIs."""

import asyncio
import time
from typing import Any, Optional

from aegis.adapters.base import BaseModelAdapter, ModelResponse


class MockAdapter(BaseModelAdapter):
    """Mock LLM adapter for testing.

    Simulates model behavior for testing purposes without making
    real API calls.
    """

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a mock response.

        Returns a simple response based on prompt length.

        Args:
            prompt: The input prompt.
            system_prompt: Optional system message.
            **kwargs: Additional parameters (ignored).

        Returns:
            ModelResponse with mock data.
        """
        # Simulate API latency
        latency_ms = len(prompt) * 0.1 + 100
        await asyncio.sleep(latency_ms / 1000)

        # Create a mock response
        text = f"Mock response to: {prompt[:50]}"

        # Estimate token counts
        input_tokens = len(prompt.split())
        output_tokens = len(text.split())

        return ModelResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=self.model,
            raw_metadata={
                "source": "mock",
                "is_mock": True,
            },
        )

    def validate_config(self) -> bool:
        """Mock config is always valid."""
        return True

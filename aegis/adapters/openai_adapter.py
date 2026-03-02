"""OpenAI adapter implementation."""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Optional

from aegis.adapters.base import BaseModelAdapter, ModelResponse


class OpenAIAdapter(BaseModelAdapter):
    """OpenAI adapter using the official OpenAI Python SDK."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize OpenAI adapter.

        Args:
            model: OpenAI model name.
            api_key: Optional API key override.
            timeout: Request timeout in seconds.
            max_retries: Number of retry attempts.
        """
        super().__init__(model)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Any = None

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    def validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI adapter")
        return True

    def _get_client(self) -> Any:
        """Lazily initialize and return OpenAI client."""
        if self._client is not None:
            return self._client

        self.validate_config()
        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise ImportError(
                "OpenAI SDK is not installed. Install with: pip install openai"
            ) from error

        self._client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate response from OpenAI chat completion API."""
        client = self._get_client()

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        attempt = 0
        while True:
            attempt += 1
            start = time.perf_counter()
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs,
                )
                latency_ms = (time.perf_counter() - start) * 1000

                usage = getattr(response, "usage", None)
                input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

                choices = getattr(response, "choices", [])
                text = ""
                if choices:
                    message = getattr(choices[0], "message", None)
                    text = getattr(message, "content", "") or ""

                return ModelResponse(
                    text=text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    model=self.model,
                    raw_metadata={
                        "provider": "openai",
                        "response_id": getattr(response, "id", None),
                        "finish_reason": (
                            getattr(choices[0], "finish_reason", None)
                            if choices
                            else None
                        ),
                        "attempt": attempt,
                    },
                )
            except Exception as error:
                if attempt >= self.max_retries:
                    raise RuntimeError(
                        f"OpenAI request failed after {self.max_retries} attempts"
                    ) from error
                await asyncio.sleep(min(2 ** (attempt - 1), 5))

"""Base adapter interface for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ModelResponse:
    """Standardized response from an LLM model.

    Attributes:
        text: Generated output text from the model.
        input_tokens: Number of tokens in the input.
        output_tokens: Number of tokens in the output.
        latency_ms: Time to generate response in milliseconds.
        model: Name/identifier of the model used.
        raw_metadata: Additional provider-specific metadata.
    """
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str
    raw_metadata: dict[str, Any]


class BaseModelAdapter(ABC):
    """Abstract base class for LLM provider adapters.

    All LLM adapters must inherit from this class and implement the
    required methods. This ensures consistent interfaces across different
    providers (OpenAI, Anthropic, etc.).
    """

    def __init__(self, model: str) -> None:
        """Initialize the adapter.

        Args:
            model: The model identifier/name to use.
        """
        self.model = model

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider.

        Returns:
            Provider name (e.g., 'openai', 'anthropic', 'huggingface').
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate a response from the model.

        Args:
            prompt: The user prompt to send to the model.
            system_prompt: Optional system message to set context.
            **kwargs: Additional model-specific parameters
                     (temperature, max_tokens, etc.).

        Returns:
            ModelResponse with generated text and metadata.

        Raises:
            Exception: If API call fails or validation raises.
        """
        pass

    def validate_config(self) -> bool:
        """Validate that adapter is properly configured.

        Returns:
            True if configuration is valid.

        Raises:
            ValueError: If configuration is invalid (e.g., missing API key).
        """
        return True

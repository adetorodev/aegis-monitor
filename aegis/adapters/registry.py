"""Adapter registry for managing multiple LLM adapters."""

from typing import Type, Optional
from aegis.adapters.base import BaseModelAdapter


class AdapterRegistry:
    """Registry for managing LLM adapter implementations.

    Maintains a mapping of provider names to adapter classes,
    enabling dynamic adapter instantiation and plugin support.
    """

    def __init__(self) -> None:
        """Initialize the adapter registry."""
        self._adapters: dict[str, Type[BaseModelAdapter]] = {}

    def register(
        self, provider_name: str, adapter_class: Type[BaseModelAdapter]
    ) -> None:
        """Register a new adapter.

        Args:
            provider_name: Name of the provider (e.g., 'openai', 'anthropic').
            adapter_class: The adapter class to register.

        Raises:
            ValueError: If provider is already registered.
        """
        if provider_name in self._adapters:
            raise ValueError(f"Adapter for '{provider_name}' already registered")
        self._adapters[provider_name] = adapter_class

    def get(self, provider_name: str) -> Optional[Type[BaseModelAdapter]]:
        """Get an adapter class by provider name.

        Args:
            provider_name: Name of the provider.

        Returns:
            Adapter class if found, None otherwise.
        """
        return self._adapters.get(provider_name)

    def list_providers(self) -> list[str]:
        """List all registered providers.

        Returns:
            List of provider names.
        """
        return list(self._adapters.keys())

    def is_registered(self, provider_name: str) -> bool:
        """Check if a provider is registered.

        Args:
            provider_name: Name of the provider.

        Returns:
            True if provider is registered.
        """
        return provider_name in self._adapters


# Global registry instance
_global_registry = AdapterRegistry()


def get_registry() -> AdapterRegistry:
    """Get the global adapter registry.

    Returns:
        The global AdapterRegistry instance.
    """
    return _global_registry

"""Pricing registry for model token costs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class PricingRegistry:
    """Registry for model pricing metadata.

    Prices are expected in USD per 1K tokens.
    """

    def __init__(
        self,
        pricing_data: Optional[dict[str, dict[str, Any]]] = None,
        pricing_file: Optional[str | Path] = None,
    ) -> None:
        """Initialize registry with optional inline data or file.

        Args:
            pricing_data: In-memory pricing dictionary.
            pricing_file: Path to JSON pricing file.
        """
        self._pricing: dict[str, dict[str, Any]] = {}

        if pricing_data is not None:
            self._pricing = dict(pricing_data)
            return

        if pricing_file is not None:
            self.load_from_file(pricing_file)
            return

        default_path = Path(__file__).with_name("pricing.json")
        self.load_from_file(default_path)

    def load_from_file(self, path: str | Path) -> None:
        """Load pricing data from JSON file.

        Args:
            path: Path to pricing JSON file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If file content is not valid pricing data.
        """
        pricing_path = Path(path)
        if not pricing_path.exists():
            raise FileNotFoundError(f"Pricing file not found: {pricing_path}")

        with open(pricing_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Pricing file must contain a JSON object")

        self._pricing = data

    def register_model(
        self,
        model: str,
        input_per_1k: float,
        output_per_1k: float,
        currency: str = "USD",
    ) -> None:
        """Register or update pricing for a model."""
        self._pricing[model] = {
            "input_per_1k": input_per_1k,
            "output_per_1k": output_per_1k,
            "currency": currency,
        }

    def has_model(self, model: str) -> bool:
        """Check if model pricing exists."""
        return model in self._pricing

    def get_pricing(self, model: str) -> dict[str, Any]:
        """Get pricing metadata for a model.

        Args:
            model: Model identifier.

        Returns:
            Pricing dictionary.

        Raises:
            ValueError: If model pricing is not found.
        """
        pricing = self._pricing.get(model)
        if pricing is None:
            raise ValueError(f"No pricing configured for model: {model}")
        return pricing

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Get registry contents as dictionary."""
        return dict(self._pricing)

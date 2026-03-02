"""Cost calculation utilities."""

from __future__ import annotations

from aegis.cost.pricing_registry import PricingRegistry


class CostCalculator:
    """Calculate request costs from token usage and model pricing."""

    def __init__(self, pricing_registry: PricingRegistry) -> None:
        """Initialize calculator with pricing registry."""
        self.pricing_registry = pricing_registry

    def calculate_request_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate request cost for token usage.

        Args:
            model: Model identifier.
            input_tokens: Prompt tokens used.
            output_tokens: Completion tokens used.

        Returns:
            Monetary cost in USD.
        """
        pricing = self.pricing_registry.get_pricing(model)
        input_cost = (input_tokens / 1000.0) * float(pricing["input_per_1k"])
        output_cost = (output_tokens / 1000.0) * float(pricing["output_per_1k"])
        return input_cost + output_cost

    def calculate_breakdown(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> dict[str, float]:
        """Calculate request cost with input/output breakdown."""
        pricing = self.pricing_registry.get_pricing(model)
        input_cost = (input_tokens / 1000.0) * float(pricing["input_per_1k"])
        output_cost = (output_tokens / 1000.0) * float(pricing["output_per_1k"])
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }

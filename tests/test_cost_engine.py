"""Tests for cost engine components."""

import pytest

from aegis.cost.calculator import CostCalculator
from aegis.cost.pricing_registry import PricingRegistry


def test_pricing_registry_loads_default_pricing() -> None:
    """Registry loads packaged JSON pricing by default."""
    registry = PricingRegistry()
    pricing = registry.get_pricing("gpt-4")
    assert pricing["input_per_1k"] > 0
    assert pricing["output_per_1k"] > 0


def test_pricing_registry_register_model() -> None:
    """Registering model pricing should be queryable."""
    registry = PricingRegistry(pricing_data={})
    registry.register_model("custom-model", input_per_1k=0.01, output_per_1k=0.02)

    pricing = registry.get_pricing("custom-model")
    assert pricing["input_per_1k"] == 0.01
    assert pricing["output_per_1k"] == 0.02


def test_pricing_registry_missing_model_raises() -> None:
    """Unknown model should raise a clear error."""
    registry = PricingRegistry(pricing_data={})
    with pytest.raises(ValueError):
        registry.get_pricing("missing-model")


def test_cost_calculator_request_cost() -> None:
    """Cost is calculated from input/output token rates."""
    registry = PricingRegistry(
        pricing_data={
            "gpt-test": {
                "input_per_1k": 0.01,
                "output_per_1k": 0.02,
                "currency": "USD",
            }
        }
    )
    calculator = CostCalculator(registry)

    cost = calculator.calculate_request_cost(
        model="gpt-test",
        input_tokens=1000,
        output_tokens=1000,
    )

    assert cost == pytest.approx(0.03)


def test_cost_calculator_breakdown() -> None:
    """Breakdown includes input, output, and total cost."""
    registry = PricingRegistry(
        pricing_data={
            "gpt-test": {
                "input_per_1k": 0.03,
                "output_per_1k": 0.06,
                "currency": "USD",
            }
        }
    )
    calculator = CostCalculator(registry)

    breakdown = calculator.calculate_breakdown(
        model="gpt-test",
        input_tokens=500,
        output_tokens=250,
    )

    assert breakdown["input_cost"] == pytest.approx(0.015)
    assert breakdown["output_cost"] == pytest.approx(0.015)
    assert breakdown["total_cost"] == pytest.approx(0.03)

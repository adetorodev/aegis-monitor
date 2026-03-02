"""
Example: Custom Adapter Development

This example demonstrates how to create and use a custom LLM adapter
with Aegis AI without requiring API keys.

Run: python examples/custom_adapter.py
"""

from dataclasses import dataclass
from typing import Optional
from aegis.adapters.base import BaseModelAdapter, ModelResponse
from aegis.core.dataset import Dataset
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.core.evaluator import Evaluator
import asyncio


class SimpleRuleBasedAdapter(BaseModelAdapter):
    """
    A simple rule-based adapter that demonstrates custom adapter creation.

    This is a toy example that doesn't call any external API - perfect for
    testing and development.
    """

    @property
    def provider_name(self) -> str:
        """Adapter provider name."""
        return "rule_based"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate response using simple rules."""

        # Simulate processing time
        import time
        start = time.time()

        # Simple rule-based logic
        response_text = self._apply_rules(prompt)

        latency_ms = (time.time() - start) * 1000

        # Estimate tokens (rough approximation)
        input_tokens = len(prompt.split()) * 1.3
        output_tokens = len(response_text.split()) * 1.3

        return ModelResponse(
            text=response_text,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            latency_ms=latency_ms,
            model=self.model,
            raw_metadata={
                "method": "rule_based",
                "rules_applied": self._get_rules_applied(prompt)
            }
        )

    def get_model_info(self) -> dict:
        """Return model information."""
        return {
            "context_window": 8192,
            "provider": "rule_based",
            "supports_vision": False,
            "training_date": "2024-01",
            "description": "Simple rule-based model for demonstration"
        }

    def _apply_rules(self, prompt: str) -> str:
        """Apply simple rules to generate response."""
        prompt_lower = prompt.lower()

        # Capital questions
        if "capital" in prompt_lower:
            if "france" in prompt_lower:
                return "Paris"
            elif "japan" in prompt_lower:
                return "Tokyo"
            elif "usa" in prompt_lower or "united states" in prompt_lower:
                return "Washington D.C."
            elif "uk" in prompt_lower or "united kingdom" in prompt_lower:
                return "London"
            else:
                return "Unknown capital"

        # Math questions
        if "2 + 2" in prompt or "2+2" in prompt:
            return "4"
        elif "3 + 3" in prompt or "3+3" in prompt:
            return "6"
        elif "10 * 10" in prompt or "10*10" in prompt:
            return "100"

        # General greeting
        elif any(g in prompt_lower for g in ["hello", "hi", "greetings"]):
            return "Hello! How can I help you?"

        # Default
        else:
            return "I don't know"

    def _get_rules_applied(self, prompt: str) -> list:
        """Return which rules were applied."""
        rules = []
        prompt_lower = prompt.lower()

        if "capital" in prompt_lower:
            rules.append("geography_rules")
        if any(op in prompt for op in ["+", "-", "*", "/"]):
            rules.append("math_rules")
        if any(g in prompt_lower for g in ["hello", "hi"]):
            rules.append("greeting_rules")

        return rules if rules else ["default"]


class LocalLLMAdapter(BaseModelAdapter):
    """
    Example of a custom adapter that wraps a local LLM
    (like Ollama, llama.cpp, etc).
    """

    def __init__(self, model: str, api_url: str = "http://localhost:11434"):
        """
        Initialize local LLM adapter.

        Args:
            model: Model identifier (e.g., 'llama2', 'mistral')
            api_url: URL to local LLM server
        """
        super().__init__(model)
        self.api_url = api_url

    @property
    def provider_name(self) -> str:
        return "local_llm"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """Generate response from local LLM."""

        # In a real implementation, you would call:
        # response = await aiohttp.ClientSession().post(
        #     f"{self.api_url}/api/generate",
        #     json={"model": self.model, "prompt": prompt}
        # )

        # For demo purposes, return mock response
        return ModelResponse(
            text="Mock response from local LLM",
            input_tokens=len(prompt.split()),
            output_tokens=10,
            latency_ms=100.0,
            model=self.model,
            raw_metadata={"provider": "local_llm"}
        )

    def get_model_info(self) -> dict:
        return {
            "context_window": 4096,
            "provider": "local_llm",
            "api_url": self.api_url,
            "training_date": "varies"
        }


async def main():
    """Demonstrate custom adapter usage."""

    print("=" * 60)
    print("CUSTOM ADAPTER DEMONSTRATION")
    print("=" * 60)

    # Create a simple test dataset
    from aegis.core.dataset import TestCase

    dataset = Dataset(
        name="custom_adapter_test",
        cases=[
            TestCase(input="What is the capital of France?", expected="Paris", tags=[]),
            TestCase(input="What is 2 + 2?", expected="4", tags=[]),
            TestCase(input="What is the capital of Japan?", expected="Tokyo", tags=[]),
        ]
    )

    print(f"\n📊 Created test dataset with {len(dataset.cases)} cases\n")

    # Test custom adapter
    print("Testing SimpleRuleBasedAdapter...")
    print("-" * 60)

    adapter = SimpleRuleBasedAdapter("rule_based_v1")
    evaluator = Evaluator(
        adapter=adapter,
        scorer=ExactMatchScorer()
    )

    result = await evaluator.run(dataset)

    print(f"\n✅ Evaluation Results:")
    print(f"  - Model: {result.model}")
    print(f"  - Average Score: {result.avg_score:.2%}")
    print(f"  - Passed Cases: {sum(1 for c in result.cases if c.score == 1.0)}")
    print(f"  - Provider: {result.metadata['adapter']}")

    # Show details
    print(f"\n📋 Detailed Results:")
    for i, case in enumerate(result.cases):
        status = "✅" if case.score == 1.0 else "❌"
        print(f"\n{status} Case {i+1}:")
        print(f"  Input: {case.input}")
        print(f"  Expected: {case.expected}")
        print(f"  Actual: {case.actual}")
        print(f"  Score: {case.score:.0%}")
        print(f"  Latency: {case.latency_ms:.1f}ms")

    print("\n" + "=" * 60)
    print("HOW TO CREATE YOUR OWN ADAPTER")
    print("=" * 60)
    print("""
1. Inherit from BaseModelAdapter:
   class MyAdapter(BaseModelAdapter):
       pass

2. Implement required methods:
   - provider_name (property)
   - generate (async method)
   - get_model_info (method)

3. Return ModelResponse with:
   - text: Generated output
   - input_tokens: Token count
   - output_tokens: Token count
   - latency_ms: Generation time
   - model: Model name
   - raw_metadata: Provider metadata

4. Use in evaluation:
   adapter = MyAdapter("my-model-v1")
   evaluator = Evaluator(adapter, scorer)
   result = await evaluator.run(dataset)

See docs/ADAPTER_DEVELOPMENT.md for detailed guide!
""")


if __name__ == "__main__":
    asyncio.run(main())

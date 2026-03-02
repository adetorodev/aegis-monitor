"""
Example: Sentiment Analysis Classification

This example demonstrates how to evaluate a sentiment classification model
using Aegis AI with different scoring approaches.

Run: python examples/sentiment_classification.py
"""

import yaml
from pathlib import Path
from aegis.core.dataset import Dataset
from aegis.adapters.openai_adapter import OpenAIAdapter
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.scoring.composite import CompositeScorer
from aegis.core.evaluator import Evaluator
from aegis.storage.sqlite_backend import SQLiteBackend


def create_sentiment_dataset():
    """Create a sentiment analysis test dataset."""
    dataset_yaml = """
name: sentiment_classification
description: Sentiment analysis evaluation dataset
cases:
  - input: "I absolutely loved this product! Best purchase ever."
    expected: "positive"
    tags: ["strong_positive"]

  - input: "This is terrible and I want my money back."
    expected: "negative"
    tags: ["strong_negative"]

  - input: "It's okay, nothing special."
    expected: "neutral"
    tags: ["neutral"]

  - input: "Pretty good, would recommend to friends."
    expected: "positive"
    tags: ["positive"]

  - input: "Waste of money, broke after a week."
    expected: "negative"
    tags: ["negative"]

  - input: "Decent quality for the price."
    expected: "positive"
    tags: ["positive"]

  - input: "Not what I expected but works fine."
    expected: "neutral"
    tags: ["neutral"]

  - input: "Amazing! Exceeded all expectations!"
    expected: "positive"
    tags: ["strong_positive"]
"""

    # Write to temporary file
    dataset_file = Path("sentiment_data.yaml")
    dataset_file.write_text(dataset_yaml)
    return dataset_file


async def main():
    """Run sentiment analysis evaluation."""

    # Create test dataset
    dataset_file = create_sentiment_dataset()
    print(f"✅ Created test dataset: {dataset_file}\n")

    # Load dataset
    dataset = Dataset.from_yaml(str(dataset_file))
    print(f"📊 Loaded {len(dataset.cases)} sentiment test cases\n")

    # Setup storage
    storage = SQLiteBackend("sentiment_eval.db")
    storage.initialize()

    # Test with Mock Adapter (no API calls)
    print("=" * 60)
    print("EVALUATION 1: Mock Adapter (For Testing)")
    print("=" * 60)

    evaluator = Evaluator(
        adapter=MockAdapter("mock-sentiment-classifier"),
        scorer=ExactMatchScorer(),
        storage=storage
    )

    result = await evaluator.run(dataset)

    print(f"\n📈 Results:")
    print(f"  - Models Tested: {result.model}")
    print(f"  - Average Score: {result.avg_score:.2%}")
    print(f"  - Total Cases: {len(result.cases)}")
    print(f"  - Passed: {sum(1 for c in result.cases if c.score == 1.0)}")
    print(f"  - Failed: {sum(1 for c in result.cases if c.score == 0.0)}")

    # Show sample results
    print(f"\n📋 Sample Results:")
    for i, case in enumerate(result.cases[:3]):
        status = "✅" if case.score == 1.0 else "❌"
        print(f"  {status} Case {i+1}:")
        print(f"     Input: {case.input[:50]}...")
        print(f"     Expected: {case.expected}")
        print(f"     Actual: {case.actual}")
        print(f"     Score: {case.score:.0%}\n")

    # Save baseline for future comparisons
    baseline_data = {
        "dataset_name": dataset.name,
        "model": result.model,
        "avg_score": result.avg_score,
        "total_cost": result.total_cost,
        "avg_latency": result.avg_latency,
        "cases": []
    }
    storage.save_baseline(dataset.name, baseline_data)
    print(f"✅ Baseline saved for future comparisons\n")

    # Cleanup
    dataset_file.unlink()
    print("🧹 Cleanup complete")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

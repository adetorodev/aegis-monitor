"""Simple evaluation example demonstrating basic usage."""

from aegis.core.dataset import Dataset
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.storage.memory_backend import InMemoryStorage
from aegis.core.evaluator import Evaluator


def main() -> None:
    """Run a simple evaluation example."""
    print("Aegis AI - Simple Evaluation Example")
    print("=" * 50)

    # Load dataset
    print("\n1. Loading dataset...")
    dataset = Dataset.from_yaml("examples/datasets/qa_sample.yaml")
    print(f"   ✓ Loaded {len(dataset)} test cases")

    # Initialize components
    print("\n2. Initializing components...")
    adapter = MockAdapter("gpt-4")
    scorer = ExactMatchScorer()
    storage = InMemoryStorage()
    storage.initialize()
    print("   ✓ All components ready")

    # Run evaluation
    print("\n3. Running evaluation...")
    evaluator = Evaluator(adapter, scorer, storage)
    result = evaluator.run_sync(dataset)

    # Display results
    print("\n4. Results:")
    print("-" * 50)
    print(result.summary())
    print("-" * 50)
    print(f"\nRun ID: {result.run_id}")
    print(f"Passed: {result.passed_cases}/{result.total_cases}")

    # Save baseline
    print(f"\n5. Saving baseline...")
    storage.save_baseline(dataset.name, result.to_dict())
    print(f"   ✓ Baseline saved")


if __name__ == "__main__":
    main()

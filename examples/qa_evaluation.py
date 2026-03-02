"""
Example: Question Answering System Evaluation

This example evaluates a QA system using semantic similarity scoring
to handle variations in correct answers.

Run: python examples/qa_evaluation.py
"""

import yaml
import json
from pathlib import Path
from aegis.core.dataset import Dataset
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.semantic_similarity import SemanticSimilarityScorer
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.scoring.composite import CompositeScorer
from aegis.core.evaluator import Evaluator
from aegis.storage.sqlite_backend import SQLiteBackend
from aegis.cost.calculator import CostCalculator


def create_qa_dataset():
    """Create a QA evaluation dataset."""
    dataset_yaml = """
name: qa_benchmark
description: Question-answering system evaluation
cases:
  - input: "What is the capital of France?"
    expected: "The capital of France is Paris."
    tags: ["geography", "capitals"]

  - input: "Who wrote Romeo and Juliet?"
    expected: "William Shakespeare wrote Romeo and Juliet."
    tags: ["literature", "shakespeare"]

  - input: "What is 2 + 2?"
    expected: "4"
    tags: ["math", "arithmetic"]

  - input: "Explain photosynthesis in simple terms."
    expected: "Photosynthesis is how plants convert sunlight into energy."
    tags: ["science", "biology"]

  - input: "What year did World War II end?"
    expected: "1945"
    tags: ["history", "dates"]
"""

    dataset_file = Path("qa_data.yaml")
    dataset_file.write_text(dataset_yaml)
    return dataset_file


async def evaluate_with_different_scorers():
    """Evaluate QA system with different scoring approaches."""

    # Create test dataset
    dataset_file = create_qa_dataset()
    print(f"✅ Created test dataset: {dataset_file}\n")

    # Load dataset
    dataset = Dataset.from_yaml(str(dataset_file))
    print(f"📊 Loaded {len(dataset.cases)} QA test cases\n")

    # Setup storage
    storage = SQLiteBackend("qa_eval.db")
    storage.initialize()

    # Setup cost calculator
    cost_calculator = CostCalculator()

    results = {}

    # Evaluate with Exact Match
    print("=" * 60)
    print("EVALUATION 1: Exact Match Scoring")
    print("=" * 60)

    evaluator_exact = Evaluator(
        adapter=MockAdapter("qa-system-v1"),
        scorer=ExactMatchScorer(),
        storage=storage,
        cost_calculator=cost_calculator
    )

    result_exact = await evaluator_exact.run(dataset)
    results["exact_match"] = {
        "avg_score": result_exact.avg_score,
        "total_cost": result_exact.total_cost,
        "passed": sum(1 for c in result_exact.cases if c.score == 1.0)
    }

    print(f"\n📊 Exact Match Results:")
    print(f"  - Average Score: {result_exact.avg_score:.2%}")
    print(f"  - Passed Cases: {results['exact_match']['passed']}/{len(dataset.cases)}")
    print(f"  - Total Cost: ${result_exact.total_cost:.4f}")

    # Evaluate with Semantic Similarity
    print("\n" + "=" * 60)
    print("EVALUATION 2: Semantic Similarity Scoring")
    print("=" * 60)

    try:
        evaluator_semantic = Evaluator(
            adapter=MockAdapter("qa-system-v1"),
            scorer=SemanticSimilarityScorer(threshold=0.5),
            storage=storage,
            cost_calculator=cost_calculator
        )

        result_semantic = await evaluator_semantic.run(dataset)
        results["semantic"] = {
            "avg_score": result_semantic.avg_score,
            "total_cost": result_semantic.total_cost,
            "passed": sum(1 for c in result_semantic.cases if c.score >= 0.5)
        }

        print(f"\n📊 Semantic Similarity Results:")
        print(f"  - Average Score: {result_semantic.avg_score:.2%}")
        print(f"  - Passed Cases: {results['semantic']['passed']}/{len(dataset.cases)}")
        print(f"  - Total Cost: ${result_semantic.total_cost:.4f}")
    except Exception as e:
        print(f"⚠️  Semantic similarity skipped: {e}")
        print("   (requires: pip install sentence-transformers)")

    # Evaluate with Composite (both methods)
    print("\n" + "=" * 60)
    print("EVALUATION 3: Composite Scoring (Hybrid)")
    print("=" * 60)

    try:
        composite_scorer = CompositeScorer(
            scorers={
                "exact": ExactMatchScorer(),
                "semantic": SemanticSimilarityScorer(threshold=0.5)
            },
            weights={"exact": 0.3, "semantic": 0.7}
        )

        evaluator_composite = Evaluator(
            adapter=MockAdapter("qa-system-v1"),
            scorer=composite_scorer,
            storage=storage,
            cost_calculator=cost_calculator
        )

        result_composite = await evaluator_composite.run(dataset)
        results["composite"] = {
            "avg_score": result_composite.avg_score,
            "total_cost": result_composite.total_cost
        }

        print(f"\n📊 Composite Scoring Results:")
        print(f"  - Average Score: {result_composite.avg_score:.2%}")
        print(f"  - Total Cost: ${result_composite.total_cost:.4f}")
    except Exception as e:
        print(f"⚠️  Composite scoring skipped: {e}")

    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(json.dumps(results, indent=2))

    # Analysis
    if "exact_match" in results and "semantic" in results:
        score_diff = results["semantic"]["avg_score"] - results["exact_match"]["avg_score"]
        print(f"\n💡 Insights:")
        print(f"  - Semantic scoring is {abs(score_diff):.1%} {'higher' if score_diff > 0 else 'lower'}")
        print(f"  - Semantic is more lenient with paraphrasing")
        print(f"  - Composite balances both approaches")

    # Cleanup
    dataset_file.unlink()
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(evaluate_with_different_scorers())

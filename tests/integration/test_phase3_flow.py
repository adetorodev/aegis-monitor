"""Integration test for baseline and regression features."""

import pytest
from pathlib import Path

from aegis.core.dataset import Dataset, TestCase
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.scoring.semantic_similarity import SemanticSimilarityScorer
from aegis.scoring.composite import CompositeScorer
from aegis.storage.sqlite_backend import SQLiteBackend
from aegis.core.evaluator import Evaluator
from aegis.core.regression import RegressionDetector


@pytest.mark.asyncio
async def test_baseline_and_regression_workflow(tmp_path: Path):
    """Test full baseline save, load, and regression detection workflow."""
    # Setup
    cases = [
        TestCase(input="Q1", expected="A1"),
        TestCase(input="Q2", expected="A2"),
    ]
    dataset = Dataset(name="test_regression", cases=cases)

    db_path = tmp_path / "test_regression.db"
    storage = SQLiteBackend(db_path)
    storage.initialize()

    adapter = MockAdapter("test-model")
    scorer = ExactMatchScorer()

    # Run baseline evaluation
    evaluator_baseline = Evaluator(adapter, scorer, storage)
    baseline_result = await evaluator_baseline.run(dataset)

    # Save as baseline
    storage.save_baseline("test_regression", baseline_result.to_dict())

    # Load baseline
    loaded_baseline = storage.load_baseline("test_regression")
    assert loaded_baseline is not None
    assert loaded_baseline["dataset_name"] == "test_regression"

    # Run current evaluation
    evaluator_current = Evaluator(adapter, scorer, storage)
    current_result = await evaluator_current.run(dataset)

    # Check regression
    detector = RegressionDetector()
    analysis = detector.compare(current_result.to_dict(), loaded_baseline)

    # Should pass since same adapter/scorer
    assert analysis.status == "pass"

    storage.close()


@pytest.mark.asyncio
async def test_composite_scorer_in_evaluation(tmp_path: Path):
    """Test evaluation with composite scorer."""
    cases = [
        TestCase(input="Hello world", expected="Hello world"),
        TestCase(input="Goodbye", expected="Goodbye"),
    ]
    dataset = Dataset(name="composite_test", cases=cases)

    exact_scorer = ExactMatchScorer()
    semantic_scorer = SemanticSimilarityScorer()
    composite = CompositeScorer(
        scorers={"exact": exact_scorer, "semantic": semantic_scorer},
        weights={"exact": 0.3, "semantic": 0.7},
    )

    adapter = MockAdapter("test-model")
    evaluator = Evaluator(adapter, composite)
    result = await evaluator.run(dataset)

    assert result.total_cases == 2
    # Composite should score between 0 and 1
    assert 0.0 <= result.avg_score <= 1.0


def test_baseline_cli_workflow(tmp_path: Path):
    """Test baseline management through storage backend."""
    db_path = tmp_path / "test_baseline.db"
    storage = SQLiteBackend(db_path)
    storage.initialize()

    # Create mock run data
    run_data = {
        "run_id": "test-run-001",
        "dataset_name": "test_ds",
        "model": "gpt-4",
        "created_at": "2026-03-02T00:00:00",
        "metrics": {
            "avg_score": 0.95,
            "total_cost": 0.05,
            "avg_latency_ms": 100.0,
        },
    }

    # Save run
    storage.save_run(run_data, "test-run-001")

    # Load run
    loaded_run = storage.load_run("test-run-001")
    assert loaded_run is not None

    # Set as baseline
    storage.save_baseline("test_ds", loaded_run)

    # Load baseline
    baseline = storage.load_baseline("test_ds")
    assert baseline is not None
    assert baseline["run_id"] == "test-run-001"
    assert baseline["metrics"]["avg_score"] == 0.95

    storage.close()

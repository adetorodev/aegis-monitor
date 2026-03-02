"""Integration tests for complete workflows."""

import pytest
from pathlib import Path

from aegis.core.dataset import Dataset, TestCase
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.storage.memory_backend import InMemoryStorage
from aegis.core.evaluator import Evaluator


@pytest.mark.asyncio
async def test_full_evaluation_flow():
    """Test complete evaluation workflow."""
    # Create dataset
    cases = [
        TestCase(input="Q1", expected="A1"),
        TestCase(input="Q2", expected="A2"),
        TestCase(input="Q3", expected="A3"),
    ]
    dataset = Dataset(name="test_ds", cases=cases)

    # Setup components
    adapter = MockAdapter("test-model")
    scorer = ExactMatchScorer()
    storage = InMemoryStorage()
    storage.initialize()

    # Run evaluation
    evaluator = Evaluator(adapter, scorer, storage)
    result = await evaluator.run(dataset)

    # Verify results
    assert result.dataset_name == "test_ds"
    assert result.model == "test-model"
    assert result.total_cases == 3
    assert len(result.cases) == 3
    assert result.avg_score is not None
    assert result.total_cost >= 0.0

    # Verify storage
    loaded_run = storage.load_run(result.run_id)
    assert loaded_run is not None
    assert loaded_run["dataset_name"] == "test_ds"


@pytest.mark.asyncio
async def test_full_evaluation_sync():
    """Test synchronous evaluation wrapper."""
    cases = [TestCase(input="Q1", expected="A1")]
    dataset = Dataset(name="test", cases=cases)

    adapter = MockAdapter("test-model")
    scorer = ExactMatchScorer()
    storage = InMemoryStorage()
    storage.initialize()

    evaluator = Evaluator(adapter, scorer, storage)
    result = await evaluator.run(dataset)

    assert result.total_cases == 1
    assert result.dataset_name == "test"


@pytest.mark.asyncio
async def test_evaluation_with_yaml_dataset(tmp_path: Path):
    """Test evaluation with YAML dataset.

    Args:
        tmp_path: Temporary directory.
    """
    # Create YAML dataset
    yaml_content = """
name: integration_test
cases:
  - input: "What is 2+2?"
    expected: "4"
  - input: "What is the capital of France?"
    expected: "Paris"
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)

    # Load and evaluate
    dataset = Dataset.from_yaml(yaml_file)
    adapter = MockAdapter("test-model")
    scorer = ExactMatchScorer()
    evaluator = Evaluator(adapter, scorer)

    result = await evaluator.run(dataset)

    assert result.total_cases == 2
    assert len(result.cases) == 2

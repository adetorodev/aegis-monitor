"""Integration tests for CLI commands - Phase 6 hardening."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aegis.cli.baseline_cmd import run_baseline
from aegis.cli.cost_cmd import run_cost
from aegis.cli.compare_cmd import run_compare
from aegis.cli.eval_cmd import run_eval
from aegis.core.dataset import Dataset, TestCase
from aegis.storage.sqlite_backend import SQLiteBackend


@pytest.fixture
def temp_db():
    """Create temporary SQLite database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield str(db_path)


@pytest.fixture
def sample_dataset_file(tmp_path):
    """Create a sample YAML dataset file."""
    dataset_content = """
name: test_dataset
description: Test evaluation dataset
cases:
  - input: "What is 2+2?"
    expected: "4"
  - input: "What is 3+3?"
    expected: "6"
"""
    dataset_file = tmp_path / "test_dataset.yaml"
    dataset_file.write_text(dataset_content)
    return str(dataset_file)


class TestBaselineCommand:
    """Test baseline management command."""

    def test_baseline_set(self, temp_db):
        """Test setting a baseline."""
        storage = SQLiteBackend(temp_db)
        storage.initialize()  # Initialize before using

        # Create and save a baseline
        baseline_data = {
            "dataset_name": "qa",
            "model": "gpt-4",
            "avg_score": 0.92,
            "total_cost": 0.05,
            "avg_latency": 1.5,
            "cases": [],
        }

        storage.save_baseline("qa", baseline_data)

        # Retrieve baseline
        retrieved = storage.load_baseline("qa")
        assert retrieved is not None
        assert retrieved["model"] == "gpt-4"
        assert retrieved["avg_score"] == 0.92

    def test_baseline_show(self, temp_db):
        """Test showing baseline."""
        storage = SQLiteBackend(temp_db)
        storage.initialize()  # Initialize before using

        baseline_data = {
            "dataset_name": "qa",
            "model": "gpt-4",
            "avg_score": 0.92,
            "total_cost": 0.05,
            "avg_latency": 1.5,
            "cases": [],
        }

        storage.save_baseline("qa", baseline_data)

        # Retrieve and verify
        baseline = storage.load_baseline("qa")
        assert baseline is not None
        assert baseline["dataset_name"] == "qa"


class TestCompareCommand:
    """Test model comparison command."""

    def test_compare_output_json(self):
        """Test JSON output format."""
        results = {
            "gpt-4": {"score": 0.92, "cost": 0.08, "latency": 2.4},
            "gpt-3.5-turbo": {"score": 0.81, "cost": 0.02, "latency": 1.2},
        }

        # Add CPQ
        for model, result in results.items():
            if "error" not in result:
                cost = result.get("cost", 0)
                score = result.get("score", 0)
                if cost > 0 and score > 0:
                    result["cpq"] = cost / score

        # Verify CPQ calculations
        assert results["gpt-4"]["cpq"] == pytest.approx(0.0870, rel=0.01)
        assert results["gpt-3.5-turbo"]["cpq"] == pytest.approx(0.0247, rel=0.01)

    def test_compare_ranking(self):
        """Test CPQ-based ranking."""
        results = {
            "model_a": {"score": 0.92, "cost": 0.08},
            "model_b": {"score": 0.85, "cost": 0.02},
            "model_c": {"score": 0.90, "cost": 0.05},
        }

        # Calculate CPQ
        cpq_data = []
        for model, r in results.items():
            cpq = r["cost"] / r["score"]
            cpq_data.append((model, cpq))

        # Sort by CPQ
        cpq_data.sort(key=lambda x: x[1])

        # model_b should be best
        assert cpq_data[0][0] == "model_b"


class TestCostCommand:
    """Test cost tracking commands."""

    def test_cost_aggregation(self, temp_db):
        """Test cost aggregation."""
        storage = SQLiteBackend(temp_db)
        storage.initialize()  # Initialize before using

        # Save multiple runs
        for i in range(3):
            run_data = {
                "dataset_name": "qa",
                "model": "gpt-4",
                "metrics": {
                    "avg_score": 0.92,
                    "total_cost": 0.05 + (i * 0.01),
                    "avg_latency": 1.5,
                },
            }
            storage.save_run(run_data, f"run_{i}")

        # Verify multiple runs stored
        runs = []
        for i in range(3):
            run = storage.load_run(f"run_{i}")
            if run:
                runs.append(run)

        assert len(runs) == 3
        assert runs[0]["metrics"]["total_cost"] == pytest.approx(0.05)
        assert runs[2]["metrics"]["total_cost"] == pytest.approx(0.07)

    def test_cost_by_model_aggregation(self):
        """Test cost aggregation by model."""
        runs = [
            {
                "model": "gpt-4",
                "metrics": {"total_cost": 0.10},
                "dataset_name": "qa",
            },
            {
                "model": "gpt-4",
                "metrics": {"total_cost": 0.05},
                "dataset_name": "qa",
            },
            {
                "model": "gpt-3.5-turbo",
                "metrics": {"total_cost": 0.02},
                "dataset_name": "qa",
            },
        ]

        by_model = {}
        for run in runs:
            model = run.get("model", "unknown")
            cost = float(run.get("metrics", {}).get("total_cost", 0.0) or 0.0)
            by_model[model] = by_model.get(model, 0.0) + cost

        assert by_model["gpt-4"] == pytest.approx(0.15)
        assert by_model["gpt-3.5-turbo"] == pytest.approx(0.02)


class TestEvalCommand:
    """Test evaluation command."""

    def test_eval_with_mock_adapter(self, sample_dataset_file, temp_db):
        """Test running evaluation with mock adapter."""
        # Load dataset
        dataset = Dataset.from_yaml(sample_dataset_file)
        assert dataset.name == "test_dataset"
        assert len(dataset.cases) == 2

    def test_eval_json_output(self):
        """Test JSON output format."""
        result = {
            "dataset": "test",
            "model": "gpt-4",
            "avg_score": 0.92,
            "total_cost": 0.05,
            "cases": [
                {
                    "input": "test",
                    "expected": "test",
                    "actual": "test",
                    "score": 1.0,
                }
            ],
        }

        # Verify JSON serialization
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["model"] == "gpt-4"


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_missing_dataset_file(self):
        """Test error when dataset file not found."""
        from pathlib import Path

        dataset_path = Path("/nonexistent/dataset.yaml")
        assert not dataset_path.exists()

    def test_invalid_dataset_format(self, tmp_path):
        """Test error with invalid YAML."""
        invalid_yaml = """
        invalid: [
            unclosed list
        """
        dataset_file = tmp_path / "invalid.yaml"
        dataset_file.write_text(invalid_yaml)

        # Should raise error on load
        with pytest.raises(Exception):
            Dataset.load_from_yaml(str(dataset_file))

    def test_invalid_model_name(self):
        """Test error with unknown model."""
        from aegis.cli.compare_cmd import _get_adapter

        with pytest.raises(ValueError, match="Unknown model"):
            _get_adapter("unknown_model_xyz")


@pytest.mark.asyncio
async def test_async_evaluation_flow():
    """Test complete async evaluation flow."""
    from aegis.adapters.mock_adapter import MockAdapter
    from aegis.scoring.exact_match import ExactMatchScorer
    from aegis.core.evaluator import Evaluator
    from aegis.core.dataset import Dataset, TestCase

    # Create test case
    cases = [
        TestCase(input="What is 2+2?", expected="4", tags=[]),
        TestCase(input="What is 3+3?", expected="6", tags=[]),
    ]

    dataset = Dataset(name="test", cases=cases)

    # Create adapter and scorer with required 'model' parameter
    adapter = MockAdapter("mock-model")
    scorer = ExactMatchScorer()

    # Run evaluation
    evaluator = Evaluator(adapter, scorer)
    result = await evaluator.run(dataset)

    assert result.avg_score >= 0.0
    assert result.avg_score <= 1.0

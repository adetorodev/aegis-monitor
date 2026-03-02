"""Tests for cost aggregation, budget enforcement, and cost CLI."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from aegis.cost.aggregator import CostAggregator
from aegis.cost.limiter import Budget, BudgetExceededError, BudgetLimiter


class TestCostAggregator:
    """Test cost aggregation functionality."""

    def test_aggregate_by_model(self):
        """Test aggregation by model."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        # Mock run data
        with patch.object(
            aggregator,
            "_get_runs_in_period",
            return_value=[
                {
                    "model": "gpt-4",
                    "metrics": {"total_cost": 0.12},
                    "dataset_name": "qa",
                },
                {
                    "model": "gpt-4",
                    "metrics": {"total_cost": 0.15},
                    "dataset_name": "qa",
                },
                {
                    "model": "gpt-3.5-turbo",
                    "metrics": {"total_cost": 0.05},
                    "dataset_name": "qa",
                },
            ],
        ):
            result = aggregator.aggregate_by_model()

            assert result["total_cost"] == pytest.approx(0.32)
            assert "gpt-4" in result["by_model"]
            assert "gpt-3.5-turbo" in result["by_model"]
            assert result["by_model"]["gpt-4"]["cost"] == pytest.approx(0.27)
            assert result["by_model"]["gpt-3.5-turbo"]["cost"] == pytest.approx(0.05)

    def test_aggregate_by_dataset(self):
        """Test aggregation by dataset."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        with patch.object(
            aggregator,
            "_get_runs_in_period",
            return_value=[
                {
                    "model": "gpt-4",
                    "metrics": {"total_cost": 0.10},
                    "dataset_name": "qa",
                },
                {
                    "model": "gpt-4",
                    "metrics": {"total_cost": 0.20},
                    "dataset_name": "summarization",
                },
            ],
        ):
            result = aggregator.aggregate_by_dataset()

            assert result["total_cost"] == pytest.approx(0.30)
            assert result["by_dataset"]["qa"] == pytest.approx(0.10)
            assert result["by_dataset"]["summarization"] == pytest.approx(0.20)

    def test_get_top_cost_drivers(self):
        """Test top cost driver identification."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        with patch.object(
            aggregator,
            "_get_runs_in_period",
            return_value=[
                {
                    "model": "gpt-4",
                    "metrics": {"total_cost": 0.50},
                    "dataset_name": "qa",
                },
                {
                    "model": "gpt-3.5-turbo",
                    "metrics": {"total_cost": 0.10},
                    "dataset_name": "qa",
                },
                {
                    "model": "gpt-4",
                    "metrics": {"total_cost": 0.30},
                    "dataset_name": "summarization",
                },
            ],
        ):
            drivers = aggregator.get_top_cost_drivers(limit=2)

            assert len(drivers) == 2
            # Top driver should be qa/gpt-4
            assert drivers[0]["dataset"] == "qa"
            assert drivers[0]["model"] == "gpt-4"
            assert drivers[0]["cost"] == pytest.approx(0.50)

    def test_aggregate_empty_runs(self):
        """Test aggregation with no runs."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        with patch.object(aggregator, "_get_runs_in_period", return_value=[]):
            result = aggregator.aggregate_by_model()

            assert result["total_cost"] == 0.0
            assert result["by_model"] == {}


class TestBudgetLimiter:
    """Test budget enforcement."""

    def test_add_budget(self):
        """Test adding a budget."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("test", budget)

        assert "test" in limiter.budgets
        assert limiter.budgets["test"].limit == 100.0

    def test_check_budget_under_limit(self):
        """Test budget check when under limit."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("test", budget)

        with patch.object(limiter, "_get_period_spend", return_value=50.0):
            result = limiter.check_budget(10.0)

            assert result["allowed"] is True
            assert len(result["violations"]) == 0
            assert len(result["warnings"]) == 0

    def test_check_budget_warn_mode(self):
        """Test budget warning when limit exceeded."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("test", budget)

        with patch.object(limiter, "_get_period_spend", return_value=95.0):
            result = limiter.check_budget(10.0)

            assert result["allowed"] is True
            assert len(result["warnings"]) == 1
            assert result["warnings"][0]["budget_name"] == "test"

    def test_check_budget_block_mode(self):
        """Test budget blocking when limit exceeded."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="block")
        limiter.add_budget("test", budget)

        with patch.object(limiter, "_get_period_spend", return_value=95.0):
            with pytest.raises(BudgetExceededError):
                limiter.check_budget(10.0)

    def test_check_budget_log_mode(self):
        """Test budget log mode when limit exceeded."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="log")
        limiter.add_budget("test", budget)

        with patch.object(limiter, "_get_period_spend", return_value=95.0):
            result = limiter.check_budget(10.0)

            assert result["allowed"] is True
            assert len(result["violations"]) == 0
            assert len(result["warnings"]) == 0

    def test_get_budget_status(self):
        """Test getting budget status."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("test", budget)

        with patch.object(limiter, "_get_period_spend", return_value=60.0):
            status = limiter.get_budget_status("test")

            assert status["name"] == "test"
            assert status["limit"] == 100.0
            assert status["spent"] == 60.0
            assert status["remaining"] == 40.0
            assert status["utilization"] == 60.0

    def test_dataset_specific_budget(self):
        """Test dataset-specific budget enforcement."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        # Global budget
        global_budget = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("global", global_budget)

        # Dataset-specific budget
        dataset_budget = Budget(limit=50.0, period="month", mode="warn", dataset="qa")
        limiter.add_budget("qa_budget", dataset_budget)

        with patch.object(limiter, "_get_period_spend", return_value=40.0):
            # Should trigger warning for qa dataset only
            result = limiter.check_budget(15.0, dataset="qa")

            assert result["allowed"] is True
            assert len(result["warnings"]) == 1
            assert result["warnings"][0]["budget_name"] == "qa_budget"

    def test_export_budget_report(self, tmp_path):
        """Test exporting budget report."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("test", budget)

        output_path = tmp_path / "budget_report.json"

        with patch.object(limiter, "_get_period_spend", return_value=50.0):
            limiter.export_budget_report(str(output_path))

            assert output_path.exists()

    def test_multiple_budgets(self):
        """Test checking multiple budgets simultaneously."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)
        limiter = BudgetLimiter(aggregator)

        budget1 = Budget(limit=100.0, period="month", mode="warn")
        limiter.add_budget("monthly", budget1)

        budget2 = Budget(limit=10.0, period="day", mode="warn")
        limiter.add_budget("daily", budget2)

        with patch.object(
            limiter, "_get_period_spend", side_effect=[95.0, 9.0]
        ):
            result = limiter.check_budget(6.0)

            # Should have warnings for both budgets (95+6=101>100, 9+6=15>10)
            assert len(result["warnings"]) == 2
            budget_names = [w["budget_name"] for w in result["warnings"]]
            assert "monthly" in budget_names
            assert "daily" in budget_names

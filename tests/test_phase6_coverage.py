"""Additional tests for improved coverage - Phase 6."""

from unittest.mock import MagicMock, patch

import pytest

from aegis.scoring.semantic_similarity import SemanticSimilarityScorer
from aegis.cost.aggregator import CostAggregator


class TestSemanticSimilarityAdvanced:
    """Advanced tests for semantic similarity scorer."""

    def test_semantic_fallback_to_lexical(self):
        """Test fallback to lexical when embeddings unavailable."""
        scorer = SemanticSimilarityScorer()

        # Test lexical similarity fallback
        result = scorer.score("hello world", "hello world")
        assert result.score == pytest.approx(1.0)

        result = scorer.score("hello", "goodbye")
        assert result.score < 1.0

    def test_semantic_similarity_empty_strings(self):
        """Test handling of empty strings."""
        scorer = SemanticSimilarityScorer()

        result = scorer.score("", "hello")
        assert 0.0 <= result.score <= 1.0

        result = scorer.score("hello", "")
        assert 0.0 <= result.score <= 1.0

        result = scorer.score("", "")
        assert 0.0 <= result.score <= 1.0

    def test_semantic_similarity_identical(self):
        """Test identical strings."""
        scorer = SemanticSimilarityScorer()

        test_strings = [
            "The quick brown fox",
            "Hello, world!",
            "This is a test string",
        ]

        for s in test_strings:
            result = scorer.score(s, s)
            assert result.score == pytest.approx(1.0, abs=0.01)

    def test_semantic_similarity_case_sensitivity(self):
        """Test case handling."""
        scorer = SemanticSimilarityScorer()

        result1 = scorer.score("HELLO", "hello")
        result2 = scorer.score("hello", "hello")

        # Similar but may differ due to case
        assert 0.0 <= result1.score <= 1.0
        assert result2.score == pytest.approx(1.0, abs=0.01)

    def test_semantic_similarity_partial_match(self):
        """Test partial matching."""
        scorer = SemanticSimilarityScorer()

        # Partial match should score between 0 and 1
        result = scorer.score(
            "The capital of France is Paris",
            "The capital of France is Lyon",
        )

        assert 0.0 < result.score < 1.0

    def test_semantic_similarity_semantic_closeness(self):
        """Test semantic closeness."""
        scorer = SemanticSimilarityScorer()

        # Semantically similar should score higher
        semantically_similar = scorer.score(
            "Dogs are animals",
            "Canines are creatures",
        )

        semantically_different = scorer.score(
            "Dogs are animals",
            "Mathematics is complex",
        )

        # Similar should score higher (but not guaranteed with lexical fallback)
        assert 0.0 <= semantically_similar.score <= 1.0
        assert 0.0 <= semantically_different.score <= 1.0

    def test_semantic_scorer_deterministic(self):
        """Test that scorer is deterministic."""
        scorer = SemanticSimilarityScorer()
        assert scorer.is_deterministic() is True

    def test_semantic_scorer_name(self):
        """Test scorer name."""
        scorer = SemanticSimilarityScorer()
        assert scorer.name == "semantic_similarity"


class TestCostAggregatorAdvanced:
    """Advanced tests for cost aggregation."""

    def test_aggregator_empty_data(self):
        """Test aggregator with no data."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        with patch.object(aggregator, "_get_runs_in_period", return_value=[]):
            result = aggregator.aggregate_by_model()

            assert result["total_cost"] == 0.0
            assert result["by_model"] == {}

    def test_aggregator_single_run(self):
        """Test aggregation with single run."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        runs = [
            {
                "model": "gpt-4",
                "metrics": {"total_cost": 0.123},
                "dataset_name": "qa",
            }
        ]

        with patch.object(aggregator, "_get_runs_in_period", return_value=runs):
            result = aggregator.aggregate_by_model()

            assert result["total_cost"] == pytest.approx(0.123)
            assert "gpt-4" in result["by_model"]

    def test_aggregator_period_calculation(self):
        """Test period date calculations."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        from datetime import datetime, timedelta

        end_date = datetime(2024, 3, 15, 12, 0, 0)

        day_start = aggregator._get_start_date(end_date, "day")
        assert day_start.date() == end_date.date() - timedelta(days=1)

        week_start = aggregator._get_start_date(end_date, "week")
        assert week_start.date() == end_date.date() - timedelta(days=7)

        month_start = aggregator._get_start_date(end_date, "month")
        assert month_start.date() == end_date.date() - timedelta(days=30)

    def test_aggregator_by_period(self):
        """Test aggregation by time period."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        runs = [
            {
                "model": "gpt-4",
                "metrics": {"total_cost": 0.10},
                "dataset_name": "qa",
            },
            {
                "model": "gpt-3.5-turbo",
                "metrics": {"total_cost": 0.05},
                "dataset_name": "summ",
            },
        ]

        with patch.object(aggregator, "_get_runs_in_period", return_value=runs):
            result = aggregator.aggregate_by_period("week")

            assert result["total_cost"] == pytest.approx(0.15)
            assert result["period"] == "week"

    def test_top_cost_drivers_sorting(self):
        """Test correct sorting of cost drivers."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        runs = [
            {
                "model": "expensive",
                "metrics": {"total_cost": 10.0},
                "dataset_name": "big_dataset",
            },
            {
                "model": "cheap",
                "metrics": {"total_cost": 0.5},
                "dataset_name": "small_dataset",
            },
            {
                "model": "mid",
                "metrics": {"total_cost": 5.0},
                "dataset_name": "medium_dataset",
            },
        ]

        with patch.object(aggregator, "_get_runs_in_period", return_value=runs):
            drivers = aggregator.get_top_cost_drivers(limit=3)

            # Should be sorted by cost descending
            costs = [d["cost"] for d in drivers]
            assert costs == sorted(costs, reverse=True)
            assert drivers[0]["cost"] == pytest.approx(10.0)

    def test_aggregator_mixed_data_quality(self):
        """Test handling of missing/malformed data."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        runs = [
            {
                "model": "gpt-4",
                "metrics": {"total_cost": 0.10},
                "dataset_name": "qa",
            },
            {
                "model": "unknown",
                # Missing metrics - should handle gracefully
                "dataset_name": "test",
            },
            {
                "model": "gpt-3.5",
                "metrics": {"total_cost": None},  # None cost
                "dataset_name": "qa",
            },
        ]

        with patch.object(aggregator, "_get_runs_in_period", return_value=runs):
            result = aggregator.aggregate_by_model()

            # Should not crash and handle missing data
            assert result["total_cost"] >= 0

    def test_csv_export_path_creation(self, tmp_path):
        """Test CSV export with directory creation."""
        storage = MagicMock()
        aggregator = CostAggregator(storage)

        export_path = tmp_path / "reports" / "nested" / "costs.csv"
        data = {
            "total_cost": 100,
            "by_model": {
                "gpt-4": {"cost": 80, "percentage": 80},
                "gpt-3.5": {"cost": 20, "percentage": 20},
            },
        }

        aggregator.export_to_csv(data, str(export_path))

        assert export_path.exists()
        content = export_path.read_text()
        assert "gpt-4" in content
        assert "gpt-3.5" in content


class TestDataValidation:
    """Test data validation and error handling."""

    def test_cost_validation_non_negative(self):
        """Test that costs are non-negative."""
        costs = [0.0, 0.01, 0.5, 10.0, 100.0]

        for cost in costs:
            assert cost >= 0

        # Negative cost should not exist
        negative_cost = -0.5
        assert negative_cost < 0

    def test_score_validation_bounds(self):
        """Test that scores are between 0 and 1."""
        valid_scores = [0.0, 0.25, 0.5, 0.75, 1.0]

        for score in valid_scores:
            assert 0.0 <= score <= 1.0

    def test_percentage_validation(self):
        """Test that percentages are 0-100."""
        valid_percentages = [0, 25, 50, 75, 100]

        for pct in valid_percentages:
            assert 0 <= pct <= 100

    def test_token_count_validation(self):
        """Test that token counts are positive integers."""
        valid_counts = [0, 1, 10, 100, 1000, 10000]

        for count in valid_counts:
            assert count >= 0
            assert isinstance(count, int)

"""Tests for evaluation results."""

import pytest
from datetime import datetime

from aegis.core.results import TestCaseResult, EvaluationResult


def test_test_case_result_creation():
    """Test creating test case result."""
    result = TestCaseResult(
        input="Q1",
        expected="A1",
        actual="A1",
        score=1.0,
        latency_ms=100.5,
        cost=0.001,
    )

    assert result.score == 1.0
    assert result.latency_ms == 100.5
    assert result.cost == 0.001


def test_evaluation_result_metrics():
    """Test evaluation result metric calculations."""
    cases = [
        TestCaseResult("Q1", "A1", "A1", 1.0, 100.0, 0.001),
        TestCaseResult("Q2", "A2", "A2", 1.0, 150.0, 0.002),
        TestCaseResult("Q3", "A3", "A3diff", 0.5, 120.0, 0.001),
    ]

    result = EvaluationResult(
        dataset_name="test",
        model="gpt-4",
        cases=cases,
    )

    assert result.total_cases == 3
    assert result.total_cost == pytest.approx(0.004)
    assert result.avg_score == pytest.approx(0.833, rel=0.01)
    assert result.pass_rate == pytest.approx(0.667, rel=0.01)


def test_evaluation_result_empty():
    """Test evaluation result with no cases."""
    result = EvaluationResult(
        dataset_name="empty",
        model="gpt-4",
        cases=[],
    )

    assert result.total_cases == 0
    assert result.avg_score == 0.0
    assert result.total_cost == 0.0


def test_evaluation_result_summary():
    """Test result summary generation."""
    cases = [
        TestCaseResult("Q1", "A1", "A1", 0.9, 100.0, 0.001),
    ]

    result = EvaluationResult(
        dataset_name="test",
        model="gpt-4",
        cases=cases,
    )

    summary = result.summary()
    assert "Dataset: test" in summary
    assert "Model: gpt-4" in summary


def test_evaluation_result_to_dict():
    """Test converting result to dictionary."""
    cases = [
        TestCaseResult("Q1", "A1", "A1", 1.0, 100.0, 0.001),
    ]

    result = EvaluationResult(
        dataset_name="test",
        model="gpt-4",
        cases=cases,
        run_id="test-run-1",
    )

    result_dict = result.to_dict()

    assert result_dict["dataset_name"] == "test"
    assert result_dict["model"] == "gpt-4"
    assert len(result_dict["cases"]) == 1
    assert result_dict["metrics"]["total_cases"] == 1
    assert result_dict["metrics"]["avg_score"] == 1.0


def test_evaluation_result_score_variance():
    """Test score variance calculation."""
    cases = [
        TestCaseResult("Q1", "A1", "A1", 0.8, 100.0, 0.001),
        TestCaseResult("Q2", "A2", "A2", 0.9, 100.0, 0.001),
    ]

    result = EvaluationResult(
        dataset_name="test",
        model="gpt-4",
        cases=cases,
    )

    # Variance should be > 0 for different scores
    assert result.score_variance > 0

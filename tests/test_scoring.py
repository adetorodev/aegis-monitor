"""Tests for scoring implementations."""

import pytest

from aegis.scoring.exact_match import ExactMatchScorer


def test_exact_match_scorer_match():
    """Test exact match scoring when outputs match."""
    scorer = ExactMatchScorer()
    result = scorer.score("hello", "hello")

    assert result.score == 1.0
    assert result.metadata["is_match"] is True


def test_exact_match_scorer_no_match():
    """Test exact match scoring when outputs don't match."""
    scorer = ExactMatchScorer()
    result = scorer.score("hello", "goodbye")

    assert result.score == 0.0
    assert result.metadata["is_match"] is False


def test_exact_match_scorer_case_insensitive():
    """Test case-insensitive matching."""
    scorer = ExactMatchScorer(case_sensitive=False)
    result = scorer.score("Hello", "hello")

    assert result.score == 1.0


def test_exact_match_scorer_case_sensitive():
    """Test case-sensitive matching."""
    scorer = ExactMatchScorer(case_sensitive=True)
    result = scorer.score("Hello", "hello")

    assert result.score == 0.0


def test_exact_match_scorer_whitespace():
    """Test whitespace handling."""
    scorer = ExactMatchScorer(ignore_whitespace=True)
    result = scorer.score("  hello  ", "hello")

    assert result.score == 1.0


def test_exact_match_scorer_no_whitespace_handling():
    """Test with whitespace handling disabled."""
    scorer = ExactMatchScorer(ignore_whitespace=False)
    result = scorer.score("  hello  ", "hello")

    assert result.score == 0.0


def test_exact_match_scorer_deterministic():
    """Test that scorer is deterministic."""
    scorer = ExactMatchScorer()
    assert scorer.is_deterministic() is True


def test_exact_match_scorer_name():
    """Test scorer name."""
    scorer = ExactMatchScorer(name="test_scorer")
    assert scorer.name == "test_scorer"

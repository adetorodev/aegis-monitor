"""Tests for Phase 3 features: semantic, composite scoring, and regression."""

import pytest

from aegis.core.regression import RegressionDetector, RegressionThresholds
from aegis.scoring.composite import CompositeScorer
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.scoring.semantic_similarity import SemanticSimilarityScorer


def test_semantic_similarity_scorer_identical():
    """Identical strings should score near 1.0."""
    scorer = SemanticSimilarityScorer()
    result = scorer.score("Hello world", "Hello world")
    assert result.score == pytest.approx(1.0, abs=0.01)


def test_semantic_similarity_scorer_different():
    """Completely different strings should score low."""
    scorer = SemanticSimilarityScorer()
    result = scorer.score("Hello world", "Quantum physics")
    assert result.score < 0.5


def test_semantic_similarity_scorer_case_insensitive():
    """Case differences should not affect score by default."""
    scorer = SemanticSimilarityScorer(case_sensitive=False)
    result1 = scorer.score("Hello", "hello")
    result2 = scorer.score("HELLO", "hello")
    assert result1.score == pytest.approx(result2.score, abs=0.01)


def test_semantic_similarity_scorer_whitespace_normalization():
    """Whitespace normalization should work."""
    scorer = SemanticSimilarityScorer(normalize_whitespace=True)
    result = scorer.score("hello  world", "hello world")
    assert result.score >= 0.9


def test_composite_scorer_single_scorer():
    """Composite scorer with one member should behave like that scorer."""
    exact_scorer = ExactMatchScorer()
    composite = CompositeScorer(
        scorers={"exact": exact_scorer},
        weights={"exact": 1.0},
    )
    result = composite.score("test", "test")
    assert result.score == 1.0


def test_composite_scorer_weighted_average():
    """Composite should compute correct weighted average."""
    exact_scorer = ExactMatchScorer()
    semantic_scorer = SemanticSimilarityScorer()

    composite = CompositeScorer(
        scorers={"exact": exact_scorer, "semantic": semantic_scorer},
        weights={"exact": 0.5, "semantic": 0.5},
    )

    result = composite.score("test", "test")
    assert 0.9 <= result.score <= 1.0
    assert "components" in result.metadata


def test_composite_scorer_empty_scorers_raises():
    """Empty scorers should raise error."""
    with pytest.raises(ValueError, match="at least one scorer"):
        CompositeScorer(scorers={}, weights={})


def test_composite_scorer_negative_weight_raises():
    """Negative weight should raise error."""
    exact_scorer = ExactMatchScorer()
    with pytest.raises(ValueError, match="must be >= 0"):
        CompositeScorer(
            scorers={"exact": exact_scorer},
            weights={"exact": -0.5},
        )


def test_composite_scorer_missing_weight():
    """Missing weight should be treated as zero and excluded."""
    exact_scorer = ExactMatchScorer()
    semantic_scorer = SemanticSimilarityScorer()

    composite = CompositeScorer(
        scorers={"exact": exact_scorer, "semantic": semantic_scorer},
        weights={"exact": 1.0},  # Only exact has weight
    )

    # Should only use exact scorer
    result = composite.score("test", "test")
    assert result.score == 1.0


def test_regression_detector_no_regression():
    """Detector should pass when metrics don't regress."""
    detector = RegressionDetector(
        thresholds=RegressionThresholds(
            score_drop_pct=5.0,
            cost_increase_pct=10.0,
            latency_increase_pct=15.0,
        )
    )

    baseline = {
        "metrics": {
            "avg_score": 0.90,
            "total_cost": 1.00,
            "avg_latency_ms": 100.0,
        }
    }
    current = {
        "metrics": {
            "avg_score": 0.91,
            "total_cost": 1.05,
            "avg_latency_ms": 105.0,
        }
    }

    analysis = detector.compare(current, baseline)
    assert analysis.status == "pass"


def test_regression_detector_score_drop():
    """Detector should fail on score drop exceeding threshold."""
    detector = RegressionDetector(
        thresholds=RegressionThresholds(score_drop_pct=5.0)
    )

    baseline = {"metrics": {"avg_score": 0.90, "total_cost": 1.0, "avg_latency_ms": 100.0}}
    current = {"metrics": {"avg_score": 0.80, "total_cost": 1.0, "avg_latency_ms": 100.0}}

    analysis = detector.compare(current, baseline)
    assert analysis.status == "fail"
    assert analysis.score_drop_pct > 5.0


def test_regression_detector_cost_warning():
    """Detector should warn on cost increase exceeding threshold."""
    detector = RegressionDetector(
        thresholds=RegressionThresholds(cost_increase_pct=10.0)
    )

    baseline = {"metrics": {"avg_score": 0.90, "total_cost": 1.0, "avg_latency_ms": 100.0}}
    current = {"metrics": {"avg_score": 0.90, "total_cost": 1.20, "avg_latency_ms": 100.0}}

    analysis = detector.compare(current, baseline)
    assert analysis.status == "warning"
    assert analysis.cost_increase_pct > 10.0


def test_regression_detector_latency_warning():
    """Detector should warn on latency increase exceeding threshold."""
    detector = RegressionDetector(
        thresholds=RegressionThresholds(latency_increase_pct=15.0)
    )

    baseline = {"metrics": {"avg_score": 0.90, "total_cost": 1.0, "avg_latency_ms": 100.0}}
    current = {"metrics": {"avg_score": 0.90, "total_cost": 1.0, "avg_latency_ms": 130.0}}

    analysis = detector.compare(current, baseline)
    assert analysis.status == "warning"
    assert analysis.latency_increase_pct > 15.0


def test_regression_detector_to_dict():
    """Regression analysis should serialize to dict."""
    detector = RegressionDetector()
    baseline = {"metrics": {"avg_score": 0.90, "total_cost": 1.0, "avg_latency_ms": 100.0}}
    current = {"metrics": {"avg_score": 0.90, "total_cost": 1.0, "avg_latency_ms": 100.0}}

    analysis = detector.compare(current, baseline)
    result_dict = analysis.to_dict()

    assert "status" in result_dict
    assert "score_drop_pct" in result_dict
    assert "details" in result_dict

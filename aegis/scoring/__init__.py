"""Scoring and evaluation metrics."""

from aegis.scoring.base import BaseScorer, ScoringResult
from aegis.scoring.composite import CompositeScorer
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.scoring.semantic_similarity import SemanticSimilarityScorer

__all__ = [
    "BaseScorer",
    "ScoringResult",
    "ExactMatchScorer",
    "SemanticSimilarityScorer",
    "CompositeScorer",
]

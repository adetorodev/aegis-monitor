"""Semantic similarity scoring implementation."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Optional

from aegis.scoring.base import BaseScorer, ScoringResult


class SemanticSimilarityScorer(BaseScorer):
    """Scorer that estimates semantic similarity between expected and actual text.

    Uses sentence-transformers embeddings when available, and falls back to
    a deterministic lexical similarity score otherwise.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        normalize_whitespace: bool = True,
        case_sensitive: bool = False,
        name: str = "semantic_similarity",
    ) -> None:
        """Initialize semantic similarity scorer."""
        super().__init__(name)
        self.model_name = model_name
        self.normalize_whitespace = normalize_whitespace
        self.case_sensitive = case_sensitive
        self._model: Any = None

    def score(self, expected: str, actual: str, **kwargs: Any) -> ScoringResult:
        """Score semantic similarity between expected and actual output."""
        expected_text = self._normalize_text(expected)
        actual_text = self._normalize_text(actual)

        score, strategy = self._compute_similarity(expected_text, actual_text)
        score = min(max(score, 0.0), 1.0)

        return ScoringResult(
            score=score,
            explanation=f"Semantic similarity ({strategy}): {score:.3f}",
            metadata={
                "strategy": strategy,
                "model_name": self.model_name if strategy == "embedding" else None,
            },
        )

    def _normalize_text(self, text: str) -> str:
        normalized = text
        if self.normalize_whitespace:
            normalized = " ".join(normalized.split())
        if not self.case_sensitive:
            normalized = normalized.lower()
        return normalized

    def _compute_similarity(self, expected: str, actual: str) -> tuple[float, str]:
        if not expected and not actual:
            return 1.0, "lexical"
        if not expected or not actual:
            return 0.0, "lexical"

        embedding_score = self._embedding_similarity(expected, actual)
        if embedding_score is not None:
            return embedding_score, "embedding"

        lexical_score = SequenceMatcher(None, expected, actual).ratio()
        return float(lexical_score), "lexical"

    def _embedding_similarity(self, expected: str, actual: str) -> Optional[float]:
        try:
            if self._model is None:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)

            expected_embedding = self._model.encode(expected)
            actual_embedding = self._model.encode(actual)

            dot_product = float((expected_embedding * actual_embedding).sum())
            expected_norm = float((expected_embedding * expected_embedding).sum()) ** 0.5
            actual_norm = float((actual_embedding * actual_embedding).sum()) ** 0.5
            if expected_norm == 0 or actual_norm == 0:
                return 0.0
            cosine_similarity = dot_product / (expected_norm * actual_norm)
            return (cosine_similarity + 1.0) / 2.0
        except Exception:
            return None

    def is_deterministic(self) -> bool:
        """Semantic scorer is deterministic for same inputs/model versions."""
        return True

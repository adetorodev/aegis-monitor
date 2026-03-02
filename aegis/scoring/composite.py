"""Composite scoring implementation."""

from __future__ import annotations

from typing import Any

from aegis.scoring.base import BaseScorer, ScoringResult


class CompositeScorer(BaseScorer):
    """Combine multiple scorers using weighted averaging."""

    def __init__(
        self,
        scorers: dict[str, BaseScorer],
        weights: dict[str, float],
        name: str = "composite",
    ) -> None:
        """Initialize composite scorer.

        Args:
            scorers: Mapping of scorer name to scorer instance.
            weights: Mapping of scorer name to non-negative weight.
            name: Scorer name.
        """
        super().__init__(name)
        if not scorers:
            raise ValueError("CompositeScorer requires at least one scorer")
        if not weights:
            raise ValueError("CompositeScorer requires at least one weight")

        missing = set(weights.keys()) - set(scorers.keys())
        if missing:
            raise ValueError(f"Weights reference missing scorers: {sorted(missing)}")

        self.scorers = scorers
        self.weights = weights
        self._validate_weights()

    def _validate_weights(self) -> None:
        for scorer_name, weight in self.weights.items():
            if weight < 0:
                raise ValueError(f"Weight for scorer '{scorer_name}' must be >= 0")
        if sum(self.weights.values()) <= 0:
            raise ValueError("CompositeScorer weights must sum to > 0")

    def score(self, expected: str, actual: str, **kwargs: Any) -> ScoringResult:
        """Score by weighted combination of child scorers."""
        weighted_sum = 0.0
        total_weight = 0.0
        components: dict[str, Any] = {}

        for scorer_name, scorer in self.scorers.items():
            weight = float(self.weights.get(scorer_name, 0.0))
            if weight <= 0:
                continue

            result = scorer.score(expected=expected, actual=actual, **kwargs)
            weighted_sum += result.score * weight
            total_weight += weight
            components[scorer_name] = {
                "score": result.score,
                "weight": weight,
                "explanation": result.explanation,
            }

        if total_weight == 0:
            raise ValueError("CompositeScorer has no positive weights for configured scorers")

        score = weighted_sum / total_weight
        return ScoringResult(
            score=score,
            explanation=f"Composite score from {len(components)} scorers",
            metadata={"components": components, "total_weight": total_weight},
        )

    def is_deterministic(self) -> bool:
        """Composite scorer is deterministic if all child scorers are deterministic."""
        return all(scorer.is_deterministic() for scorer in self.scorers.values())

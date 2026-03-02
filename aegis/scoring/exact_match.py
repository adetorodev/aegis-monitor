"""Exact match scoring implementation."""

from typing import Any

from aegis.scoring.base import BaseScorer, ScoringResult


class ExactMatchScorer(BaseScorer):
    """Scorer that checks for exact string match.

    Scores 1.0 if actual exactly matches expected, 0.0 otherwise.
    Optionally case-insensitive and whitespace-insensitive.
    """

    def __init__(
        self,
        case_sensitive: bool = False,
        ignore_whitespace: bool = True,
        name: str = "exact_match",
    ) -> None:
        """Initialize scorer.

        Args:
            case_sensitive: If True, comparison is case-sensitive.
            ignore_whitespace: If True, ignore leading/trailing whitespace.
            name: Scorer name identifier.
        """
        super().__init__(name)
        self.case_sensitive = case_sensitive
        self.ignore_whitespace = ignore_whitespace

    def score(
        self, expected: str, actual: str, **kwargs: Any
    ) -> ScoringResult:
        """Score actual against expected.

        Args:
            expected: Ground truth string.
            actual: Model output string.
            **kwargs: Additional parameters (unused).

        Returns:
            ScoringResult with 0.0 or 1.0.
        """
        exp = expected
        act = actual

        # Apply transformations
        if self.ignore_whitespace:
            exp = exp.strip()
            act = act.strip()

        if not self.case_sensitive:
            exp = exp.lower()
            act = act.lower()

        # Score
        is_match = exp == act
        score = 1.0 if is_match else 0.0

        return ScoringResult(
            score=score,
            explanation=(
                "Exact match" if is_match else "Output does not match expected"
            ),
            metadata={
                "is_match": is_match,
                "case_sensitive": self.case_sensitive,
                "ignore_whitespace": self.ignore_whitespace,
            },
        )

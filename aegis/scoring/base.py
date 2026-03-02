"""Base scoring interface for evaluation metrics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ScoringResult:
    """Result of scoring an evaluation.

    Attributes:
        score: Numeric score, typically normalized to [0.0, 1.0].
        explanation: Optional explanation of the score.
        metadata: Additional scoring details.
    """
    score: float
    explanation: Optional[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        """Validate score is in acceptable range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be in [0.0, 1.0], got {self.score}")
        if self.metadata is None:
            self.metadata = {}


class BaseScorer(ABC):
    """Abstract base class for scoring implementations.

    All scoring strategies must inherit from this class and implement
    the score() method. This enables pluggable evaluation metrics
    (exact match, semantic similarity, LLM judge, etc.).
    """

    def __init__(self, name: str = "") -> None:
        """Initialize the scorer.

        Args:
            name: Optional name/identifier for this scorer.
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def score(
        self, expected: str, actual: str, **kwargs: Any
    ) -> ScoringResult:
        """Score a model output against expected output.

        Args:
            expected: The ground truth / expected output.
            actual: The actual model output to evaluate.
            **kwargs: Additional scorer-specific parameters.

        Returns:
            ScoringResult with numeric score and explanation.
        """
        pass

    def is_deterministic(self) -> bool:
        """Whether this scorer produces deterministic results.

        Some scorers (e.g., LLM judge) may be non-deterministic.
        This allows callers to be aware of variability.

        Returns:
            True if scorer produces same results for same inputs.
        """
        return True

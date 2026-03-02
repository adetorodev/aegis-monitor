"""Evaluation results and metrics."""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
from statistics import mean, stdev


@dataclass
class TestCaseResult:
    """Result of evaluating a single test case.

    Attributes:
        input: The input prompt.
        expected: Expected output.
        actual: Actual model output.
        score: Evaluation score (0-1).
        latency_ms: Time to generate response.
        cost: Monetary cost of this request.
        metadata: Additional result metadata.
    """
    input: str
    expected: str
    actual: str
    score: float
    latency_ms: float
    cost: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Complete evaluation run results.

    Attributes:
        dataset_name: Name of evaluated dataset.
        model: Model used for evaluation.
        cases: Results for each test case.
        run_id: Unique identifier for this run.
        created_at: When the run was created.
        metadata: Run-level metadata.
    """
    dataset_name: str
    model: str
    cases: list[TestCaseResult]
    run_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_cases(self) -> int:
        """Total number of test cases."""
        return len(self.cases)

    @property
    def avg_score(self) -> float:
        """Average score across all cases."""
        if not self.cases:
            return 0.0
        return mean(case.score for case in self.cases)

    @property
    def min_score(self) -> float:
        """Minimum score."""
        if not self.cases:
            return 0.0
        return min(case.score for case in self.cases)

    @property
    def max_score(self) -> float:
        """Maximum score."""
        if not self.cases:
            return 0.0
        return max(case.score for case in self.cases)

    @property
    def score_variance(self) -> float:
        """Score standard deviation."""
        if len(self.cases) < 2:
            return 0.0
        return stdev(case.score for case in self.cases)

    @property
    def total_cost(self) -> float:
        """Total cost for all requests."""
        return sum(case.cost for case in self.cases)

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if not self.cases:
            return 0.0
        return mean(case.latency_ms for case in self.cases)

    @property
    def total_latency_ms(self) -> float:
        """Total cumulative latency."""
        return sum(case.latency_ms for case in self.cases)

    @property
    def passed_cases(self) -> int:
        """Number of cases with score >= 0.8."""
        threshold = 0.8
        return sum(1 for case in self.cases if case.score >= threshold)

    @property
    def pass_rate(self) -> float:
        """Percentage of cases that passed (score >= 0.8)."""
        if not self.cases:
            return 0.0
        return self.passed_cases / self.total_cases

    def summary(self) -> str:
        """Get a text summary of results.

        Returns:
            Formatted summary string.
        """
        return (
            f"Dataset: {self.dataset_name}\n"
            f"Model: {self.model}\n"
            f"Cases: {self.total_cases}\n"
            f"Avg Score: {self.avg_score:.3f}\n"
            f"Pass Rate: {self.pass_rate:.1%}\n"
            f"Total Cost: ${self.total_cost:.4f}\n"
            f"Avg Latency: {self.avg_latency_ms:.1f}ms"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "dataset_name": self.dataset_name,
            "model": self.model,
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat(),
            "cases": [
                {
                    "input": case.input,
                    "expected": case.expected,
                    "actual": case.actual,
                    "score": case.score,
                    "latency_ms": case.latency_ms,
                    "cost": case.cost,
                    "metadata": case.metadata,
                }
                for case in self.cases
            ],
            "metrics": {
                "total_cases": self.total_cases,
                "avg_score": self.avg_score,
                "min_score": self.min_score,
                "max_score": self.max_score,
                "score_variance": self.score_variance,
                "total_cost": self.total_cost,
                "avg_latency_ms": self.avg_latency_ms,
                "pass_rate": self.pass_rate,
            },
            "metadata": self.metadata,
        }

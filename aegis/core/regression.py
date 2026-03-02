"""Regression detection for evaluation runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RegressionThresholds:
    """Threshold configuration for regression checks."""

    score_drop_pct: float = 5.0
    cost_increase_pct: float = 10.0
    latency_increase_pct: float = 15.0


@dataclass
class RegressionAnalysis:
    """Regression analysis result."""

    status: str
    score_drop_pct: float
    cost_increase_pct: float
    latency_increase_pct: float
    details: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "score_drop_pct": self.score_drop_pct,
            "cost_increase_pct": self.cost_increase_pct,
            "latency_increase_pct": self.latency_increase_pct,
            "details": self.details,
        }


class RegressionDetector:
    """Detect regressions by comparing current run to baseline run."""

    def __init__(self, thresholds: Optional[RegressionThresholds] = None) -> None:
        self.thresholds = thresholds or RegressionThresholds()

    def compare(
        self,
        current_run: dict[str, Any],
        baseline_run: dict[str, Any],
    ) -> RegressionAnalysis:
        """Compare run metrics and determine pass/warning/fail status."""
        current_metrics = current_run.get("metrics", {})
        baseline_metrics = baseline_run.get("metrics", {})

        current_score = float(current_metrics.get("avg_score", 0.0) or 0.0)
        baseline_score = float(baseline_metrics.get("avg_score", 0.0) or 0.0)

        current_cost = float(current_metrics.get("total_cost", 0.0) or 0.0)
        baseline_cost = float(baseline_metrics.get("total_cost", 0.0) or 0.0)

        current_latency = float(current_metrics.get("avg_latency_ms", 0.0) or 0.0)
        baseline_latency = float(baseline_metrics.get("avg_latency_ms", 0.0) or 0.0)

        score_drop_pct = _percent_drop(baseline_score, current_score)
        cost_increase_pct = _percent_increase(baseline_cost, current_cost)
        latency_increase_pct = _percent_increase(baseline_latency, current_latency)

        status = "pass"
        details: list[str] = []

        if score_drop_pct > self.thresholds.score_drop_pct:
            status = "fail"
            details.append(
                (
                    f"Score regression: drop {score_drop_pct:.2f}% "
                    f"exceeds threshold {self.thresholds.score_drop_pct:.2f}%"
                )
            )

        if cost_increase_pct > self.thresholds.cost_increase_pct:
            if status != "fail":
                status = "warning"
            details.append(
                (
                    f"Cost increase: {cost_increase_pct:.2f}% "
                    f"exceeds threshold {self.thresholds.cost_increase_pct:.2f}%"
                )
            )

        if latency_increase_pct > self.thresholds.latency_increase_pct:
            if status != "fail":
                status = "warning"
            details.append(
                (
                    f"Latency increase: {latency_increase_pct:.2f}% "
                    f"exceeds threshold {self.thresholds.latency_increase_pct:.2f}%"
                )
            )

        if not details:
            details.append("No regression detected")

        return RegressionAnalysis(
            status=status,
            score_drop_pct=score_drop_pct,
            cost_increase_pct=cost_increase_pct,
            latency_increase_pct=latency_increase_pct,
            details=details,
        )


def _percent_drop(previous: float, current: float) -> float:
    if previous <= 0:
        return 0.0
    if current >= previous:
        return 0.0
    return ((previous - current) / previous) * 100.0


def _percent_increase(previous: float, current: float) -> float:
    if previous <= 0:
        return 0.0
    if current <= previous:
        return 0.0
    return ((current - previous) / previous) * 100.0

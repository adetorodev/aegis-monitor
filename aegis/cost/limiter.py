"""Budget limiting and enforcement."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from aegis.cost.aggregator import CostAggregator

logger = logging.getLogger(__name__)

EnforcementMode = Literal["block", "warn", "log"]


@dataclass
class Budget:
    """Budget configuration."""

    limit: float
    period: str = "month"  # day, week, month
    mode: EnforcementMode = "warn"
    dataset: Optional[str] = None  # None = global budget


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded in block mode."""

    pass


class BudgetLimiter:
    """Enforce budget limits with configurable policies."""

    def __init__(self, aggregator: CostAggregator) -> None:
        """Initialize limiter with cost aggregator."""
        self.aggregator = aggregator
        self.budgets: dict[str, Budget] = {}

    def add_budget(self, name: str, budget: Budget) -> None:
        """Add a named budget constraint."""
        self.budgets[name] = budget

    def check_budget(
        self,
        request_cost: float,
        dataset: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict[str, Any]:
        """Check if request would exceed any budgets.

        Args:
            request_cost: Cost of pending request.
            dataset: Dataset name for feature-specific budgets.
            model: Model name for model-specific budgets.

        Returns:
            Status dict with allowed flag and violations.

        Raises:
            BudgetExceededError: If budget exceeded in block mode.
        """
        violations = []
        warnings = []

        for name, budget in self.budgets.items():
            # Skip dataset-specific budgets if dataset doesn't match
            if budget.dataset and budget.dataset != dataset:
                continue

            current_spend = self._get_period_spend(budget)
            projected_spend = current_spend + request_cost

            if projected_spend > budget.limit:
                violation_info = {
                    "budget_name": name,
                    "limit": budget.limit,
                    "current": current_spend,
                    "projected": projected_spend,
                    "overage": projected_spend - budget.limit,
                    "mode": budget.mode,
                }

                if budget.mode == "block":
                    violations.append(violation_info)
                    msg = (
                        f"Budget '{name}' exceeded: "
                        f"${projected_spend:.4f} > ${budget.limit:.4f}"
                    )
                    logger.error(msg)
                    raise BudgetExceededError(msg)
                elif budget.mode == "warn":
                    warnings.append(violation_info)
                    msg = (
                        f"Budget '{name}' would exceed: "
                        f"${projected_spend:.4f} > ${budget.limit:.4f}"
                    )
                    logger.warning(msg)
                else:  # log
                    msg = (
                        f"Budget '{name}' exceeded (log only): "
                        f"${projected_spend:.4f} > ${budget.limit:.4f}"
                    )
                    logger.info(msg)

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
        }

    def get_budget_status(self, name: Optional[str] = None) -> dict[str, Any]:
        """Get current budget status."""
        if name:
            if name not in self.budgets:
                return {"error": f"Budget '{name}' not found"}
            budget = self.budgets[name]
            current_spend = self._get_period_spend(budget)
            return {
                "name": name,
                "limit": budget.limit,
                "spent": current_spend,
                "remaining": budget.limit - current_spend,
                "utilization": (current_spend / budget.limit * 100.0)
                if budget.limit > 0
                else 0.0,
                "period": budget.period,
                "mode": budget.mode,
            }
        else:
            # Get status for all budgets
            return {
                name: self.get_budget_status(name) for name in self.budgets.keys()
            }

    def _get_period_spend(self, budget: Budget) -> float:
        """Get current spend for budget period."""
        end_date = datetime.now()
        start_date = self._get_period_start(end_date, budget.period)

        if budget.dataset:
            # Get dataset-specific costs
            data = self.aggregator.aggregate_by_dataset(start_date, end_date)
            return data.get("by_dataset", {}).get(budget.dataset, 0.0)
        else:
            # Get total costs
            data = self.aggregator.aggregate_by_period(budget.period, end_date)
            return data.get("total_cost", 0.0)

    def _get_period_start(self, end_date: datetime, period: str) -> datetime:
        """Calculate period start date."""
        if period == "day":
            return end_date - timedelta(days=1)
        elif period == "week":
            return end_date - timedelta(days=7)
        elif period == "month":
            return end_date - timedelta(days=30)
        else:
            return end_date - timedelta(days=7)

    def export_budget_report(self, output_path: str) -> None:
        """Export budget status to file."""
        import json
        from pathlib import Path

        status = self.get_budget_status()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)

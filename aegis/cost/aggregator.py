"""Cost aggregation and analysis."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from aegis.storage.base import BaseStorage


class CostAggregator:
    """Aggregate and analyze costs from evaluation runs."""

    def __init__(self, storage: BaseStorage) -> None:
        """Initialize aggregator with storage backend."""
        self.storage = storage

    def aggregate_by_period(
        self,
        period: str = "week",
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Aggregate costs over a time period.

        Args:
            period: Time period (day, week, month).
            end_date: End date for aggregation (defaults to now).

        Returns:
            Aggregated cost data with breakdowns.
        """
        if end_date is None:
            end_date = datetime.now()

        start_date = self._get_start_date(end_date, period)

        # Get all runs in period (this is a simplified implementation)
        # In production, storage would need efficient time-range queries
        all_runs = self._get_runs_in_period(start_date, end_date)

        return self._aggregate_runs(all_runs, period)

    def aggregate_by_model(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Aggregate costs grouped by model."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        runs = self._get_runs_in_period(start_date, end_date)
        by_model: dict[str, float] = {}
        total_cost = 0.0

        for run in runs:
            model = run.get("model", "unknown")
            cost = float(run.get("metrics", {}).get("total_cost", 0.0) or 0.0)
            by_model[model] = by_model.get(model, 0.0) + cost
            total_cost += cost

        by_model_pct = {
            model: {
                "cost": cost,
                "percentage": (cost / total_cost * 100.0) if total_cost > 0 else 0.0,
            }
            for model, cost in by_model.items()
        }

        return {
            "total_cost": total_cost,
            "by_model": by_model_pct,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    def aggregate_by_dataset(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Aggregate costs grouped by dataset/feature."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        runs = self._get_runs_in_period(start_date, end_date)
        by_dataset: dict[str, float] = {}
        total_cost = 0.0

        for run in runs:
            dataset = run.get("dataset_name", "unknown")
            cost = float(run.get("metrics", {}).get("total_cost", 0.0) or 0.0)
            by_dataset[dataset] = by_dataset.get(dataset, 0.0) + cost
            total_cost += cost

        return {
            "total_cost": total_cost,
            "by_dataset": by_dataset,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    def get_top_cost_drivers(
        self,
        limit: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get top cost drivers (model/dataset combinations)."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        runs = self._get_runs_in_period(start_date, end_date)
        drivers: dict[tuple[str, str], float] = {}

        for run in runs:
            dataset = run.get("dataset_name", "unknown")
            model = run.get("model", "unknown")
            cost = float(run.get("metrics", {}).get("total_cost", 0.0) or 0.0)
            key = (dataset, model)
            drivers[key] = drivers.get(key, 0.0) + cost

        sorted_drivers = sorted(drivers.items(), key=lambda x: x[1], reverse=True)
        return [
            {"dataset": dataset, "model": model, "cost": cost}
            for (dataset, model), cost in sorted_drivers[:limit]
        ]

    def _get_start_date(self, end_date: datetime, period: str) -> datetime:
        """Calculate start date from period."""
        if period == "day":
            return end_date - timedelta(days=1)
        elif period == "week":
            return end_date - timedelta(days=7)
        elif period == "month":
            return end_date - timedelta(days=30)
        else:
            return end_date - timedelta(days=7)

    def _get_runs_in_period(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Get all runs within time period.

        Note: This is a simplified implementation. Production version
        would need efficient time-range queries in storage backend.
        """
        # For SQLite backend, we'd need to add a query method
        # For now, return empty list as placeholder
        return []

    def _aggregate_runs(
        self, runs: list[dict[str, Any]], period: str
    ) -> dict[str, Any]:
        """Aggregate run data into summary."""
        total_cost = 0.0
        run_count = len(runs)
        by_model: dict[str, float] = {}
        by_dataset: dict[str, float] = {}

        for run in runs:
            cost = float(run.get("metrics", {}).get("total_cost", 0.0) or 0.0)
            total_cost += cost

            model = run.get("model", "unknown")
            by_model[model] = by_model.get(model, 0.0) + cost

            dataset = run.get("dataset_name", "unknown")
            by_dataset[dataset] = by_dataset.get(dataset, 0.0) + cost

        return {
            "total_cost": total_cost,
            "run_count": run_count,
            "period": period,
            "by_model": by_model,
            "by_dataset": by_dataset,
        }

    def export_to_csv(
        self, data: dict[str, Any], output_path: str
    ) -> None:
        """Export aggregated data to CSV."""
        import csv
        from pathlib import Path

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Item", "Cost", "Percentage"])

            if "by_model" in data:
                for model, info in data["by_model"].items():
                    if isinstance(info, dict):
                        cost = info.get("cost", 0.0)
                        pct = info.get("percentage", 0.0)
                    else:
                        cost = info
                        pct = 0.0
                    writer.writerow(["Model", model, f"{cost:.4f}", f"{pct:.2f}"])

            if "by_dataset" in data and isinstance(data["by_dataset"], dict):
                for dataset, cost in data["by_dataset"].items():
                    writer.writerow(["Dataset", dataset, f"{cost:.4f}", ""])

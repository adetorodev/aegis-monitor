"""Cost tracking and budget management commands."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from aegis.cost.aggregator import CostAggregator
from aegis.cost.limiter import Budget, BudgetLimiter
from aegis.storage.sqlite_backend import SQLiteBackend

console = Console()


def run_cost(
    action: str,
    period: Optional[str] = None,
    dataset: Optional[str] = None,
    export: Optional[str] = None,
    limit: Optional[float] = None,
    mode: Optional[str] = None,
) -> None:
    """Execute cost command.

    Args:
        action: Action to perform (report, analyze, budget).
        period: Time period (day, week, month).
        dataset: Dataset name for filtering.
        export: Export path for CSV/JSON.
        limit: Budget limit amount.
        mode: Budget enforcement mode (block, warn, log).
    """
    storage = SQLiteBackend("aegis.db")
    aggregator = CostAggregator(storage)

    if action == "report":
        _cost_report(aggregator, period or "week", export)
    elif action == "analyze":
        _cost_analyze(aggregator, period or "week")
    elif action == "budget":
        _cost_budget(aggregator, dataset, limit, mode or "warn")
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)


def _cost_report(
    aggregator: CostAggregator,
    period: str,
    export_path: Optional[str] = None,
) -> None:
    """Display cost report."""
    console.print(f"\n[bold]Cost Report - {period.capitalize()}[/bold]\n")

    # Aggregate by model
    model_data = aggregator.aggregate_by_model()
    total_cost = model_data.get("total_cost", 0.0)

    table = Table(title="Cost by Model")
    table.add_column("Model", style="cyan")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("Percentage", justify="right")

    by_model = model_data.get("by_model", {})
    for model, info in by_model.items():
        if isinstance(info, dict):
            cost = info.get("cost", 0.0)
            pct = info.get("percentage", 0.0)
        else:
            cost = info
            pct = 0.0
        table.add_row(model, f"${cost:.4f}", f"{pct:.1f}%")

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]${total_cost:.4f}[/bold]", "100.0%")

    console.print(table)

    # Dataset breakdown
    dataset_data = aggregator.aggregate_by_dataset()
    by_dataset = dataset_data.get("by_dataset", {})

    if by_dataset:
        console.print()
        table2 = Table(title="Cost by Dataset")
        table2.add_column("Dataset", style="cyan")
        table2.add_column("Cost", justify="right", style="green")

        for dataset, cost in by_dataset.items():
            table2.add_row(dataset, f"${cost:.4f}")

        console.print(table2)

    # Export if requested
    if export_path:
        aggregator.export_to_csv(model_data, export_path)
        console.print(f"\n[green]Report exported to {export_path}[/green]")


def _cost_analyze(aggregator: CostAggregator, period: str) -> None:
    """Analyze cost drivers and trends."""
    console.print(f"\n[bold]Cost Analysis - {period.capitalize()}[/bold]\n")

    # Get top cost drivers
    drivers = aggregator.get_top_cost_drivers(limit=5)

    table = Table(title="Top Cost Drivers")
    table.add_column("Dataset", style="cyan")
    table.add_column("Model", style="blue")
    table.add_column("Cost", justify="right", style="green")

    for driver in drivers:
        dataset = driver.get("dataset", "unknown")
        model = driver.get("model", "unknown")
        cost = driver.get("cost", 0.0)
        table.add_row(dataset, model, f"${cost:.4f}")

    console.print(table)

    # Historical comparison placeholder
    console.print("\n[dim]Historical trend analysis coming soon...[/dim]")


def _cost_budget(
    aggregator: CostAggregator,
    dataset: Optional[str] = None,
    limit: Optional[float] = None,
    mode: str = "warn",
) -> None:
    """Configure and check budget."""
    limiter = BudgetLimiter(aggregator)

    if limit is not None:
        # Set new budget
        budget_name = f"{dataset}_budget" if dataset else "global_budget"
        budget = Budget(
            limit=limit,
            period="month",
            mode=mode,  # type: ignore
            dataset=dataset,
        )
        limiter.add_budget(budget_name, budget)
        console.print(f"[green]Budget '{budget_name}' set: ${limit:.2f}/month ({mode} mode)[/green]")
    else:
        # Show budget status
        console.print("\n[bold]Budget Status[/bold]\n")
        console.print("[dim]No budgets configured. Use --limit to set a budget.[/dim]")
        console.print(
            "\nExample: aegis cost budget --limit 100.0 --mode warn --dataset my_dataset"
        )

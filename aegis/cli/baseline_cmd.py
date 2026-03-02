"""Baseline management command implementation."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from aegis.storage.sqlite_backend import SQLiteBackend

console = Console()


def run_baseline(
    action: str,
    dataset: Optional[str],
    run_id: Optional[str],
) -> None:
    """Execute baseline command.

    Args:
        action: Action (set, show, list).
        dataset: Dataset name.
        run_id: Run ID to set as baseline.
    """
    storage = SQLiteBackend()
    storage.initialize()

    try:
        if action == "set":
            _set_baseline(storage, dataset, run_id)
        elif action == "show":
            _show_baseline(storage, dataset)
        elif action == "list":
            _list_baselines(storage)
        else:
            console.print(
                f"[bold red]Error:[/bold red] Unknown action '{action}'",
                style="red",
            )
            console.print(
                "Valid actions: set, show, list",
                style="dim",
            )
            raise typer.Exit(1)
    finally:
        storage.close()


def _set_baseline(
    storage: SQLiteBackend,
    dataset: Optional[str],
    run_id: Optional[str],
) -> None:
    """Set baseline for dataset."""
    if not dataset:
        console.print(
            "[bold red]Error:[/bold red] --dataset is required for 'set' action",
            style="red",
        )
        raise typer.Exit(1)
    if not run_id:
        console.print(
            "[bold red]Error:[/bold red] --run-id is required for 'set' action",
            style="red",
        )
        raise typer.Exit(1)

    run_data = storage.load_run(run_id)
    if run_data is None:
        console.print(
            f"[bold red]Error:[/bold red] Run ID '{run_id}' not found",
            style="red",
        )
        raise typer.Exit(1)

    storage.save_baseline(dataset, run_data)
    console.print(
        f"[bold green]✓[/bold green] Set baseline for dataset '{dataset}' to run '{run_id}'",
        style="green",
    )


def _show_baseline(storage: SQLiteBackend, dataset: Optional[str]) -> None:
    """Show baseline for dataset."""
    if not dataset:
        console.print(
            "[bold red]Error:[/bold red] --dataset is required for 'show' action",
            style="red",
        )
        raise typer.Exit(1)

    baseline = storage.load_baseline(dataset)
    if baseline is None:
        console.print(
            f"[bold yellow]No baseline set for dataset '{dataset}'[/bold yellow]",
            style="yellow",
        )
        raise typer.Exit(0)

    metrics = baseline.get("metrics", {})
    table = Table(title=f"Baseline for '{dataset}'")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Run ID", baseline.get("run_id", "N/A"))
    table.add_row("Model", baseline.get("model", "N/A"))
    table.add_row("Created At", baseline.get("created_at", "N/A"))
    table.add_row("Avg Score", f"{metrics.get('avg_score', 0.0):.3f}")
    table.add_row("Total Cost", f"${metrics.get('total_cost', 0.0):.4f}")
    table.add_row("Avg Latency", f"{metrics.get('avg_latency_ms', 0.0):.1f}ms")
    table.add_row("Pass Rate", f"{metrics.get('pass_rate', 0.0):.1%}")

    console.print(table)


def _list_baselines(storage: SQLiteBackend) -> None:
    """List all baselines."""
    console.print(
        "[dim]Listing all baselines from storage...[/dim]",
        style="dim",
    )
    console.print(
        "[yellow]list action not yet implemented - use show with --dataset[/yellow]",
        style="yellow",
    )

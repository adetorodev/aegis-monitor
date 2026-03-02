"""Model comparison command."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from aegis.adapters.openai_adapter import OpenAIAdapter
from aegis.adapters.mock_adapter import MockAdapter
from aegis.core.dataset import Dataset
from aegis.core.evaluator import Evaluator
from aegis.scoring.composite import CompositeScorer
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.scoring.semantic_similarity import SemanticSimilarityScorer
from aegis.storage.sqlite_backend import SQLiteBackend

logger = logging.getLogger(__name__)
console = Console()


def _get_adapter(model: str):
    """Get adapter for model name."""
    if model.startswith("gpt-"):
        return OpenAIAdapter(model=model)
    elif model == "mock":
        return MockAdapter()
    else:
        raise ValueError(f"Unknown model: {model}")


def run_compare(
    dataset: str,
    models: str,
    output: str,
    verbose: bool,
    storage_path: str = "aegis.db",
) -> None:
    """Compare multiple models on the same dataset.

    Args:
        dataset: Path to dataset YAML file.
        models: Comma-separated list of models to compare.
        output: Output format (text or json).
        verbose: Enable verbose output.
        storage_path: Path to SQLite database.
    """
    try:
        # Parse models list
        model_list = [m.strip() for m in models.split(",")]

        # Load dataset
        dataset_path = Path(dataset)
        if not dataset_path.exists():
            console.print(f"[red]Dataset not found: {dataset}[/red]")
            raise typer.Exit(1)

        ds = Dataset.load_from_yaml(str(dataset_path))
        console.print(f"[cyan]Dataset loaded: {ds.name} ({len(ds.cases)} cases)[/cyan]")

        # Setup storage and scorer
        storage = SQLiteBackend(storage_path)
        scorer = _get_scorer()

        # Run evaluations for each model
        results: dict[str, Any] = {}
        console.print(f"\n[bold]Running evaluations...[/bold]\n")

        for model in model_list:
            console.print(f"  Testing {model}...", end=" ")

            try:
                adapter = _get_adapter(model)
                evaluator = Evaluator(adapter, scorer, storage)
                eval_result = evaluator.evaluate(ds)

                results[model] = {
                    "score": eval_result.avg_score,
                    "cost": eval_result.total_cost,
                    "latency": eval_result.avg_latency,
                    "passed": eval_result.passed,
                    "case_count": len(eval_result.cases),
                }

                console.print("[green]✓[/green]")

            except Exception as e:
                console.print(f"[red]✗[/red]")
                logger.error(f"Error evaluating {model}: {e}")
                if verbose:
                    console.print(f"  [red]{str(e)}[/red]")
                results[model] = {"error": str(e)}

        # Generate comparison report
        if output == "json":
            _output_json(results)
        else:
            _output_text(results, model_list)

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


def _get_scorer() -> CompositeScorer:
    """Create composite scorer for comparison."""
    scorers = {
        "exact_match": ExactMatchScorer(),
        "semantic": SemanticSimilarityScorer(),
    }
    return CompositeScorer(
        scorers=scorers,
        weights={"exact_match": 0.3, "semantic": 0.7},
    )


def _output_text(results: dict[str, Any], models: list[str]) -> None:
    """Output comparison results as text table.

    Args:
        results: Results dictionary.
        models: List of model names in order.
    """
    console.print("\n[bold]Model Comparison Report[/bold]\n")

    # Validate results
    valid_results = {m: results[m] for m in models if "error" not in results[m]}
    if not valid_results:
        console.print("[red]No valid results to compare[/red]")
        return

    # Calculate CPQ and rankings
    scores_valid = [r for r in valid_results.values() if r.get("cost", 0) > 0]
    if not scores_valid:
        console.print("[yellow]No cost data available[/yellow]")
        return

    # Calculate CPQ: Cost Per Quality (lower is better)
    cpq_data = []
    for model, result in valid_results.items():
        cost = result.get("cost", 0)
        score = result.get("score", 0)

        if cost > 0 and score > 0:
            cpq = cost / score  # Cost per unit of quality
        else:
            cpq = float("inf")

        cpq_data.append((model, cpq, result))

    # Sort by CPQ (ascending = better)
    cpq_data.sort(key=lambda x: x[1] if x[1] != float("inf") else float("inf"))

    # Create comparison table
    table = Table(title="Model Comparison")
    table.add_column("Rank", style="cyan")
    table.add_column("Model", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Cost", justify="right", style="yellow")
    table.add_column("Latency", justify="right", style="blue")
    table.add_column("CPQ", justify="right", style="magenta")

    for rank, (model, cpq, result) in enumerate(cpq_data, 1):
        score = result.get("score", 0)
        cost = result.get("cost", 0)
        latency = result.get("latency", 0)
        cpq_str = f"${cpq:.4f}" if cpq != float("inf") else "N/A"

        table.add_row(
            str(rank),
            model,
            f"{score:.4f}",
            f"${cost:.4f}",
            f"{latency:.2f}s",
            cpq_str,
        )

    console.print(table)

    # Recommendation
    if cpq_data:
        best_model, best_cpq, _ = cpq_data[0]
        console.print(
            f"\n[bold green]Recommendation: [cyan]{best_model}[/cyan] "
            f"(best cost-quality ratio)[/bold green]"
        )

    # Error summary
    errors = {m: r["error"] for m, r in results.items() if "error" in r}
    if errors:
        console.print("\n[yellow]Errors:[/yellow]")
        for model, error in errors.items():
            console.print(f"  {model}: {error}")


def _output_json(results: dict[str, Any]) -> None:
    """Output comparison results as JSON.

    Args:
        results: Results dictionary.
    """
    # Calculate CPQ for JSON output
    for model, result in results.items():
        if "error" not in result:
            cost = result.get("cost", 0)
            score = result.get("score", 0)

            if cost > 0 and score > 0:
                result["cpq"] = cost / score
            else:
                result["cpq"] = None

    console.print_json(data=results)


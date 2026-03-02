"""Evaluation command implementation."""

import os
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aegis.core.dataset import Dataset
from aegis.adapters.base import BaseModelAdapter
from aegis.adapters.mock_adapter import MockAdapter
from aegis.adapters.openai_adapter import OpenAIAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.cost.calculator import CostCalculator
from aegis.cost.pricing_registry import PricingRegistry
from aegis.storage.sqlite_backend import SQLiteBackend
from aegis.core.evaluator import Evaluator
from aegis.core.regression import RegressionDetector


console = Console()


def run_eval(
    dataset_path: str,
    model: str,
    provider: str,
    output_format: str,
    storage_path: str,
    baseline_name: Optional[str],
    config_path: Optional[str],
    verbose: bool,
) -> None:
    """Execute evaluation command.

    Args:
        dataset_path: Path to dataset YAML file.
        model: Model identifier.
        provider: Adapter provider (auto/openai/mock).
        output_format: Output format (text or json).
        storage_path: SQLite database path.
        baseline_name: Optional dataset name for baseline comparison.
        config_path: Optional config file path.
        verbose: Enable verbose logging.
    """
    storage: Optional[SQLiteBackend] = None

    try:
        if output_format not in {"text", "json"}:
            raise ValueError("Output format must be 'text' or 'json'")

        # Load dataset
        console.print(f"[bold blue]Loading dataset:[/bold blue] {dataset_path}")
        dataset = Dataset.from_yaml(dataset_path)
        console.print(f"  ✓ Loaded {len(dataset)} cases from {dataset.name}")

        # Initialize components
        console.print(f"\n[bold blue]Initializing:[/bold blue]")
        console.print(f"  Model: {model}")

        adapter = _resolve_adapter(provider=provider, model=model)
        console.print(f"  ✓ Adapter initialized")

        scorer = ExactMatchScorer()
        console.print(f"  ✓ Scorer initialized")

        pricing_registry = PricingRegistry()
        cost_calculator = CostCalculator(pricing_registry)
        console.print(f"  ✓ Cost engine initialized")

        storage = SQLiteBackend(storage_path)
        storage.initialize()
        console.print(f"  ✓ Storage initialized: {storage_path}")

        # Run evaluation
        console.print(f"\n[bold blue]Running evaluation:[/bold blue]")
        evaluator = Evaluator(adapter, scorer, storage, cost_calculator)
        result = evaluator.run_sync(dataset)

        # Regression detection
        regression_status = "pass"
        regression_analysis = None
        if baseline_name:
            console.print(f"\n[bold blue]Regression Check:[/bold blue]")
            baseline_data = storage.load_baseline(baseline_name)
            if baseline_data is None:
                console.print(
                    f"  [yellow]⚠[/yellow] No baseline found for '{baseline_name}'",
                    style="yellow",
                )
            else:
                detector = RegressionDetector()
                regression_analysis = detector.compare(result.to_dict(), baseline_data)
                regression_status = regression_analysis.status

                if regression_status == "pass":
                    console.print("  [green]✓ No regression detected[/green]")
                elif regression_status == "warning":
                    console.print("  [yellow]⚠ Performance warning[/yellow]")
                    for detail in regression_analysis.details:
                        console.print(f"    • {detail}", style="yellow")
                elif regression_status == "fail":
                    console.print("  [red]✗ Regression detected[/red]")
                    for detail in regression_analysis.details:
                        console.print(f"    • {detail}", style="red")

        # Display results
        console.print(f"\n[bold green]✓ Evaluation Complete[/bold green]\n")

        if output_format == "json":
            import json

            result_dict = result.to_dict()
            if regression_analysis:
                result_dict["regression"] = regression_analysis.to_dict()
            console.print_json(data=result_dict)
        else:
            # Text format
            table = Table(title=f"Evaluation Results: {dataset.name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Dataset", dataset.name)
            table.add_row("Model", model)
            table.add_row("Total Cases", str(result.total_cases))
            table.add_row("Avg Score", f"{result.avg_score:.3f}")
            table.add_row("Min Score", f"{result.min_score:.3f}")
            table.add_row("Max Score", f"{result.max_score:.3f}")
            table.add_row("Pass Rate", f"{result.pass_rate:.1%}")
            table.add_row("Avg Latency", f"{result.avg_latency_ms:.1f}ms")
            table.add_row("Total Cost", f"${result.total_cost:.4f}")
            table.add_row("Run ID", result.run_id)

            console.print(table)

            if verbose:
                console.print("\n[bold blue]Case Details:[/bold blue]")
                case_table = Table()
                case_table.add_column("Case", style="cyan", width=5)
                case_table.add_column("Input", style="dim", width=30)
                case_table.add_column("Score", style="green")
                case_table.add_column("Latency", style="yellow")

                for i, case in enumerate(result.cases):
                    case_table.add_row(
                        str(i + 1),
                        case.input[:30] + "..." if len(case.input) > 30 else case.input,
                        f"{case.score:.2f}",
                        f"{case.latency_ms:.0f}ms",
                    )

                console.print(case_table)

        # Exit with appropriate code for regression checks
        if baseline_name and regression_status == "fail":
            raise typer.Exit(2)  # Distinct exit code for regression failure
        elif result.avg_score < 0.8:
            raise typer.Exit(1)  # Score threshold failure
        else:
            raise typer.Exit(0)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        if verbose:
            import traceback
            console.print(traceback.format_exc(), style="red")
        else:
            console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        raise typer.Exit(1)
    finally:
        if storage is not None:
            storage.close()


def _resolve_adapter(provider: str, model: str) -> BaseModelAdapter:
    """Resolve adapter implementation from provider selection."""
    provider_normalized = provider.lower().strip()

    if provider_normalized == "mock":
        return MockAdapter(model)
    if provider_normalized == "openai":
        return OpenAIAdapter(model)
    if provider_normalized == "auto":
        if os.getenv("OPENAI_API_KEY"):
            return OpenAIAdapter(model)
        return MockAdapter(model)

    raise ValueError(
        f"Unsupported provider '{provider}'. Use one of: auto, openai, mock"
    )

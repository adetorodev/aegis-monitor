"""CLI main entry point."""

import typer
from typing import Optional

app = typer.Typer(
    name="aegis",
    help="LLM evaluation and cost monitoring framework",
    no_args_is_help=True,
)

eval_app = typer.Typer(help="Evaluation commands")
app.add_typer(eval_app, name="eval")


@eval_app.command("run")
def eval_run(
    dataset: str = typer.Option(
        ..., "--dataset", "-d", help="Path to evaluation dataset (YAML)"
    ),
    model: str = typer.Option(
        "gpt-4", "--model", "-m", help="Model to evaluate"
    ),
    provider: str = typer.Option(
        "auto", "--provider", "-p", help="Provider to use: auto, openai, mock"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text or json"
    ),
    storage_path: str = typer.Option(
        "aegis.db", "--storage", "-s", help="Path to SQLite storage database"
    ),
    baseline: Optional[str] = typer.Option(
        None, "--baseline", "-b", help="Compare to baseline for this dataset name"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to config file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
) -> None:
    """Run evaluation on a dataset.

    Example:
        aegis eval run --dataset qa.yaml --model gpt-4
        aegis eval run --dataset qa.yaml --model gpt-4 --baseline qa_production
    """
    from aegis.cli.eval_cmd import run_eval

    run_eval(dataset, model, provider, output, storage_path, baseline, config, verbose)


@app.command("run")
def run_alias(
    dataset: str = typer.Option(
        ..., "--dataset", "-d", help="Path to evaluation dataset (YAML)"
    ),
    model: str = typer.Option(
        "gpt-4", "--model", "-m", help="Model to evaluate"
    ),
    provider: str = typer.Option(
        "auto", "--provider", "-p", help="Provider to use: auto, openai, mock"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text or json"
    ),
    storage_path: str = typer.Option(
        "aegis.db", "--storage", "-s", help="Path to SQLite storage database"
    ),
    baseline: Optional[str] = typer.Option(
        None, "--baseline", "-b", help="Compare to baseline for this dataset name"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to config file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
) -> None:
    """Backward-compatible alias for evaluation run."""
    from aegis.cli.eval_cmd import run_eval

    run_eval(dataset, model, provider, output, storage_path, baseline, config, verbose)


@app.command()
def compare(
    dataset: str = typer.Option(
        ..., "--dataset", "-d", help="Path to evaluation dataset (YAML)"
    ),
    models: str = typer.Option(
        ..., "--models", "-m", help="Comma-separated list of models"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text or json"
    ),
    storage_path: str = typer.Option(
        "aegis.db", "--storage", "-s", help="Path to SQLite storage database"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Verbose output"
    ),
) -> None:
    """Compare multiple models on the same dataset.

    Example:
        aegis compare --dataset qa.yaml --models gpt-4,gpt-3.5-turbo
        aegis compare --dataset qa.yaml --models gpt-4,claude-3-opus
    """
    from aegis.cli.compare_cmd import run_compare

    run_compare(dataset, models, output, verbose, storage_path)


@app.command()
def baseline(
    action: str = typer.Argument(
        ..., help="Action: set, show, or list"
    ),
    dataset: Optional[str] = typer.Option(
        None, "--dataset", "-d", help="Dataset name"
    ),
    run_id: Optional[str] = typer.Option(
        None, "--run-id", "-r", help="Run ID to set as baseline"
    ),
) -> None:
    """Manage baseline comparisons.

    Example:
        aegis baseline set --dataset qa.yaml --run-id abc123
        aegis baseline show --dataset qa.yaml
    """
    from aegis.cli.baseline_cmd import run_baseline

    run_baseline(action, dataset, run_id)


@app.command()
def cost(
    action: str = typer.Argument(
        ..., help="Action: report, analyze, or budget"
    ),
    period: Optional[str] = typer.Option(
        "week", "--period", "-p", help="Time period: day, week, month"
    ),
    dataset: Optional[str] = typer.Option(
        None, "--dataset", "-d", help="Dataset name for filtering/budgets"
    ),
    export: Optional[str] = typer.Option(
        None, "--export", "-e", help="Export path for CSV report"
    ),
    limit: Optional[float] = typer.Option(
        None, "--limit", "-l", help="Budget limit amount (USD)"
    ),
    mode: Optional[str] = typer.Option(
        "warn", "--mode", "-m", help="Budget enforcement mode: block, warn, log"
    ),
) -> None:
    """Cost tracking and analysis.

    Examples:
        aegis cost report --period week
        aegis cost report --period month --export costs.csv
        aegis cost analyze --period week
        aegis cost budget --limit 100.0 --mode warn --dataset my_dataset
    """
    from aegis.cli.cost_cmd import run_cost

    run_cost(action, period, dataset, export, limit, mode)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version",
        is_flag=True,
    )
) -> None:
    """Aegis AI - LLM Evaluation and Cost Monitoring Framework."""
    if version:
        from aegis import __version__
        print(f"Aegis AI version {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()

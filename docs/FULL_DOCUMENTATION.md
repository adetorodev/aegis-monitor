# Full Documentation

This document is the complete high-level reference for Aegis Monitor.

## 1. What Aegis Monitor Solves

Aegis Monitor helps teams evaluate model output quality, monitor costs, compare models, and detect regressions in production-oriented workflows.

## 2. System Modules

### `aegis/core`
- `Dataset`: YAML dataset loading and validation
- `Evaluator`: asynchronous/synchronous execution over test cases
- `EvaluationResult` / `TestCaseResult`: normalized result models

### `aegis/adapters`
- OpenAI, Anthropic, Mock providers
- Unified model interface via `BaseModelAdapter`
- Standardized `ModelResponse`

### `aegis/scoring`
- Exact match scoring
- Semantic similarity scoring
- Composite weighted scoring

### `aegis/cost`
- Pricing registry
- Request-level cost calculator
- Cost aggregation and budget limits

### `aegis/storage`
- SQLite backend for persistent runs/baselines
- Memory backend for tests and ephemeral workflows

### `aegis/cli`
- `eval run` for evaluations
- `compare` for model comparison
- `baseline` for baseline management
- `cost` for reporting and budgeting
- `run` as compatibility alias

## 3. End-to-End Evaluation Flow

1. Load dataset from YAML.
2. Build adapter + scorer (+ optional storage/cost calculator).
3. Execute all test cases with the evaluator.
4. Compute average quality, cost, latency, pass rate.
5. Save run for trend and baseline comparisons.

## 4. CLI Reference

### Evaluate

```bash
aegis eval run \
  --dataset <path.yaml> \
  --model gpt-4 \
  --provider auto \
  --output text \
  --storage aegis.db
```

### Compare

```bash
aegis compare \
  --dataset <path.yaml> \
  --models gpt-4,gpt-3.5-turbo,claude-3-opus \
  --output text
```

### Baseline

```bash
aegis baseline set --dataset <dataset_name> --run-id <run_id>
aegis baseline show --dataset <dataset_name>
aegis baseline list
```

### Cost

```bash
aegis cost report --period week
aegis cost analyze --period month
aegis cost budget --limit 100 --mode warn --dataset <dataset_name>
```

## 5. Python API Reference

### Minimal API usage

```python
from aegis.core.dataset import Dataset
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.core.evaluator import Evaluator

dataset = Dataset.from_yaml("examples/datasets/qa_sample.yaml")
adapter = MockAdapter("mock-model")
scorer = ExactMatchScorer()

evaluator = Evaluator(adapter, scorer)
result = evaluator.run_sync(dataset)
print(result.avg_score, result.total_cost)
```

### Advanced API usage with storage and cost

```python
from aegis.storage.sqlite_backend import SQLiteBackend
from aegis.cost.calculator import CostCalculator

storage = SQLiteBackend("aegis.db")
storage.initialize()
cost_calculator = CostCalculator()

evaluator = Evaluator(adapter, scorer, storage=storage, cost_calculator=cost_calculator)
result = evaluator.run_sync(dataset)
```

## 6. Configuration

### Environment variables

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- optional app-level settings from `.env`

### Dependency groups

- `.[openai]`
- `.[anthropic]`
- `.[scoring]`
- `.[dev]`
- `.[all]`

## 7. Output and Metrics

Typical metrics in run results:
- Average score
- Pass rate
- Total cost
- Average latency
- Per-case metadata (tokens, model, scorer explanation)

Comparison adds:
- CPQ (cost-per-quality)
- Per-model ranking

## 8. Testing and Validation

- Unit tests: adapters/core/scoring/cost/storage
- Integration tests: CLI and evaluation flows
- Coverage reports via pytest-cov

Run all tests:

```bash
pytest -v
```

Run validation utility:

```bash
python validate_project.py
```

## 9. Extension Guide Summary

- Custom adapters: see [ADAPTER_DEVELOPMENT.md](ADAPTER_DEVELOPMENT.md)
- Custom scorers: implement scorer interface
- Custom storage: implement storage base interface

## 10. Security and Operational Notes

- Never commit API keys.
- Use environment variables/secrets manager in CI.
- Prefer mock adapter in tests to avoid accidental external calls.
- Set budget limits for production cost controls.

## 11. Documentation Map

- [Docs Home](README.md)
- [Usage Guide](USAGE.md)
- [Architecture](ARCHITECTURE.md)
- [Adapter Development](ADAPTER_DEVELOPMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [HTML Homepage](index.html)

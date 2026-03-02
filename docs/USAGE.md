# Usage Guide

This guide covers day-to-day use of Aegis AI from install to evaluation workflows.

## 1) Installation

### Base install

```bash
pip install aegis-ai
```

### Development install (from source)

```bash
git clone https://github.com/aegis-ai/aegis-ai
cd aegis-ai
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Optional features

```bash
# OpenAI adapter
pip install -e ".[openai]"

# Anthropic adapter
pip install -e ".[anthropic]"

# Semantic scoring
pip install -e ".[scoring]"

# Everything
pip install -e ".[all]"
```

## 2) Environment Setup

Create `.env` from the template:

```bash
cp .env.example .env
```

Set keys as needed:

```env
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## 3) Dataset Format

Aegis uses YAML datasets.

```yaml
name: qa_sample
description: basic QA checks
cases:
  - input: "What is the capital of France?"
    expected: "Paris"
    tags: ["geography"]
  - input: "What is 2 + 2?"
    expected: "4"
    tags: ["math"]
```

Required fields:
- `name`
- `cases` (array)
- each case needs `input` and `expected`

## 4) CLI Usage

### Evaluate one model

```bash
aegis eval run --dataset examples/datasets/qa_sample.yaml --model gpt-4
```

Options:
- `--provider` (`auto`, `openai`, `mock`)
- `--output` (`text`, `json`)
- `--storage` SQLite file path
- `--baseline` baseline dataset key for regression comparison

### Compare multiple models

```bash
aegis compare \
  --dataset examples/datasets/qa_sample.yaml \
  --models gpt-4,gpt-3.5-turbo,claude-3-opus
```

### Manage baselines

```bash
aegis baseline set --dataset qa_sample --run-id <RUN_ID>
aegis baseline show --dataset qa_sample
aegis baseline list
```

### Cost analysis

```bash
aegis cost report --period week
aegis cost analyze --period month
aegis cost budget --limit 100 --mode warn --dataset qa_sample
```

## 5) Python API Usage

```python
from aegis.core.dataset import Dataset
from aegis.adapters.mock_adapter import MockAdapter
from aegis.scoring.exact_match import ExactMatchScorer
from aegis.core.evaluator import Evaluator

# Load dataset
dataset = Dataset.from_yaml("examples/datasets/qa_sample.yaml")

# Build evaluator
adapter = MockAdapter("mock-model")
scorer = ExactMatchScorer()
evaluator = Evaluator(adapter, scorer)

# Run
result = evaluator.run_sync(dataset)
print(result.avg_score, result.total_cost)
```

## 6) Common Workflows

### Regression gate in CI

1. Run evaluation and save baseline from approved run.
2. Compare new runs to baseline.
3. Fail pipeline on regression threshold.

### Cost-aware model selection

1. Run `aegis compare` on candidate models.
2. Use CPQ (cost-per-quality) ranking from output.
3. Pick model with best quality-cost balance.

## 7) Troubleshooting

### `Unknown model` error
- Ensure model name matches supported adapter prefixes.
- Example: `gpt-*` (OpenAI), `claude-*` (Anthropic), `mock-*` via MockAdapter usage.

### Missing dependency
- Install optional dependency group (for example `.[anthropic]` or `.[scoring]`).

### Empty or invalid dataset
- Validate YAML structure (`name`, `cases`, each case with `input` and `expected`).

## 8) Next Reading

- [Full Documentation](FULL_DOCUMENTATION.md)
- [Architecture](ARCHITECTURE.md)
- [Adapter Development](ADAPTER_DEVELOPMENT.md)

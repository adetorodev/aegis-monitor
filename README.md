# Aegis AI - LLM Evaluation & Cost Governance

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)](#)

**Aegis AI** is an open-source framework for evaluating, comparing, and governing LLM systems. Engineers use Aegis AI to:

- **Evaluate** LLM outputs with pluggable metrics
- **Monitor** costs in real-time and enforce budgets
- **Detect** regressions before deploying to production
- **Compare** models objectively on quality vs. cost
- **Integrate** evaluations into CI/CD pipelines

Built for engineering teams that want reproducible, cost-conscious LLM workflows.

## Quick Start

### Installation

```bash
# Core installation
pip install aegis-ai

# With OpenAI support
pip install "aegis-ai[openai]"

# With Anthropic (Claude) support
pip install "aegis-ai[anthropic]"

# With all providers
pip install "aegis-ai[all]"
```

### 1-Minute Example

**Create a dataset** (`examples/qa.yaml`):

```yaml
name: qa_sample
description: Basic Q&A evaluation
cases:
  - input: "What is the capital of France?"
    expected: "Paris"

  - input: "Explain photosynthesis"
    expected: "Process where plants convert light to energy"
```

**Run evaluation**:

```bash
export OPENAI_API_KEY=your-key-here

aegis eval run \
  --dataset examples/qa.yaml \
  --model gpt-4
```

**Output**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dataset:     qa_sample (2 cases)
Model:       gpt-4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Results:
  Avg Score:      0.92
  Total Cost:     $0.0045
  Avg Latency:    1.2s
  Pass Rate:      2/2

Status: ✓ PASSED
```

## Core Features

### Evaluation Metrics

Evaluate using:

- **Exact Match**: String similarity
- **Semantic Similarity**: Embedding-based comparison
- **Composite**: Multiple metrics with weights

```bash
# Compare models on quality vs cost
aegis compare \
  --dataset examples/qa.yaml \
  --models gpt-4,gpt-3.5-turbo,claude-3-opus
```

### Cost Transparency

Track costs across evaluations:

```bash
# Weekly cost report
aegis cost report --period week

# By-model breakdown
aegis cost report --period month

# Export for analysis
aegis cost report --period month --export costs.csv
```

### Regression Detection

Maintain quality standards:

```bash
# Set baseline
aegis baseline set --dataset qa --run-id abc123

# Compare to baseline
aegis eval run \
  --dataset examples/qa.yaml \
  --model gpt-4 \
  --baseline qa
```

Result: ✓ PASS, ⚠ WARNING, or ✗ FAIL

### Budget Enforcement

Control spending:

```bash
# Set monthly budget
aegis cost budget --limit 500.00 --mode warn

# Per-feature budgets
aegis cost budget \
  --limit 100.00 \
  --dataset summarization \
  --mode block
```

Modes:
- `block`: Raise error if exceeded
- `warn`: Log warning but continue
- `log`: Silent logging only

## Advanced Usage

### Programmatic API

```python
from aegis.core.evaluator import Evaluator
from aegis.adapters.registry import get_adapter
from aegis.scoring.semantic_similarity import SemanticSimilarityScorer
from aegis.core.dataset import Dataset

# Load dataset
dataset = Dataset.load_from_yaml("examples/qa.yaml")

# Create adapter and scorer
adapter = get_adapter("gpt-4")
scorer = SemanticSimilarityScorer()

# Run evaluation
evaluator = Evaluator(adapter, scorer)
results = evaluator.evaluate(dataset)

# Access results
print(f"Average score: {results.avg_score}")
print(f"Total cost: ${results.total_cost:.4f}")
```

### Custom Scorers

Create your own scoring logic:

```python
from aegis.scoring.base import BaseScorer

class CustomScorer(BaseScorer):
    """Custom evaluation metric."""

    name = "custom"

    def score(self, expected: str, actual: str) -> float:
        """Score output (0.0 to 1.0)."""
        # Your logic here
        return 1.0 if expected.lower() == actual.lower() else 0.0

# Use in evaluation
scorer = CustomScorer()
evaluator = Evaluator(adapter, scorer)
results = evaluator.evaluate(dataset)
```

### Custom Adapters

Integrate any LLM provider:

See [ADAPTER_DEVELOPMENT.md](docs/ADAPTER_DEVELOPMENT.md) for complete guide.

```python
from aegis.adapters.base import BaseModelAdapter, ModelResponse

class CustomAdapter(BaseModelAdapter):
    """Adapter for custom LLM service."""

    async def call(self, prompt: str, **kwargs) -> ModelResponse:
        # Call your model
        response = await self._call_api(prompt)

        return ModelResponse(
            text=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=response.latency_ms,
            model=self.model,
        )

    def validate_connection(self) -> bool:
        # Test API
        return True

    def get_model_info(self) -> dict:
        return {
            "model": self.model,
            "provider": "custom",
            "pricing": {"input": 0.01, "output": 0.05},
        }

# Register in aegis/adapters/registry.py
```

## CLI Reference

### Evaluation

```bash
# Run single model
aegis eval run \
  --dataset <path> \
  --model <model-name> \
  --provider <auto|openai|anthropic|mock> \
  --output <text|json> \
  --baseline <name>

# Compare models
aegis compare \
  --dataset <path> \
  --models <model1,model2,...>
```

### Baselines

```bash
# Set baseline
aegis baseline set \
  --dataset <name> \
  --run-id <id>

# Show baseline
aegis baseline show --dataset <name>

# List baselines
aegis baseline list
```

### Cost Intelligence

```bash
# Cost report
aegis cost report \
  --period <day|week|month] \
  --export <file.csv>

# Cost analysis
aegis cost analyze --period week

# Budget management
aegis cost budget \
  --limit <amount> \
  --mode <block|warn|log> \
  --dataset <optional>
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│         CLI (typer)                             │
│  ├─ eval: Run evaluation on dataset             │
│  ├─ compare: Multi-model comparison             │
│  ├─ baseline: Manage baseline comparisons       │
│  └─ cost: Cost tracking and budgets             │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│  Core Orchestration (Evaluator)                 │
│  ├─ Loads dataset                               │
│  ├─ Calls LLM adapter                           │
│  ├─ Scores outputs                              │
│  ├─ Calculates costs                            │
│  └─ Detects regressions                         │
└────────────┬────────────────────────────────────┘
             │
     ┌───────┴───────┬──────────┬──────────┐
     │               │          │          │
┌────▼──────┐  ┌────▼──────┐ ┌─▼──────┐ ┌─▼────────┐
│ Adapters  │  │  Scorers  │ │ Cost   │ │ Storage  │
├───────────┤  ├───────────┤ ├────────┤ ├──────────┤
│ OpenAI    │  │ Exact     │ │ Calc   │ │ SQLite   │
│ Anthropic │  │ Semantic  │ │ Budget │ │ Aggregate│
│ Custom    │  │ Composite │ │ Report │ │ Export   │
└───────────┘  └───────────┘ └────────┘ └──────────┘
```

## Dataset Format

YAML datasets define test cases:

```yaml
name: my_dataset
description: "My evaluation dataset"

# Individual test cases
cases:
  - input: "User question here"
    expected: "Expected answer"
    tags: [feature-1, easy]

  - input: "Another question"
    expected: "Another answer"
    tags: [feature-2, hard]

# Scoring configuration
scoring:
  type: composite
  weights:
    exact_match: 0.3
    semantic_similarity: 0.7

# Optional thresholds for pass/fail
thresholds:
  pass: 0.8
  warning: 0.7
```

## Examples

### Example 1: Q&A Evaluation

```bash
# Evaluate Q&A model
aegis eval run \
  --dataset examples/qa_sample.yaml \
  --model gpt-4

# Compare models
aegis compare \
  --dataset examples/qa_sample.yaml \
  --models gpt-4,gpt-3.5-turbo
```

See: [examples/simple_eval.py](examples/simple_eval.py)

### Example 2: Cost Tracking

```bash
# Track costs over time
aegis eval run \
  --dataset examples/qa_sample.yaml \
  --model gpt-4

# View cost report
aegis cost report --period week

# Set budgets
aegis cost budget --limit 100.0 --mode warn
```

See: [examples/cost_tracking_demo.py](examples/cost_tracking_demo.py)

### Example 3: Model Comparison

```bash
# Compare multiple models
aegis compare \
  --dataset examples/qa_sample.yaml \
  --models gpt-4,claude-3-opus,gpt-3.5-turbo

# See cost-per-quality rankings
```

See: [examples/model_compare.py](examples/model_compare.py)

### Example 4: CI/CD Integration

```yaml
# .github/workflows/llm-test.yml
name: LLM Tests

on: [push, pull_request]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Aegis AI
        run: pip install aegis-ai[openai]

      - name: Run Evaluations
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          aegis eval run \
            --dataset tests/evaluation.yaml \
            --model gpt-4 \
            --baseline production \
            --output json > results.json

      - name: Check Costs
        run: |
          aegis cost report --period day

      - name: Fail on Regression
        run: |
          # Custom logic to fail if regression detected
          python scripts/check_regression.py results.json
```

## Configuration

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY=sk-...

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Aegis AI
export AEGIS_STORAGE=./aegis.db
export AEGIS_LOG_LEVEL=INFO
```

### Configuration File

Create `aegis.yaml`:

```yaml
models:
  gpt-4:
    provider: openai
    temperature: 0.7
    max_tokens: 1000

  claude-3-opus:
    provider: anthropic
    temperature: 0.7

storage:
  backend: sqlite
  path: ./aegis.db

thresholds:
  score_drop_pct: 5
  cost_increase_pct: 10

budget:
  monthly_limit: 1000.0
  enforcement: warn
```

## Performance

* **Per-evaluation latency**: ~2-5 seconds (depends on model)
* **Storage**: SQLite, minimal overhead
* **Memory**: ~50MB for typical datasets
* **Cost calculation**: Real-time per request

## Testing

Run the test suite:

```bash
# All tests
pytest

# Specific module
pytest tests/test_evaluator.py -v

# With coverage
pytest --cov=aegis --cov-report=html

# Integration tests
pytest tests/integration/ -v
```

Tests use mock LLM responses, no real API calls required.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas for contribution:
- New adapter implementations
- Custom scoring metrics
- Documentation improvements
- Example projects
- Bug fixes

## Support

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/username/aegis-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/aegis-ai/discussions)

## Roadmap

**✅ Complete **
- Foundation, first integration, intelligence layer, cost engine
- Model comparison, Anthropic adapter
- Hardening, 80%+ coverage, comprehensive docs

**Future**
- Web dashboard
- Real-time monitoring
- Advanced analytics
- SaaS hosting

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Pydantic](https://pydantic-settings.readthedocs.io/) - Data validation
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [sentence-transformers](https://www.sbert.net/) - Sentence embeddings

---

**Questions?** Open an issue or discussion on [GitHub](https://github.com/yourusername/aegis-ai).

**Ready to get started?** See [Quick Start](#quick-start) above.

Made with ❤️ for the AI engineering community.

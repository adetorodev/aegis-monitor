# Aegis AI Documentation

Welcome to the Aegis AI documentation portal.

## Start Here

- [Usage Guide](USAGE.html) — installation, dataset format, CLI, Python API
- [Full Documentation](FULL_DOCUMENTATION.html) — complete reference and architecture overview
- [Architecture](ARCHITECTURE.html) — system design and component interactions
- [Adapter Development](ADAPTER_DEVELOPMENT.html) — build custom providers/adapters
- [Contributing Guide](CONTRIBUTING.html) — how to contribute code and docs
- [Code of Conduct](CODE_OF_CONDUCT.html) — community standards

## HTML Homepage

Open [Documentation Home](index.html) in your browser for a visual, clickable docs landing page.
Open [Docs Index (HTML)](README.html) for rendered documentation pages.

## Examples

- [Sentiment Classification Example](../examples/sentiment_classification.py)
- [QA Evaluation Example](../examples/qa_evaluation.py)
- [Custom Adapter Example](../examples/custom_adapter.py)
- [Simple Evaluation Example](../examples/simple_eval.py)

## Quick CLI Commands

```bash
# Evaluate one model
aegis eval run --dataset examples/datasets/qa_sample.yaml --model gpt-4

# Compare multiple models
aegis compare --dataset examples/datasets/qa_sample.yaml --models gpt-4,gpt-3.5-turbo

# Baselines
aegis baseline set --dataset qa_sample --run-id <RUN_ID>
aegis baseline show --dataset qa_sample

# Cost reporting
aegis cost report --period week
```

.PHONY: help install install-dev test lint typecheck format clean run-example

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev,openai,anthropic,scoring]"

test: ## Run tests with coverage
	pytest -v

test-fast: ## Run tests without coverage
	pytest -v --no-cov

coverage: ## Generate coverage report
	pytest --cov=aegis --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint: ## Run code linting
	ruff check aegis/ tests/

lint-fix: ## Run linting with auto-fix
	ruff check --fix aegis/ tests/

format: ## Format code with black
	black aegis/ tests/

typecheck: ## Run type checking
	mypy aegis/

check: lint typecheck test ## Run all checks (lint, typecheck, test)

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-db: ## Clean database files
	rm -f aegis.db
	rm -f *.sqlite
	rm -f *.sqlite3

run-example: ## Run simple evaluation example
	python examples/simple_eval.py

cli-help: ## Show CLI help
	aegis --help

build: ## Build package
	python -m build

.DEFAULT_GOAL := help

# Contributing Guide

Thanks for contributing to Aegis Monitor.

## Ways to Contribute

- Bug reports and issue triage
- New adapters and scoring methods
- Test improvements and coverage
- Docs fixes and examples
- Performance and reliability improvements

## Development Setup

```bash
git clone https://github.com/aegis-ai/aegis-ai
cd aegis-ai
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before You Start

1. Open an issue (or comment on an existing one).
2. Describe scope and expected behavior.
3. Keep PRs focused and small when possible.

## Branching and Commits

- Create a feature branch from `main`.
- Use clear commit messages.
- Keep each commit logically scoped.

Suggested commit style:

```text
feat: add adapter timeout retry support
fix: correct cost aggregation for empty runs
docs: expand usage guide for compare command
test: add integration tests for baseline command
```

## Code Standards

- Python >= 3.10
- Use type hints for public interfaces
- Prefer simple, explicit logic over cleverness
- Preserve existing patterns in this repository
- Add/update tests with behavioral changes

## Quality Checks

Run these locally before opening a PR:

```bash
pytest -v
ruff check .
black --check .
mypy aegis --ignore-missing-imports
```

If needed, format code:

```bash
black .
ruff check . --fix
```

## Testing Expectations

- Add unit tests for new logic.
- Add integration tests when changing command flows.
- Do not break existing test behavior.
- Prefer deterministic tests (avoid live external API calls).

## Documentation Expectations

Update docs when changing:
- CLI flags or command behavior
- Adapter interfaces
- Dataset schema
- Cost/scoring output semantics

Relevant docs are in `/docs`.

## Pull Request Checklist

- [ ] Scope is clear and matches linked issue
- [ ] Code is formatted and linted
- [ ] Tests added/updated and passing
- [ ] Docs updated where needed
- [ ] No secrets or credentials committed
- [ ] PR description explains what changed and why

## Review and Merge Process

1. Automated checks must pass.
2. At least one maintainer review.
3. Address feedback with focused updates.
4. Squash/merge according to maintainer preference.

## Reporting Bugs

Include:
- Environment (OS, Python version)
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs/error trace
- Minimal repro dataset or command

## Security Issues

Do not open public issues for sensitive vulnerabilities.
Contact maintainers privately through repository security channels.

## License

By contributing, you agree that your contributions are licensed under the project’s MIT license.

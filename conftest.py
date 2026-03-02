"""Pytest configuration."""

import pytest
import asyncio
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_dataset_yaml(tmp_path: Path) -> Path:
    """Create a sample dataset YAML file for testing.

    Args:
        tmp_path: Temporary directory.

    Returns:
        Path to created YAML file.
    """
    yaml_content = """
name: test_dataset
description: Test dataset
cases:
  - input: "What is 2+2?"
    expected: "4"
    tags: [math, easy]
  - input: "Explain quantum mechanics"
    expected: "QM is a fundamental theory"
    tags: [science, hard]
scoring:
  type: exact_match
  case_sensitive: false
"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)
    return yaml_file

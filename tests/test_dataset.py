"""Tests for dataset loading and management."""

import pytest
from pathlib import Path

from aegis.core.dataset import Dataset, TestCase


def test_test_case_creation():
    """Test creating a test case."""
    case = TestCase(
        input="Hello?",
        expected="Hi",
        tags=["greeting"],
    )
    assert case.input == "Hello?"
    assert case.expected == "Hi"
    assert "greeting" in case.tags


def test_dataset_creation():
    """Test creating a dataset."""
    cases = [
        TestCase(input="Q1", expected="A1"),
        TestCase(input="Q2", expected="A2"),
    ]
    dataset = Dataset(name="test", cases=cases, description="Test dataset")

    assert dataset.name == "test"
    assert len(dataset) == 2
    assert dataset.description == "Test dataset"


def test_dataset_from_yaml(sample_dataset_yaml: Path):
    """Test loading dataset from YAML file.

    Args:
        sample_dataset_yaml: Path to sample YAML file.
    """
    dataset = Dataset.from_yaml(sample_dataset_yaml)

    assert dataset.name == "test_dataset"
    assert len(dataset) == 2
    assert dataset.cases[0].input == "What is 2+2?"
    assert dataset.cases[0].expected == "4"


def test_dataset_from_yaml_not_found():
    """Test loading non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        Dataset.from_yaml("/nonexistent/path.yaml")


def test_dataset_from_yaml_missing_cases(tmp_path: Path):
    """Dataset must include cases list."""
    dataset_file = tmp_path / "invalid.yaml"
    dataset_file.write_text("name: missing_cases\n", encoding="utf-8")

    with pytest.raises(ValueError, match="cases"):
        Dataset.from_yaml(dataset_file)


def test_dataset_from_yaml_invalid_case_schema(tmp_path: Path):
    """Each case must include input and expected strings."""
    dataset_file = tmp_path / "invalid_case.yaml"
    dataset_file.write_text(
        """
name: invalid
cases:
  - input: 123
    expected: ok
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        Dataset.from_yaml(dataset_file)


def test_dataset_to_yaml(tmp_path: Path):
    """Test saving dataset to YAML file.

    Args:
        tmp_path: Temporary directory.
    """
    cases = [TestCase(input="Q1", expected="A1", tags=["easy"])]
    dataset = Dataset(
        name="test",
        cases=cases,
        description="Test dataset",
    )

    yaml_path = tmp_path / "output.yaml"
    dataset.to_yaml(yaml_path)

    # Load it back
    loaded = Dataset.from_yaml(yaml_path)
    assert loaded.name == "test"
    assert len(loaded) == 1
    assert loaded.cases[0].input == "Q1"


def test_dataset_filter_by_tag():
    """Test filtering dataset by tag."""
    cases = [
        TestCase(input="Q1", expected="A1", tags=["easy"]),
        TestCase(input="Q2", expected="A2", tags=["hard"]),
        TestCase(input="Q3", expected="A3", tags=["easy", "math"]),
    ]
    dataset = Dataset(name="test", cases=cases)

    easy_dataset = dataset.filter_by_tag("easy")
    assert len(easy_dataset) == 2
    assert easy_dataset.cases[0].input == "Q1"

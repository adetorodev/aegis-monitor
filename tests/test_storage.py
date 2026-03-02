"""Tests for storage backends."""

import pytest
from datetime import datetime

from aegis.storage.memory_backend import InMemoryStorage


def test_memory_storage_initialize():
    """Test storage initialization."""
    storage = InMemoryStorage()
    storage.initialize()
    assert storage.initialized is True


def test_memory_storage_save_run():
    """Test saving evaluation run."""
    storage = InMemoryStorage()
    storage.initialize()

    run_data = {
        "dataset": "test",
        "score": 0.85,
        "cases": [],
    }

    storage.save_run(run_data, "run-123")
    assert storage.load_run("run-123") is not None


def test_memory_storage_load_run():
    """Test loading evaluation run."""
    storage = InMemoryStorage()
    storage.initialize()

    run_data = {"score": 0.85}
    storage.save_run(run_data, "run-123")

    loaded = storage.load_run("run-123")
    assert loaded["score"] == 0.85


def test_memory_storage_load_run_not_found():
    """Test loading non-existent run."""
    storage = InMemoryStorage()
    storage.initialize()

    loaded = storage.load_run("nonexistent")
    assert loaded is None


def test_memory_storage_save_baseline():
    """Test saving baseline."""
    storage = InMemoryStorage()
    storage.initialize()

    baseline_data = {"score": 0.90}
    storage.save_baseline("qa_dataset", baseline_data)

    loaded = storage.load_baseline("qa_dataset")
    assert loaded["score"] == 0.90


def test_memory_storage_load_baseline_not_found():
    """Test loading non-existent baseline."""
    storage = InMemoryStorage()
    storage.initialize()

    loaded = storage.load_baseline("nonexistent")
    assert loaded is None


def test_memory_storage_clear():
    """Test clearing storage."""
    storage = InMemoryStorage()
    storage.initialize()

    storage.save_run({"score": 0.85}, "run-1")
    storage.save_baseline("ds", {"score": 0.90})

    storage.clear()

    assert storage.load_run("run-1") is None
    assert storage.load_baseline("ds") is None


def test_memory_storage_multiple_runs():
    """Test storing multiple runs."""
    storage = InMemoryStorage()
    storage.initialize()

    for i in range(5):
        storage.save_run({"score": 0.80 + i * 0.01}, f"run-{i}")

    # Should be able to load all
    for i in range(5):
        loaded = storage.load_run(f"run-{i}")
        assert loaded is not None
        assert loaded["score"] == 0.80 + i * 0.01

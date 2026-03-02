"""Tests for SQLite storage backend."""

from pathlib import Path

from aegis.storage.sqlite_backend import SQLiteBackend


def test_sqlite_storage_save_and_load_run(tmp_path: Path) -> None:
    """Run data should persist and be retrievable by run_id."""
    db_path = tmp_path / "aegis_test.db"
    storage = SQLiteBackend(db_path)
    storage.initialize()

    run_data = {
        "dataset_name": "qa_sample",
        "model": "gpt-4",
        "run_id": "run-1",
        "created_at": "2026-03-02T00:00:00",
        "cases": [],
        "metrics": {"avg_score": 1.0},
    }
    storage.save_run(run_data, "run-1")

    loaded = storage.load_run("run-1")
    assert loaded is not None
    assert loaded["dataset_name"] == "qa_sample"
    assert loaded["model"] == "gpt-4"

    storage.close()


def test_sqlite_storage_load_run_not_found(tmp_path: Path) -> None:
    """Missing run lookup should return None."""
    storage = SQLiteBackend(tmp_path / "aegis_test.db")
    storage.initialize()

    assert storage.load_run("missing") is None
    storage.close()


def test_sqlite_storage_save_and_load_baseline(tmp_path: Path) -> None:
    """Baseline data should persist per dataset name."""
    storage = SQLiteBackend(tmp_path / "aegis_test.db")
    storage.initialize()

    baseline_data = {
        "dataset_name": "qa_sample",
        "model": "gpt-4",
        "run_id": "baseline-1",
        "created_at": "2026-03-02T00:00:00",
        "cases": [],
    }

    storage.save_baseline("qa_sample", baseline_data)
    loaded = storage.load_baseline("qa_sample")

    assert loaded is not None
    assert loaded["run_id"] == "baseline-1"
    assert loaded["dataset_name"] == "qa_sample"

    storage.close()

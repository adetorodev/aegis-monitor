"""In-memory storage backend for testing."""

from typing import Any, Optional
from datetime import datetime

from aegis.storage.base import BaseStorage, StorageMetadata


class InMemoryStorage(BaseStorage):
    """Simple in-memory storage backend for testing.

    Stores all data in memory. Useful for testing and development.
    Not suitable for production use.
    """

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._runs: dict[str, dict[str, Any]] = {}
        self._baselines: dict[str, dict[str, Any]] = {}
        self.initialized = False

    def initialize(self) -> None:
        """Initialize storage (no-op for memory backend)."""
        self.initialized = True

    def save_run(self, run_data: dict[str, Any], run_id: str) -> None:
        """Save evaluation run to memory.

        Args:
            run_data: Run data dictionary.
            run_id: Unique run identifier.
        """
        self._runs[run_id] = {
            **run_data,
            "_metadata": {
                "created_at": datetime.now().isoformat(),
                "run_id": run_id,
            },
        }

    def load_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Load evaluation run from memory.

        Args:
            run_id: Unique run identifier.

        Returns:
            Run data if found, None otherwise.
        """
        return self._runs.get(run_id)

    def load_baseline(self, dataset_name: str) -> Optional[dict[str, Any]]:
        """Load baseline for dataset.

        Args:
            dataset_name: Name of dataset.

        Returns:
            Baseline run data if set, None otherwise.
        """
        return self._baselines.get(dataset_name)

    def save_baseline(
        self, dataset_name: str, run_data: dict[str, Any]
    ) -> None:
        """Save baseline for dataset.

        Args:
            dataset_name: Name of dataset.
            run_data: Run to set as baseline.
        """
        self._baselines[dataset_name] = {
            **run_data,
            "_metadata": {
                "created_at": datetime.now().isoformat(),
                "baseline_for": dataset_name,
            },
        }

    def close(self) -> None:
        """Close storage (no-op for memory backend)."""
        pass

    def clear(self) -> None:
        """Clear all data (useful for testing)."""
        self._runs.clear()
        self._baselines.clear()

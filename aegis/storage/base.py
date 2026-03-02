"""Storage backend abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime


@dataclass
class StorageMetadata:
    """Metadata for storage operations."""
    created_at: datetime
    updated_at: datetime
    run_id: str


class BaseStorage(ABC):
    """Abstract base class for storage backends.

    Enables different storage implementations (SQLite, PostgreSQL, Cloud)
    without coupling the core evaluation logic to a specific backend.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize storage (create tables, connections, etc).

        Raises:
            Exception: If initialization fails.
        """
        pass

    @abstractmethod
    def save_run(self, run_data: dict[str, Any], run_id: str) -> None:
        """Save an evaluation run.

        Args:
            run_data: Complete evaluation run data.
            run_id: Unique identifier for this run.

        Raises:
            Exception: If save fails.
        """
        pass

    @abstractmethod
    def load_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Load a previously saved evaluation run.

        Args:
            run_id: Unique identifier of the run to load.

        Returns:
            Run data if found, None otherwise.
        """
        pass

    @abstractmethod
    def load_baseline(self, dataset_name: str) -> Optional[dict[str, Any]]:
        """Load baseline (reference) evaluation results.

        Args:
            dataset_name: Name of the dataset to get baseline for.

        Returns:
            Baseline run data if found, None otherwise.
        """
        pass

    @abstractmethod
    def save_baseline(
        self, dataset_name: str, run_data: dict[str, Any]
    ) -> None:
        """Save baseline evaluation results.

        Args:
            dataset_name: Name of the dataset.
            run_data: The run to set as baseline.

        Raises:
            Exception: If save fails.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close storage connections."""
        pass

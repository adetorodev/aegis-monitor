"""SQLite storage backend."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from aegis.storage.base import BaseStorage


class SQLiteBackend(BaseStorage):
    """SQLite backend for persisting evaluation runs and baselines."""

    def __init__(self, db_path: str | Path = "aegis.db") -> None:
        """Initialize backend with database path."""
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Return active SQLite connection."""
        if self._connection is None:
            raise RuntimeError("SQLite backend is not initialized")
        return self._connection

    def initialize(self) -> None:
        """Create database and required schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(str(self.db_path))
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                dataset_name TEXT,
                model TEXT,
                created_at TEXT,
                run_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS baselines (
                dataset_name TEXT PRIMARY KEY,
                run_id TEXT,
                updated_at TEXT NOT NULL,
                run_json TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def save_run(self, run_data: dict[str, Any], run_id: str) -> None:
        """Save or update an evaluation run."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO runs (run_id, dataset_name, model, created_at, run_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                run_data.get("dataset_name"),
                run_data.get("model"),
                run_data.get("created_at"),
                json.dumps(run_data),
            ),
        )
        self.connection.commit()

    def load_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Load evaluation run by run_id."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT run_json FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def load_baseline(self, dataset_name: str) -> Optional[dict[str, Any]]:
        """Load baseline run for dataset."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT run_json FROM baselines WHERE dataset_name = ?",
            (dataset_name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def save_baseline(self, dataset_name: str, run_data: dict[str, Any]) -> None:
        """Save or update baseline run for dataset."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO baselines (dataset_name, run_id, updated_at, run_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                dataset_name,
                run_data.get("run_id"),
                datetime.now().isoformat(),
                json.dumps(run_data),
            ),
        )
        self.connection.commit()

    def close(self) -> None:
        """Close connection if open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

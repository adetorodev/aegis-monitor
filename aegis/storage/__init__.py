"""Storage backends for evaluation results."""

from aegis.storage.base import BaseStorage
from aegis.storage.sqlite_backend import SQLiteBackend

__all__ = ["BaseStorage", "SQLiteBackend"]

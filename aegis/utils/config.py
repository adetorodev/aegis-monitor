"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Optional
import yaml
from dotenv import load_dotenv


class Config:
    """Application configuration manager.

    Loads configuration from multiple sources with precedence:
    1. Environment variables
    2. YAML config file
    3. Defaults
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration.

        Args:
            config_path: Optional path to config YAML file.
        """
        # Load environment variables
        load_dotenv()

        self._config: dict[str, Any] = {}
        self._load_defaults()

        if config_path:
            self._load_yaml(config_path)

    def _load_defaults(self) -> None:
        """Load default configuration."""
        self._config = {
            "log_level": "INFO",
            "database": "aegis.db",
            "mock_mode": False,
            "enable_cost_tracking": True,
            "enable_regression_detection": True,
        }

    def _load_yaml(self, path: str) -> None:
        """Load configuration from YAML file.

        Args:
            path: Path to YAML file.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If YAML is invalid.
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path, "r") as f:
            yaml_config = yaml.safe_load(f) or {}

        self._config.update(yaml_config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Checks environment variables first, then config dict.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value.
        """
        # Check environment variable first
        env_key = f"AEGIS_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Try to parse as boolean
            if env_value.lower() in ("true", "false"):
                return env_value.lower() == "true"
            return env_value

        # Check config dict
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dict syntax.

        Args:
            key: Configuration key.

        Returns:
            Configuration value.

        Raises:
            KeyError: If key not found.
        """
        value = self.get(key)
        if value is None:
            raise KeyError(f"Configuration key not found: {key}")
        return value


def get_config(config_path: Optional[str] = None) -> Config:
    """Get configuration instance.

    Args:
        config_path: Optional path to config YAML file.

    Returns:
        Configuration instance.
    """
    return Config(config_path)

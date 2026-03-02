"""Constants and enumerations."""

from enum import Enum


class ScoreThreshold(float, Enum):
    """Standard score thresholds."""
    FAIL = 0.5
    POOR = 0.6
    FAIR = 0.7
    GOOD = 0.8
    EXCELLENT = 0.9


class OutputFormat(str, Enum):
    """Supported output formats."""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class RegressionLevel(str, Enum):
    """Regression detection severity levels."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


# Standard cost tracking tags
COST_TAGS = {
    "model": "which_model",
    "feature": "which_feature",
    "user": "user_id",
    "session": "session_id",
    "environment": "prod|staging|dev",
}

# Default pricing for common models (in USD per 1k tokens)
DEFAULT_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
}

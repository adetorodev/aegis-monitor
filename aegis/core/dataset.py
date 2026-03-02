"""Dataset and test case management."""

from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path
import yaml


@dataclass
class TestCase:
    """A single test case in an evaluation dataset.

    Attributes:
        input: The prompt/input to send to the model.
        expected: Ground truth output to compare against.
        tags: Optional tags for categorizing the test case.
        metadata: Additional test case metadata.
    """
    input: str
    expected: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Dataset:
    """Collection of test cases for evaluation.

    Attributes:
        name: Identifier for this dataset.
        description: Human-readable description.
        cases: List of test cases.
        metadata: Dataset-level metadata.
        scoring_config: Scoring strategy configuration.
    """
    name: str
    cases: list[TestCase]
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    scoring_config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Dataset":
        """Load dataset from YAML file.

        Args:
            path: Path to YAML file.

        Returns:
            Loaded Dataset instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If YAML is invalid.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cls._validate_dataset_dict(data)

        cases = []
        for case_data in data.get("cases", []):
            case = TestCase(
                input=case_data["input"],
                expected=case_data["expected"],
                tags=case_data.get("tags", []),
                metadata=case_data.get("metadata", {}),
            )
            cases.append(case)

        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            cases=cases,
            metadata=data.get("metadata", {}),
            scoring_config=data.get("scoring", {}),
        )

    @staticmethod
    def _validate_dataset_dict(data: Any) -> None:
        """Validate dataset payload loaded from YAML.

        Args:
            data: Parsed YAML payload.

        Raises:
            ValueError: If dataset schema is invalid.
        """
        if not isinstance(data, dict):
            raise ValueError("Dataset YAML must be a dictionary")

        if "cases" not in data:
            raise ValueError("Dataset YAML must include a 'cases' field")

        cases = data["cases"]
        if not isinstance(cases, list):
            raise ValueError("Dataset 'cases' must be a list")

        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                raise ValueError(f"Case at index {index} must be a dictionary")
            if "input" not in case:
                raise ValueError(f"Case at index {index} missing required field 'input'")
            if "expected" not in case:
                raise ValueError(f"Case at index {index} missing required field 'expected'")
            if not isinstance(case["input"], str):
                raise ValueError(f"Case at index {index} field 'input' must be a string")
            if not isinstance(case["expected"], str):
                raise ValueError(f"Case at index {index} field 'expected' must be a string")
            if "tags" in case and not isinstance(case["tags"], list):
                raise ValueError(f"Case at index {index} field 'tags' must be a list")

    def to_yaml(self, path: str | Path) -> None:
        """Save dataset to YAML file.

        Args:
            path: Path to write YAML file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "name": self.name,
            "description": self.description,
            "cases": [
                {
                    "input": case.input,
                    "expected": case.expected,
                    "tags": case.tags,
                    "metadata": case.metadata,
                }
                for case in self.cases
            ],
            "metadata": self.metadata,
            "scoring": self.scoring_config,
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def __len__(self) -> int:
        """Return number of test cases."""
        return len(self.cases)

    def filter_by_tag(self, tag: str) -> "Dataset":
        """Filter dataset to cases with specific tag.

        Args:
            tag: Tag to filter by.

        Returns:
            New Dataset with filtered cases.
        """
        filtered_cases = [case for case in self.cases if tag in case.tags]
        return Dataset(
            name=f"{self.name}_filtered_{tag}",
            cases=filtered_cases,
            description=f"{self.description} (filtered: {tag})",
            metadata=self.metadata,
            scoring_config=self.scoring_config,
        )

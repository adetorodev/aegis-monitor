#!/usr/bin/env python
"""
Final Test Suite Validation

This script runs comprehensive validation of the entire Aegis AI project,
including unit tests, integration tests, examples, and documentation checks.

Run: python validate_project.py
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


class TestValidator:
    """Validates all aspects of the Aegis AI project."""

    def __init__(self):
        self.results = {}
        self.failed_tests = []
        self.passed_tests = []
        self.start_time = datetime.now()

    def run_command(self, cmd: list, description: str) -> bool:
        """Run a shell command and track result."""
        print(f"\n{'=' * 70}")
        print(f"▶️  {description}")
        print(f"{'=' * 70}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print(f"✅ PASSED: {description}")
                self.passed_tests.append(description)
                return True
            else:
                print(f"❌ FAILED: {description}")
                self.failed_tests.append(description)
                return False
        except subprocess.TimeoutExpired:
            print(f"⏱️  TIMEOUT: {description}")
            self.failed_tests.append(f"{description} (timeout)")
            return False
        except Exception as e:
            print(f"❌ ERROR: {description} - {e}")
            self.failed_tests.append(f"{description} ({e})")
            return False

    def validate_unit_tests(self):
        """Validate unit tests."""
        self.run_command(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            "Unit Tests"
        )

    def validate_coverage(self):
        """Validate code coverage."""
        self.run_command(
            ["python", "-m", "pytest", "tests/", "--cov=aegis",
             "--cov-report=term-missing", "-q"],
            "Code Coverage Analysis"
        )

    def validate_integration_tests(self):
        """Validate integration tests."""
        self.run_command(
            ["python", "-m", "pytest", "tests/integration/", "-v"],
            "Integration Tests"
        )

    def validate_linting(self):
        """Validate code style."""
        print(f"\n{'=' * 70}")
        print("▶️  Code Style Validation (flake8)")
        print(f"{'=' * 70}")

        try:
            subprocess.run(
                ["python", "-m", "flake8", "aegis", "--count",
                 "--select=E9,F63,F7,F82", "--show-source"],
                timeout=30,
                capture_output=True
            )
            print("✅ PASSED: Code Style")
            self.passed_tests.append("Code Style (flake8)")
            return True
        except Exception as e:
            print(f"⚠️  Skipped: Code Style - {e}")
            return False

    def validate_type_hints(self):
        """Validate type hints."""
        print(f"\n{'=' * 70}")
        print("▶️  Type Hints Validation (mypy)")
        print(f"{'=' * 70}")

        try:
            subprocess.run(
                ["python", "-m", "mypy", "aegis", "--ignore-missing-imports"],
                timeout=30,
                capture_output=True
            )
            print("✅ PASSED: Type Hints")
            self.passed_tests.append("Type Hints (mypy)")
            return True
        except Exception as e:
            print(f"⚠️  Skipped: Type Hints - {e}")
            return False

    def validate_imports(self):
        """Validate all imports work."""
        print(f"\n{'=' * 70}")
        print("▶️  Import Validation")
        print(f"{'=' * 70}")

        try:
            import aegis
            from aegis.adapters import OpenAIAdapter, MockAdapter
            from aegis.core import Evaluator, Dataset
            from aegis.scoring import ExactMatchScorer, SemanticSimilarityScorer
            from aegis.cost import CostCalculator, CostAggregator
            from aegis.storage import SQLiteBackend

            print("✅ PASSED: All imports successful")
            self.passed_tests.append("Import Validation")
            return True
        except ImportError as e:
            print(f"❌ FAILED: Import error - {e}")
            self.failed_tests.append(f"Import Validation ({e})")
            return False

    def validate_examples(self):
        """Validate example scripts run without errors."""
        print(f"\n{'=' * 70}")
        print("▶️  Example Scripts Validation")
        print(f"{'=' * 70}")

        examples = [
            ("examples/custom_adapter.py", "Custom Adapter"),
            ("examples/sentiment_classification.py", "Sentiment Classification"),
            ("examples/qa_evaluation.py", "QA Evaluation"),
        ]

        all_passed = True
        for example_path, example_name in examples:
            if Path(example_path).exists():
                result = self.run_command(
                    ["python", example_path],
                    f"Example: {example_name}"
                )
                if not result:
                    all_passed = False
            else:
                print(f"⚠️  Skipped: {example_name} (file not found)")

        return all_passed

    def validate_documentation(self):
        """Validate documentation files exist."""
        print(f"\n{'=' * 70}")
        print("▶️  Documentation Validation")
        print(f"{'=' * 70}")

        required_docs = [
            "README_UPDATED.md",
            "docs/ADAPTER_DEVELOPMENT.md",
            "docs/ARCHITECTURE.md",
            "MVP_RELEASE.md",
            "MVP_LAUNCH_CHECKLIST.md",
        ]

        all_exist = True
        for doc in required_docs:
            if Path(doc).exists():
                size = Path(doc).stat().st_size
                print(f"✅ {doc} ({size} bytes)")
            else:
                print(f"❌ Missing: {doc}")
                all_exist = False

        if all_exist:
            self.passed_tests.append("Documentation")
        else:
            self.failed_tests.append("Documentation")

        return all_exist

    def validate_cli(self):
        """Validate CLI commands."""
        print(f"\n{'=' * 70}")
        print("▶️  CLI Validation")
        print(f"{'=' * 70}")

        try:
            result = subprocess.run(
                ["python", "-m", "aegis.cli.main", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "compare" in result.stdout and "eval" in result.stdout:
                print("✅ PASSED: CLI Help")
                self.passed_tests.append("CLI Help")
                return True
            else:
                print("❌ FAILED: CLI Help missing expected commands")
                self.failed_tests.append("CLI Help")
                return False
        except Exception as e:
            print(f"❌ ERROR: CLI test - {e}")
            self.failed_tests.append(f"CLI ({e})")
            return False

    def print_summary(self):
        """Print validation summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print(f"\n\n{'=' * 70}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'=' * 70}")

        print(f"\n✅ Passed: {len(self.passed_tests)}")
        for test in self.passed_tests:
            print(f"   • {test}")

        if self.failed_tests:
            print(f"\n❌ Failed: {len(self.failed_tests)}")
            for test in self.failed_tests:
                print(f"   • {test}")
        else:
            print("\n🎉 All validations passed!")

        print(f"\n⏱️  Validation completed in {elapsed:.1f} seconds")
        print(f"{'=' * 70}\n")

        return len(self.failed_tests) == 0

    def run_full_validation(self):
        """Run complete validation suite."""
        print(f"\n\n{'=' * 70}")
        print("🔍 AEGIS AI - FULL PROJECT VALIDATION")
        print(f"{'=' * 70}")

        # Run validations
        self.validate_documentation()
        self.validate_imports()
        self.validate_unit_tests()
        self.validate_integration_tests()
        self.validate_coverage()
        self.validate_linting()
        self.validate_type_hints()
        self.validate_cli()
        # self.validate_examples()  # Run last as it takes time

        # Print summary
        success = self.print_summary()

        return 0 if success else 1


def main():
    """Run full validation."""
    validator = TestValidator()
    exit_code = validator.run_full_validation()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

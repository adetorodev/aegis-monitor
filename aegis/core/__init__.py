"""Core evaluation orchestration components."""

from aegis.core.evaluator import Evaluator
from aegis.core.results import EvaluationResult, TestCaseResult
from aegis.core.dataset import Dataset, TestCase
from aegis.core.regression import RegressionAnalysis, RegressionDetector, RegressionThresholds

__all__ = [
    "Evaluator",
    "EvaluationResult",
    "TestCaseResult",
    "Dataset",
    "TestCase",
    "RegressionDetector",
    "RegressionThresholds",
    "RegressionAnalysis",
]

"""
Aegis AI - LLM Evaluation and Cost Monitoring Framework

A unified framework for evaluating LLM output quality, monitoring costs,
and detecting regressions in production AI systems.
"""

__version__ = "0.1.0"
__author__ = "Aegis AI Team"

from aegis.core.evaluator import Evaluator
from aegis.core.results import EvaluationResult

__all__ = ["Evaluator", "EvaluationResult", "__version__"]

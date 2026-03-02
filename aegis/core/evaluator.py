"""Main evaluation orchestrator."""

import asyncio
import logging
from typing import Optional
from datetime import datetime
import uuid

from aegis.core.dataset import Dataset
from aegis.core.results import EvaluationResult, TestCaseResult
from aegis.adapters.base import BaseModelAdapter
from aegis.scoring.base import BaseScorer
from aegis.cost.calculator import CostCalculator
from aegis.storage.base import BaseStorage


logger = logging.getLogger(__name__)


class Evaluator:
    """Orchestrates LLM evaluation workflow.

    Coordinates dataset loading, model generation, scoring, cost tracking,
    and result storage.
    """

    def __init__(
        self,
        adapter: BaseModelAdapter,
        scorer: BaseScorer,
        storage: Optional[BaseStorage] = None,
        cost_calculator: Optional[CostCalculator] = None,
    ) -> None:
        """Initialize evaluator.

        Args:
            adapter: Model adapter for generation.
            scorer: Scorer for evaluating outputs.
            storage: Optional storage backend for persisting results.
            cost_calculator: Optional cost calculator for token-cost tracking.
        """
        self.adapter = adapter
        self.scorer = scorer
        self.storage = storage
        self.cost_calculator = cost_calculator
        self.run_id = str(uuid.uuid4())

    async def run(
        self,
        dataset: Dataset,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> EvaluationResult:
        """Run evaluation on dataset.

        Args:
            dataset: Dataset to evaluate against.
            system_prompt: Optional system message for model.
            **kwargs: Additional model generation parameters.

        Returns:
            EvaluationResult with all metrics.
        """
        logger.info(
            f"Starting evaluation: {dataset.name} on {self.adapter.model}"
        )

        results = []

        for i, test_case in enumerate(dataset.cases):
            logger.debug(f"Evaluating case {i+1}/{len(dataset.cases)}")

            # Generate model output
            response = await self.adapter.generate(
                prompt=test_case.input,
                system_prompt=system_prompt,
                **kwargs,
            )

            # Score the output
            scoring_result = self.scorer.score(
                expected=test_case.expected,
                actual=response.text,
            )

            # Create result record
            cost = 0.0
            if self.cost_calculator is not None:
                try:
                    cost = self.cost_calculator.calculate_request_cost(
                        model=response.model,
                        input_tokens=response.input_tokens,
                        output_tokens=response.output_tokens,
                    )
                except ValueError:
                    cost = 0.0

            result = TestCaseResult(
                input=test_case.input,
                expected=test_case.expected,
                actual=response.text,
                score=scoring_result.score,
                latency_ms=response.latency_ms,
                cost=cost,
                metadata={
                    "tokens_in": response.input_tokens,
                    "tokens_out": response.output_tokens,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "model": response.model,
                    "scoring_explanation": scoring_result.explanation,
                },
            )
            results.append(result)

        # Create evaluation result
        eval_result = EvaluationResult(
            dataset_name=dataset.name,
            model=self.adapter.model,
            cases=results,
            run_id=self.run_id,
            created_at=datetime.now(),
            metadata={
                "adapter": self.adapter.provider_name,
                "scorer": self.scorer.name,
                "dataset_size": len(dataset.cases),
            },
        )

        # Save if storage available
        if self.storage:
            self.storage.save_run(eval_result.to_dict(), self.run_id)
            logger.info(f"Evaluation results saved with run_id: {self.run_id}")

        logger.info(f"Evaluation complete. Avg score: {eval_result.avg_score:.3f}")

        return eval_result

    def run_sync(
        self,
        dataset: Dataset,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> EvaluationResult:
        """Synchronous wrapper for run().

        Args:
            dataset: Dataset to evaluate against.
            system_prompt: Optional system message for model.
            **kwargs: Additional model generation parameters.

        Returns:
            EvaluationResult with all metrics.
        """
        return asyncio.run(self.run(dataset, system_prompt, **kwargs))

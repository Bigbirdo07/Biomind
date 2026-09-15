"""
BioReason evaluation harness for running benchmarks against model adapters.
"""

import json
from typing import List, Dict, Any, Optional
from bioreason.schemas.benchmark import BenchmarkItem, EvaluationScore
from bioreason.models.base import BaseModelAdapter, GenerationConfig, ModelPrediction
from .rubric import ScientificRubricScorer
from .metrics import compute_aggregate_benchmark_metrics


PROMPT_TEMPLATE = """You are BioReason, a biology-native scientific reasoning AI.
Evaluate the following scientific scenario and proposed analysis with maximum methodological rigor.

SCENARIO:
{scenario}

QUESTION:
{question}

You must respond in valid JSON format with the following keys:
{{
  "flaw_detected": true/false,
  "flaw_type": "name of flaw if present or null",
  "scientific_rationale": "detailed explanation of biological, statistical, or ML validity",
  "proposed_correction": "statistically and biologically defensible alternative",
  "limitations": ["list", "of", "limitations"]
}}
"""


class BioReasonEvaluationHarness:
    def __init__(self, adapter: BaseModelAdapter, scorer: Optional[ScientificRubricScorer] = None):
        self.adapter = adapter
        self.scorer = scorer or ScientificRubricScorer()

    def format_prompt(self, item: BenchmarkItem) -> str:
        return PROMPT_TEMPLATE.format(scenario=item.scenario, question=item.question)

    def evaluate_benchmark(
        self,
        benchmark_items: List[BenchmarkItem],
        config: Optional[GenerationConfig] = None
    ) -> Dict[str, Any]:
        scores: List[EvaluationScore] = []
        predictions: List[ModelPrediction] = []

        for item in benchmark_items:
            prompt = self.format_prompt(item)
            pred = self.adapter.evaluate_item(prompt, item.item_id, config)
            predictions.append(pred)
            score = self.scorer.evaluate_prediction(item, pred)
            scores.append(score)

        aggregate = compute_aggregate_benchmark_metrics(scores)
        
        return {
            "aggregate_metrics": aggregate,
            "individual_scores": [s.model_dump() for s in scores],
            "predictions": [p.model_dump() for p in predictions],
        }

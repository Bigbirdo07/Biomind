"""
BioReason evaluation harness for running benchmarks against model adapters.
"""

import json
from typing import List, Dict, Any, Optional
from bioreason.schemas.benchmark import BenchmarkItem, EvaluationScore
from bioreason.models.base import BaseModelAdapter, GenerationConfig, ModelPrediction
from .rubric import ScientificRubricScorer
from .metrics import compute_aggregate_benchmark_metrics


PROMPT_TEMPLATE = """You are evaluating a biological and scientific data analysis with rigorous methodological standards.
Identify methodological problems, explain them concisely, recommend defensible corrections, and distinguish supported from unsupported conclusions.

SCENARIO:
{scenario}

QUESTION:
{question}

Provide your evaluation strictly as a valid JSON object matching this schema:
{{
  "primary_assessment": "<concise summary of scientific assessment>",
  "identified_issues": ["<issue 1>", "<issue 2>"],
  "recommended_actions": ["<defensible correction 1>", "<action 2>"],
  "supported_claims": ["<claims warranted by design and data>"],
  "unsupported_claims": ["<claims exceeding evidence or causal overclaims>"],
  "confidence": "LOW" | "MEDIUM" | "HIGH"
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

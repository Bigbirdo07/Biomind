"""
Mock model adapter for deterministic testing and benchmark verification without GPU weights.
"""

import json
from typing import Optional, Dict, Any
from .base import BaseModelAdapter, GenerationConfig, ModelPrediction


class MockModelAdapter(BaseModelAdapter):
    """
    Deterministic mock adapter used for unit testing, CI pipelines,
    and harness verification without requiring multi-gigabyte neural network weights.
    """

    def __init__(self, mode: str = "oracle"):
        """
        mode: 'oracle' (answers correctly), 'naive' (fails flaw detection), or 'custom'
        """
        self.mode = mode

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        if self.mode == "oracle":
            return json.dumps({
                "primary_assessment": "The proposed analysis contains fatal methodological issues in replication and validation structure.",
                "identified_issues": ["detected_methodological_flaw", "violates independence and cross-validation assumptions"],
                "recommended_actions": ["Re-architect workflow using proper biological replication and nested training pipelines."],
                "supported_claims": ["Experimental measurements were collected."],
                "unsupported_claims": ["Causal generalizability claim exceeds observational evidence."],
                "confidence": "HIGH",
                "flaw_detected": True,
                "flaw_type": "detected_methodological_flaw",
                "scientific_rationale": "The proposed analysis violates core statistical and biological assumptions.",
                "proposed_correction": "Re-architect workflow using proper biological replication and nested training pipelines.",
                "limitations": ["Requires external cohort validation.", "Association does not imply causality."]
            }, indent=2)
        else:
            return json.dumps({
                "primary_assessment": "The analysis appears methodologically sound and executes without code errors.",
                "identified_issues": [],
                "recommended_actions": ["Proceed with current pipeline."],
                "supported_claims": ["The classifier achieves 99% accuracy."],
                "unsupported_claims": [],
                "confidence": "HIGH",
                "flaw_detected": False,
                "flaw_type": None,
                "scientific_rationale": "The code runs without error and yields high accuracy.",
                "proposed_correction": "None, execute proposed analysis.",
                "limitations": []
            }, indent=2)

    def evaluate_item(self, prompt: str, item_id: str, config: Optional[GenerationConfig] = None) -> ModelPrediction:
        response_text = self.generate(prompt, config)
        try:
            parsed = json.loads(response_text)
        except Exception:
            parsed = {}

        return ModelPrediction(
            item_id=item_id,
            prompt=prompt,
            raw_response=response_text,
            parsed_json=parsed,
            primary_assessment=parsed.get("primary_assessment"),
            identified_issues=parsed.get("identified_issues", []),
            recommended_actions=parsed.get("recommended_actions", []),
            supported_claims=parsed.get("supported_claims", []),
            unsupported_claims=parsed.get("unsupported_claims", []),
            confidence=parsed.get("confidence", "MEDIUM"),
            flaw_detected=parsed.get("flaw_detected") if parsed.get("flaw_detected") is not None else (len(parsed.get("identified_issues", [])) > 0),
            flaw_type=parsed.get("flaw_type") or (" ".join(parsed.get("identified_issues", [])) if parsed.get("identified_issues") else None),
            scientific_rationale=parsed.get("scientific_rationale") or parsed.get("primary_assessment"),
            proposed_correction=parsed.get("proposed_correction") or (" ".join(parsed.get("recommended_actions", [])) if parsed.get("recommended_actions") else None),
            limitations_noted=parsed.get("limitations", parsed.get("unsupported_claims", []))
        )


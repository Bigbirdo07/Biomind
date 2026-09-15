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
                "flaw_detected": True,
                "flaw_type": "detected_methodological_flaw",
                "scientific_rationale": "The proposed analysis violates core statistical and biological assumptions.",
                "proposed_correction": "Re-architect workflow using proper biological replication and nested training pipelines.",
                "limitations": ["Requires external cohort validation.", "Association does not imply causality."]
            }, indent=2)
        else:
            return json.dumps({
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
            flaw_detected=parsed.get("flaw_detected"),
            flaw_type=parsed.get("flaw_type"),
            scientific_rationale=parsed.get("scientific_rationale"),
            proposed_correction=parsed.get("proposed_correction"),
            limitations_noted=parsed.get("limitations", [])
        )

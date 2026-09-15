"""
Base interfaces and generation configurations for model adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    max_new_tokens: int = 1024
    temperature: float = 0.1
    top_p: float = 0.95
    do_sample: bool = False
    repetition_penalty: float = 1.05


class ModelPrediction(BaseModel):
    item_id: str
    prompt: str
    raw_response: str
    parsed_json: Optional[Dict[str, Any]] = None
    flaw_detected: Optional[bool] = None
    flaw_type: Optional[str] = None
    scientific_rationale: Optional[str] = None
    proposed_correction: Optional[str] = None
    limitations_noted: List[str] = Field(default_factory=list)
    primary_assessment: Optional[str] = None
    identified_issues: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    supported_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    confidence: Optional[str] = "MEDIUM"  # "LOW", "MEDIUM", "HIGH"



class BaseModelAdapter(ABC):
    """Abstract interface for LLM inference in BioReason."""

    @abstractmethod
    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        """Generate response from prompt."""
        pass

    @abstractmethod
    def evaluate_item(self, prompt: str, item_id: str, config: Optional[GenerationConfig] = None) -> ModelPrediction:
        """Evaluate a single benchmark item and return structured prediction."""
        pass

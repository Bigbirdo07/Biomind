"""
Typed schemas for BioReasonPreference-v0.1 preference optimization pairs.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PreferenceCategory(str, Enum):
    VALID_VS_FALSE_ALARM = "VALID_VS_FALSE_ALARM"
    ACTIONABLE_VS_VAGUE_CORRECTION = "ACTIONABLE_VS_VAGUE_CORRECTION"
    CALIBRATED_VS_OVERCONFIDENT = "CALIBRATED_VS_OVERCONFIDENT"
    ASSOCIATION_VS_CAUSATION = "ASSOCIATION_VS_CAUSATION"
    CORRECT_EXPERIMENTAL_UNIT = "CORRECT_EXPERIMENTAL_UNIT"
    CORRECT_VALIDATION_STRATEGY = "CORRECT_VALIDATION_STRATEGY"
    PRIMARY_ISSUE_PRIORITIZATION = "PRIMARY_ISSUE_PRIORITIZATION"
    INSUFFICIENT_INFORMATION_VS_INVENTED_ASSUMPTION = "INSUFFICIENT_INFORMATION_VS_INVENTED_ASSUMPTION"
    METHOD_COMPARISON = "METHOD_COMPARISON"
    BIOMARKER_EVIDENCE_CALIBRATION = "BIOMARKER_EVIDENCE_CALIBRATION"


class ScientificSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    SERIOUS = "SERIOUS"
    WARNING = "WARNING"
    INFO = "INFO"


class PreferenceSourceType(str, Enum):
    ACTUAL_SFT_ERROR = "ACTUAL_SFT_ERROR"
    DPO_SMOKE_RESIDUAL = "DPO_SMOKE_RESIDUAL"
    COUNTERFACTUAL_VARIANT = "COUNTERFACTUAL_VARIANT"
    EXPERT_SCIENTIFIC_CONTRAST = "EXPERT_SCIENTIFIC_CONTRAST"


class PreferenceReviewStatus(str, Enum):
    PREF_A = "PREF_A"  # Human expert reviewed
    PREF_B = "PREF_B"  # Computational biologist reviewed
    PREF_C = "PREF_C"  # Automated rule-validated
    EXPERT_VALIDATED = "expert_validated"
    EXPERT_VERIFIED = "expert_verified"
    VALIDATED = "validated"
    FLAGGED = "flagged"
    DEVELOPER_SCIENTIST_REVIEWED = "developer_scientist_reviewed"  # honest label: authored/reviewed by the project's developer-scientist, NOT an independent external human expert


class BioReasonPreferencePair(BaseModel):
    model_config = ConfigDict(extra="ignore")

    preference_id: str = Field(description="Unique preference pair identifier (e.g. PREF_001_PRIMARY_ISSUE_LEAKAGE)")
    category: PreferenceCategory = Field(description="Core archetype of preference contrast")
    prompt: str = Field(description="Scientific scenario and analytical question")
    preferred_response: Dict[str, Any] = Field(description="High-quality, actionable, calibrated scientific response")
    rejected_response: Dict[str, Any] = Field(description="Plausible but scientifically flawed or vague response")
    preference_reason: str = Field(description="Detailed scientific justification explaining why preferred is superior")
    error_taxonomy: List[str] = Field(default_factory=list, description="Taxonomy classes corrected by this preference pair")
    scientific_severity: ScientificSeverity = Field(default=ScientificSeverity.SERIOUS)
    domain: str = Field(description="Scientific domain (e.g. biological_ml, scrna_seq, bulk_rnaseq)")
    source: str = Field(default="bioreason_expert_review", description="Provenance of the preference pair")
    source_type: PreferenceSourceType = Field(default=PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST)
    review_status: PreferenceReviewStatus = Field(default=PreferenceReviewStatus.PREF_A)
    parent_episode_ids: List[str] = Field(default_factory=list, description="IDs of source reasoning episodes if derived")


def format_dpo_pair(pair: BioReasonPreferencePair) -> Dict[str, str]:
    """
    Format a BioReasonPreferencePair into chosen and rejected strings for DPO
    trainers. If a response dict has a "text" key, that plain-prose string is
    used verbatim (this is the expected shape for pairs authored after the
    SFT-001 format-collapse finding, where DPO targets must not be JSON-only).
    Otherwise falls back to json.dumps of the whole dict, for backward
    compatibility with older JSON-shaped preference pairs.
    """
    import json

    def render(response: Dict[str, Any]) -> str:
        if isinstance(response, dict) and "text" in response and len(response) == 1:
            return response["text"]
        return json.dumps(response, indent=2)

    return {
        "prompt": pair.prompt,
        "chosen": render(pair.preferred_response),
        "rejected": render(pair.rejected_response),
    }


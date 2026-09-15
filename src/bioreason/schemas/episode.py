"""
Typed schemas for Scientific Reasoning Episodes and Claim Hierarchy.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .experiment import ExperimentSpec


class ValidationStatus(str, Enum):
    EXPERT_VALIDATED = "expert_validated"
    PEER_REVIEWED = "peer_reviewed"
    BENCHMARK_VERIFIED = "benchmark_verified"
    DRAFT = "draft"
    PROVISIONAL = "provisional"


class ClaimLevel(str, Enum):
    OBSERVATION = "OBSERVATION"
    STATISTICAL_INFERENCE = "STATISTICAL_INFERENCE"
    BIOLOGICAL_INTERPRETATION = "BIOLOGICAL_INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    CAUSAL_CLAIM = "CAUSAL_CLAIM"


class ScientificClaim(BaseModel):
    statement: str = Field(description="The scientific statement or assertion")
    level: ClaimLevel = Field(description="Strict epistemic classification of the claim")
    justification: Optional[str] = Field(
        default=None,
        description="Scientific evidence or rationale supporting this classification level"
    )


class ScientificChecks(BaseModel):
    replication_valid: bool = Field(
        description="True if biological replication is sufficient and pseudoreplication is avoided"
    )
    confounding_detected: bool = Field(
        description="True if batch or technical covariates confound biological variables of interest"
    )
    leakage_detected: bool = Field(
        description="True if test/validation information leaked into training transformations/splits"
    )
    transformation_valid: bool = Field(
        description="True if data transformations are mathematically and biologically compatible with downstream models"
    )
    multiple_testing_controlled: Optional[bool] = Field(
        default=True,
        description="True if false discovery rate or family-wise error rate is appropriately controlled"
    )
    sample_size_adequate: Optional[bool] = Field(
        default=True,
        description="True if biological sample size (n) is adequate for statistical power in p >> n regimes"
    )


class InterpretationSection(BaseModel):
    supported_claims: List[ScientificClaim] = Field(
        default_factory=list,
        description="Claims legitimately supported by data and methodology"
    )
    unsupported_claims: List[ScientificClaim] = Field(
        default_factory=list,
        description="Claims that exceed the evidence or conflate association with causality"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Methodological, statistical, and biological limitations of the analysis"
    )


class ScientificReasoningEpisode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_id: str = Field(description="Unique deterministic identifier (e.g., EP_001_SCRNA_PSEUDOREP)")
    domain: str = Field(
        description="Scientific domain (e.g., single_cell_transcriptomics, biological_ml, bulk_rnaseq, variant_calling)"
    )
    question: str = Field(description="User question, research problem, or proposed analytical scenario")
    experiment: ExperimentSpec = Field(description="Structured metadata of the biological experiment")
    proposed_analysis: str = Field(description="Description or code snippet of the proposed or flawed analysis")
    scientific_checks: ScientificChecks = Field(description="Evaluation of core scientific validity checks")
    preferred_analysis: str = Field(
        description="Methodologically rigorous alternative or corrected analytical workflow"
    )
    reasoning_summary: str = Field(
        description="Concise scientific rationale explaining the flaw, assumptions, and correction"
    )
    interpretation: InterpretationSection = Field(
        description="Explicit breakdown of supported vs unsupported claims and limitations"
    )
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.EXPERT_VALIDATED,
        description="Verification status of the episode"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Citations, DOIs, or peer-reviewed literature references supporting the rationale"
    )

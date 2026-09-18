"""
Typed schemas for Scientific Reasoning Episodes, Claim Hierarchy, and Episode Classification.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .experiment import ExperimentSpec


class ValidationStatus(str, Enum):
    DRAFT = "draft"
    AUTO_VALIDATED = "auto_validated"
    SCIENTIST_REVIEWED = "scientist_reviewed"
    EXPERT_VALIDATED = "expert_validated"
    PEER_REVIEWED = "peer_reviewed"
    BENCHMARK_VERIFIED = "benchmark_verified"
    PROVISIONAL = "provisional"


class EpisodeType(str, Enum):
    CORRECT_WORKFLOW = "CORRECT_WORKFLOW"
    FLAWED_WORKFLOW = "FLAWED_WORKFLOW"
    COMPARE_METHODS = "COMPARE_METHODS"
    DIAGNOSE_FAILURE = "DIAGNOSE_FAILURE"
    INTERPRET_RESULT = "INTERPRET_RESULT"
    DESIGN_EXPERIMENT = "DESIGN_EXPERIMENT"
    SELECT_MODEL = "SELECT_MODEL"
    ASSESS_CLAIM = "ASSESS_CLAIM"
    UNCERTAINTY_CASE = "UNCERTAINTY_CASE"


class ClaimLevel(str, Enum):
    OBSERVATION = "OBSERVATION"
    STATISTICAL_INFERENCE = "STATISTICAL_INFERENCE"
    BIOLOGICAL_INTERPRETATION = "BIOLOGICAL_INTERPRETATION"
    HYPOTHESIS = "HYPOTHESIS"
    CAUSAL_CLAIM = "CAUSAL_CLAIM"


class BiomarkerEvidenceLevel(str, Enum):
    """
    Structured biomarker evidence hierarchy.
    Crucial scientific principle: No single biomarker evidence level automatically proves
    biological causality or mechanistic necessity.
    """
    LEVEL_0_CANDIDATE_FEATURE = "LEVEL_0: Candidate predictive feature"
    LEVEL_1_INTERNALLY_STABLE = "LEVEL_1: Internally stable feature"
    LEVEL_2_CV_STABLE_SIGNATURE = "LEVEL_2: Cross-validation stable signature"
    LEVEL_3_EXTERNAL_COHORT = "LEVEL_3: Independent external cohort replication"
    LEVEL_4_ORTHOGONAL_ASSAY = "LEVEL_4: Orthogonal assay validation"
    LEVEL_5_PROSPECTIVE_VALIDATION = "LEVEL_5: Prospective validation"
    LEVEL_6_CLINICAL_UTILITY = "LEVEL_6: Clinical utility / deployment evidence"



class ScientificClaim(BaseModel):
    statement: str = Field(description="The scientific statement or assertion")
    level: ClaimLevel = Field(description="Strict epistemic classification of the claim")
    justification: Optional[str] = Field(
        default=None,
        description="Scientific evidence or rationale supporting this classification level"
    )


class ScientificChecks(BaseModel):
    replication_valid: bool = Field(
        description="True if biological replication is modeled independently and pseudoreplication is avoided"
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
        description="True if biological sample size (independent N) provides adequate statistical power"
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


class ScenarioSignature(BaseModel):
    """
    Structured semantic signature of an experimental scenario used for
    fine-grained contamination detection across different surface wordings.
    """
    assay: str
    problem: str
    experimental_unit: str
    observational_unit: Optional[str] = "same"
    analysis: str
    failure_mode: Optional[str] = "none"


class SourceProvenance(BaseModel):
    source_type: str = Field(default="expert_authored", description="e.g. expert_authored, methods_paper, textbook, benchmark")
    citation: Optional[str] = None
    doi: Optional[str] = None
    license: Optional[str] = "CC-BY-4.0"
    author: Optional[str] = "BioReason Scientific Working Group"
    reviewer: Optional[str] = None
    review_status: ValidationStatus = ValidationStatus.EXPERT_VALIDATED


class ScientificReasoningEpisode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_id: str = Field(description="Unique deterministic identifier (e.g., EP_001_SCRNA_PSEUDOREP)")
    episode_type: Optional[EpisodeType] = Field(
        default=EpisodeType.FLAWED_WORKFLOW,
        description="Specific pedagogical archetype of the reasoning episode"
    )
    domain: str = Field(
        description="Scientific domain (e.g., single_cell_transcriptomics, biological_ml, bulk_rnaseq, variant_calling)"
    )
    subdomain: Optional[str] = None
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
    scenario_signature: Optional[ScenarioSignature] = None
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.EXPERT_VALIDATED,
        description="Verification status of the episode"
    )
    quality_tier: Optional[str] = Field(
        default=None,
        description="Assigned quality tier (TIER_A, TIER_B, TIER_C, TIER_D)"
    )
    example_weight: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        description="Configurable sample loss weight for SFT"
    )
    provenance: Optional[SourceProvenance] = None
    sources: List[str] = Field(
        default_factory=list,
        description="Citations, DOIs, or peer-reviewed literature references supporting the rationale"
    )


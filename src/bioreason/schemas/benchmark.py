"""
Typed schemas for BioReasonBench items, difficulty levels, compound issues, scoring rubrics, and critical failure metrics.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .episode import ScenarioSignature, SourceProvenance


class DifficultyLevel(str, Enum):
    FOUNDATIONAL = "FOUNDATIONAL"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    ADVERSARIAL = "ADVERSARIAL"


class BenchmarkCategory(str, Enum):
    EXPERIMENTAL_DESIGN = "experimental_design"
    BIOLOGICAL_REPLICATION = "biological_replication"
    STATISTICAL_REASONING = "statistical_reasoning"
    CONFOUNDING = "confounding"
    BATCH_EFFECTS = "batch_effects"
    NORMALIZATION = "normalization"
    TRANSFORMATIONS = "transformations"
    BULK_RNASEQ = "bulk_rnaseq"
    SCRNA_SEQ = "scrna_seq"
    WGS_WES = "wgs_wes"
    FASTQ_BAM_VCF = "fastq_bam_vcf"
    GATK_WORKFLOWS = "gatk_workflows"
    DIFFERENTIAL_EXPRESSION = "differential_expression"
    ML_DESIGN = "ml_design"
    DATA_LEAKAGE = "data_leakage"
    CROSS_VALIDATION = "cross_validation"
    FEATURE_SELECTION = "feature_selection"
    MODEL_SELECTION = "model_selection"
    BIOMARKER_DISCOVERY = "biomarker_discovery"
    INTERPRETABILITY = "interpretability"
    OVERFITTING = "overfitting"
    RESULT_INTERPRETATION = "result_interpretation"
    BIOLOGICAL_PLAUSIBILITY = "biological_plausibility"
    REPRODUCIBILITY = "reproducibility"
    ADVERSARIAL_FLAWED_ANALYSIS = "adversarial_flawed_analysis"
    AMBIGUOUS_JUDGMENT = "ambiguous_judgment"


class RubricCriterion(BaseModel):
    name: str = Field(description="Criterion name (e.g. flaw_detection, scientific_explanation, correction_quality)")
    weight: float = Field(default=1.0, ge=0.0)
    key_points: List[str] = Field(description="Essential scientific concepts or points that must be recognized")
    negative_points: List[str] = Field(
        default_factory=list,
        description="Scientific errors, hallucinations, or uncalibrated claims that penalize score"
    )


class ScoringRubric(BaseModel):
    flaw_detection: RubricCriterion
    scientific_explanation: RubricCriterion
    correction_quality: RubricCriterion
    uncertainty_calibration: RubricCriterion
    interpretation_quality: RubricCriterion
    experimental_unit_reasoning: Optional[RubricCriterion] = None


class ExpectedDecision(BaseModel):
    primary_issue: str
    secondary_issues: List[str] = Field(default_factory=list)
    severity: str = "ERROR"
    acceptable_methods: List[str] = Field(default_factory=list)
    unacceptable_methods: List[str] = Field(default_factory=list)
    supported_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)


class ScoringBreakdown(BaseModel):
    must_identify: List[str] = Field(default_factory=list)
    should_identify: List[str] = Field(default_factory=list)
    critical_errors: List[str] = Field(
        default_factory=list,
        description="Fatal scientific endorsements that trigger critical_failure = true"
    )
    partial_credit: List[str] = Field(default_factory=list)


class BenchmarkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(description="Unique benchmark question identifier (e.g. BENCH_001_LEAKAGE_PCA)")
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Reasoning complexity level"
    )
    category: BenchmarkCategory
    scenario: str = Field(description="Detailed experimental, computational, or statistical scenario presented")
    question: str = Field(description="Specific scientific question testing deep reasoning")
    flawed_analysis_present: bool = Field(description="True if the presented scenario contains a methodological flaw")
    flaw_type: Optional[str] = Field(
        default=None,
        description="Short canonical flaw name if flawed"
    )
    ground_truth_rationale: str = Field(description="Authoritative, expert-validated scientific rationale")
    scoring_rubric: ScoringRubric
    expected_decision: Optional[ExpectedDecision] = None
    scoring_breakdown: Optional[ScoringBreakdown] = None
    scenario_signature: Optional[ScenarioSignature] = None
    provenance: Optional[SourceProvenance] = None
    tags: List[str] = Field(default_factory=list)


class EvaluationScore(BaseModel):
    item_id: str
    difficulty: Optional[DifficultyLevel] = DifficultyLevel.INTERMEDIATE
    flaw_detection_score: float = Field(ge=0.0, le=1.0)
    explanation_score: float = Field(ge=0.0, le=1.0)
    correction_score: float = Field(ge=0.0, le=1.0)
    calibration_score: float = Field(ge=0.0, le=1.0)
    interpretation_score: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    flaw_detected_binary: bool
    critical_failure: bool = Field(
        default=False,
        description="True if model endorsed an egregious scientific violation (e.g. pseudoreplication, causal overclaim, leakage)"
    )
    false_alarm: bool = Field(
        default=False,
        description="True if benchmark scenario was valid, but model invented a critical methodological flaw"
    )
    correction_actionability_score: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Actionability and specificity of recommended statistical and methodological corrections"
    )
    primary_issue_prioritized: Optional[bool] = Field(
        default=True,
        description="True if model identified and prioritized the primary methodological violation over peripheral concerns"
    )
    identified_failure_modes: List[str] = Field(default_factory=list)
    is_hard_negative: bool = Field(default=False, description="True if scenario was a valid hard-negative control")
    no_error_correct: bool = Field(default=False, description="True if scenario was valid and model correctly accepted it")
    is_insufficient_info: bool = Field(default=False, description="True if scenario required flagging insufficient information")
    high_confidence_critical_error: bool = Field(default=False, description="True if model made a high-confidence critical scientific failure")
    comments: Optional[str] = None




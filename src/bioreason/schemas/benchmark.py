"""
Typed schemas for BioReasonBench items, multi-dimensional scoring rubrics, and evaluation results.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


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


class BenchmarkItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(description="Unique benchmark question identifier (e.g. BENCH_001_LEAKAGE_PCA)")
    category: BenchmarkCategory
    scenario: str = Field(description="Detailed experimental, computational, or statistical scenario presented")
    question: str = Field(description="Specific scientific question testing deep reasoning")
    flawed_analysis_present: bool = Field(description="True if the presented scenario contains a methodological flaw")
    flaw_type: Optional[str] = Field(
        default=None,
        description="Short canonical flaw name if flawed (e.g., pseudoreplication, target_leakage, batch_confounding)"
    )
    ground_truth_rationale: str = Field(description="Authoritative, expert-validated scientific rationale")
    scoring_rubric: ScoringRubric
    tags: List[str] = Field(default_factory=list)


class EvaluationScore(BaseModel):
    item_id: str
    flaw_detection_score: float = Field(ge=0.0, le=1.0)
    explanation_score: float = Field(ge=0.0, le=1.0)
    correction_score: float = Field(ge=0.0, le=1.0)
    calibration_score: float = Field(ge=0.0, le=1.0)
    interpretation_score: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    flaw_detected_binary: bool
    comments: Optional[str] = None

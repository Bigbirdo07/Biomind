"""
src/bioreason/schemas/guided_pipeline.py

Schemas for BioReason Guided Pipeline Mode:
- Pipeline Intent & State Machine
- Pipeline Context & Intake
- Pipeline Plan & Foundation
- Code Chunks & Synchronized Guide Chunks
- Source Trace & Diagnostics
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class PipelineIntent(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"
    SCIENTIFIC_AUDIT = "SCIENTIFIC_AUDIT"
    PIPELINE_BUILD = "PIPELINE_BUILD"
    PIPELINE_DEBUG = "PIPELINE_DEBUG"
    PIPELINE_EXPLAIN = "PIPELINE_EXPLAIN"
    CODE_ONLY = "CODE_ONLY"
    OTHER = "OTHER"


class PipelineState(str, Enum):
    IDLE = "IDLE"
    PIPELINE_REQUESTED = "PIPELINE_REQUESTED"
    INTAKE_REQUIRED = "INTAKE_REQUIRED"
    INTAKE_PARTIAL = "INTAKE_PARTIAL"
    READY_TO_PLAN = "READY_TO_PLAN"
    PLAN_READY = "PLAN_READY"
    CODE_READY = "CODE_READY"
    DEBUGGING = "DEBUGGING"
    COMPLETE = "COMPLETE"


class ResponseSource(str, Enum):
    MODEL_GENERATED = "MODEL_GENERATED"
    BACKEND_DERIVED = "BACKEND_DERIVED"
    STATIC_DEMO = "STATIC_DEMO"
    FALLBACK = "FALLBACK"
    ERROR = "ERROR"


class PipelineContext(BaseModel):
    biological_question: Optional[str] = None
    analysis_goal: Optional[str] = None
    organism: Optional[str] = "Human (Homo sapiens)"
    genome_build: Optional[str] = "GRCh38 / hg38"
    input_type: Optional[str] = None  # count_matrix, fastq, bam, vcf, h5ad, csv
    file_paths: Dict[str, str] = Field(default_factory=dict)  # {"counts": "...", "metadata": "..."}
    file_layout: Optional[str] = None  # genes_x_samples, samples_x_genes
    matrix_orientation: Optional[str] = None
    sample_count: Optional[int] = None
    subject_count: Optional[int] = None
    experimental_unit: Optional[str] = None  # Patient, Animal, Biopsy, Cell, Unknown
    observation_unit: Optional[str] = None
    measurement_unit: Optional[str] = None
    groups: List[str] = Field(default_factory=list)
    group_counts: Dict[str, int] = Field(default_factory=dict)
    paired_design: Optional[bool] = None
    longitudinal: Optional[bool] = None
    technical_replicates: Optional[bool] = None
    biological_replicates: Optional[int] = None
    batch_columns: List[str] = Field(default_factory=list)
    covariates: List[str] = Field(default_factory=list)
    outcome: Optional[str] = None
    compute_environment: Optional[str] = "Local / Conda"
    requested_tools: List[str] = Field(default_factory=list)
    known_constraints: List[str] = Field(default_factory=list)
    missing_required_fields: List[str] = Field(default_factory=list)
    inferred_fields: Dict[str, str] = Field(default_factory=dict)
    n_pcs: int = 20


class ShapeProgressionStep(BaseModel):
    step: str
    shape: str
    description: Optional[str] = None


class ConfigField(BaseModel):
    key: str
    label: str
    default: str


class PipelineFoundation(BaseModel):
    experimental_unit: str
    observation_unit: str
    measurement_unit: str
    shape_progression: List[ShapeProgressionStep]
    analytical_stages: List[str] = Field(default_factory=list)


class PipelineStage(BaseModel):
    stage_id: str
    name: str
    purpose: str
    input: str
    output: str
    method: str
    scientific_reason: str
    assumptions: List[str] = Field(default_factory=list)
    user_configurable_values: List[str] = Field(default_factory=list)
    protected_constraints: List[str] = Field(default_factory=list)
    validation_checkpoint: str
    common_failures: List[str] = Field(default_factory=list)


class CodeChunk(BaseModel):
    chunk_id: str
    stage_id: str
    title: str
    language: str = "python"
    code: str
    depends_on: List[str] = Field(default_factory=list)
    user_edit_points: List[str] = Field(default_factory=list)
    expected_output: Optional[str] = None


class GuideChunk(BaseModel):
    chunk_id: str
    what: str
    why: str
    data_in: Optional[str] = None
    data_out: Optional[str] = None
    bio_change: Optional[str] = None
    statistical_assumptions: Optional[str] = None
    scores_vs_loadings: Optional[str] = None
    modify: Optional[str] = None
    warning: Optional[str] = None
    troubleshooting: Optional[str] = None
    validation_checkpoint: Optional[str] = None


class PipelineChunkPair(BaseModel):
    id: str
    stage_id: str
    title: str
    code: str
    guide: GuideChunk


class PipelinePlan(BaseModel):
    plan_id: str
    title: str
    analysis_goal: str
    experimental_unit: str
    observation_unit: str
    measurement_unit: str
    stages: List[PipelineStage]
    missing_information: List[str] = Field(default_factory=list)
    inferred_fields: Dict[str, str] = Field(default_factory=dict)


class GuidedPipelineData(BaseModel):
    title: str
    pipeline_context: PipelineContext
    foundation: PipelineFoundation
    config_fields: List[ConfigField]
    chunks: List[PipelineChunkPair]


class GuidedPipelineResponse(BaseModel):
    status: str = "success"
    mode: str = "guided_pipeline"  # conversational, guided_pipeline, scientific_audit
    message: str
    pipeline_state: PipelineState = PipelineState.IDLE
    pipeline_context: Optional[PipelineContext] = None
    guided_pipeline: Optional[GuidedPipelineData] = None
    audit: Optional[Dict[str, Any]] = None
    source_trace: ResponseSource = ResponseSource.MODEL_GENERATED
    model_checkpoint: str = "BR-VERIFIED-SFT-002 (final_adapter)"
    diagnostics: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None

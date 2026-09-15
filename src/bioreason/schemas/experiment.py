"""
Typed schemas for biological experimental design and metadata specification.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AssayType(str, Enum):
    BULK_RNA_SEQ = "bulk_rna_seq"
    SINGLE_CELL_RNA_SEQ = "scrna_seq"
    SINGLE_NUCLEUS_RNA_SEQ = "snrna_seq"
    WGS = "wgs"
    WES = "wes"
    CHIP_SEQ = "chip_seq"
    ATAC_SEQ = "atac_seq"
    PROTEOMICS = "proteomics"
    METABOLOMICS = "metabolomics"
    FLOW_CYTOMETRY = "flow_cytometry"
    OTHER = "other"


class ExperimentalUnitLevel(str, Enum):
    ORGANISM = "organism"
    PATIENT = "patient"
    ANIMAL = "animal"
    TISSUE_SAMPLE = "tissue_sample"
    CELL_CULTURE_DISH = "cell_culture_dish"
    CELL = "cell"
    READ = "read"
    OTHER = "other"


class DataType(str, Enum):
    RAW_COUNTS = "raw_counts"
    NORMALIZED_COUNTS = "normalized_counts"
    LOG_NORMALIZED_COUNTS = "log_normalized_counts"
    TPM_FPKM_RPKM = "tpm_fpkm_rpkm"
    FASTQ = "fastq"
    BAM_CRAM = "bam_cram"
    VCF = "vcf"
    CONTINUOUS_INTENSITY = "continuous_intensity"
    TABULAR_FEATURES = "tabular_features"
    OTHER = "other"


class AnalysisObjective(str, Enum):
    DIFFERENTIAL_EXPRESSION = "differential_expression"
    VARIANT_CALLING = "variant_calling"
    VARIANT_ANNOTATION = "variant_annotation"
    SUPERVISED_CLASSIFICATION = "supervised_classification"
    SUPERVISED_REGRESSION = "supervised_regression"
    BIOMARKER_DISCOVERY = "biomarker_discovery"
    CLUSTERING_CELL_TYPING = "clustering_cell_typing"
    TRAJECTORY_INFERENCE = "trajectory_inference"
    PATHWAY_ENRICHMENT = "pathway_enrichment"
    EXPLORATORY_ANALYSIS = "exploratory_analysis"


class SampleGroup(BaseModel):
    name: str
    sample_count: int = Field(ge=0, description="Number of distinct biological subjects/samples")
    cell_count: Optional[int] = Field(default=None, ge=0, description="Total cells if single-cell assay")
    description: Optional[str] = None


class BatchStructure(BaseModel):
    batch_variable: Optional[str] = None
    batch_count: Optional[int] = None
    confounded_with_group: bool = Field(
        default=False,
        description="True if batch perfectly or severely confounds the biological condition of interest"
    )
    notes: Optional[str] = None


class ExperimentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organism: str = Field(description="Scientific or common name of organism (e.g. Homo sapiens, Mercenaria mercenaria)")
    assay: AssayType = Field(description="Type of biological assay performed")
    experimental_unit: ExperimentalUnitLevel = Field(
        description="True independent biological unit of replication (e.g. animal, patient)"
    )
    samples: int = Field(ge=1, description="Total number of independent biological samples/replicates")
    total_observations: Optional[int] = Field(
        default=None,
        ge=1,
        description="Total measurements (e.g., total cells, total reads, total observations)"
    )
    groups: List[SampleGroup] = Field(default_factory=list, description="Experimental and control groups")
    covariates: List[str] = Field(default_factory=list, description="Known technical and biological covariates")
    batch_structure: Optional[BatchStructure] = Field(
        default=None,
        description="Structure of processing batches, dates, or sequencing runs"
    )
    input_data_type: DataType = Field(description="Format and transformation level of input data")
    objective: AnalysisObjective = Field(description="Primary scientific objective")
    description: Optional[str] = None

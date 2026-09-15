"""
Typed schemas for structured scientific workflow plans and validation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from .experiment import AssayType, ExperimentalUnitLevel


class SplitType(str, Enum):
    RANDOM_KFOLD = "random_kfold"
    STRATIFIED_KFOLD = "stratified_kfold"
    GROUPED_KFOLD = "grouped_kfold"
    STRATIFIED_GROUP_KFOLD = "stratified_group_kfold"
    TEMPORAL_SPLIT = "temporal_split"
    EXTERNAL_COHORT = "external_cohort"


class NormalizationMethod(str, Enum):
    NONE = "none"
    APPROPRIATE_FOR_ASSAY = "appropriate_for_assay"
    DESEQ2_MEDIAN_OF_RATIOS = "deseq2_median_of_ratios"
    TMM = "tmm"
    CPM = "cpm"
    TPM = "tpm"
    SCRAN_POOLED_SIZE_FACTORS = "scran_pooled_size_factors"
    SCT_TRANSFORM = "sctransform"
    STANDARD_SCALER = "standard_scaler"
    MIN_MAX = "min_max"
    ROBUST_SCALER = "robust_scaler"


class TransformationMethod(str, Enum):
    NONE = "none"
    LOG1P = "log1p"
    VST = "vst"
    RLOG = "rlog"
    QUANTILE_TRANSFORM = "quantile_transform"
    BOX_COX = "box_cox"


class FeatureSelectionMethod(str, Enum):
    NONE = "none"
    SELECT_K_BEST = "select_k_best"
    VARIANCE_THRESHOLD = "variance_threshold"
    HIGHLY_VARIABLE_GENES = "highly_variable_genes"
    LASSO = "lasso"
    ELASTIC_NET = "elastic_net"
    RANDOM_FOREST_IMPORTANCE = "random_forest_importance"
    RECURSIVE_FEATURE_ELIMINATION = "rfe"


class FitScope(str, Enum):
    TRAINING_ONLY = "training_only"
    FULL_DATASET = "full_dataset"  # Flawed if done before split in supervised tasks


class MLModelType(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    SPARSE_LOGISTIC_REGRESSION = "sparse_logistic_regression"
    ELASTIC_NET = "elastic_net"
    LINEAR_SVM = "linear_svm"
    RBF_SVM = "rbf_svm"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    MULTILAYER_PERCEPTRON = "mlp"
    DESEQ2 = "deseq2"
    EDGER = "edger"
    LIMMA_VOOM = "limma_voom"


class MetricType(str, Enum):
    ROC_AUC = "roc_auc"
    PR_AUC = "pr_auc"
    BALANCED_ACCURACY = "balanced_accuracy"
    F1 = "f1"
    SENSITIVITY = "sensitivity"
    SPECIFICITY = "specificity"
    BRIER_SCORE = "brier_score"
    LOG_LOSS = "log_loss"
    MSE = "mse"
    R2 = "r2"


class PreprocessingConfig(BaseModel):
    normalization: NormalizationMethod = Field(default=NormalizationMethod.NONE)
    transformation: TransformationMethod = Field(default=TransformationMethod.NONE)
    fit_scope: FitScope = Field(
        default=FitScope.TRAINING_ONLY,
        description="Must be training_only for any learned transformation"
    )


class FeatureSelectionConfig(BaseModel):
    method: FeatureSelectionMethod = Field(default=FeatureSelectionMethod.NONE)
    target_feature_count: Optional[int] = None
    fit_scope: FitScope = Field(
        default=FitScope.TRAINING_ONLY,
        description="Crucial: fitting feature selection on full dataset causes leakage"
    )


class ValidationConfig(BaseModel):
    outer_cv: SplitType = Field(description="Validation cross-validation or split strategy")
    folds: int = Field(default=5, ge=2)
    group_by: Optional[str] = Field(
        default=None,
        description="Grouping variable (e.g., animal_id, patient_id) for non-independent units"
    )
    nested_inner_cv: Optional[bool] = Field(
        default=False,
        description="Nested cross-validation for hyperparameter tuning"
    )


class InterpretabilityConfig(BaseModel):
    bootstrap_feature_stability: bool = Field(default=True)
    permutation_importance: bool = Field(default=True)
    shap_analysis: bool = Field(default=False)
    sparsity_enforced: bool = Field(default=True)


class WorkflowPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(description="Unique workflow identifier")
    assay: AssayType
    organism: str
    target: str
    prediction_task: str
    experimental_unit_level: ExperimentalUnitLevel
    split: ValidationConfig
    preprocessing: PreprocessingConfig
    feature_selection: FeatureSelectionConfig
    models: List[MLModelType]
    metrics: List[MetricType]
    interpretability: InterpretabilityConfig
    notes: Optional[str] = None

"""
Unit tests for BioReason Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from bioreason.schemas.experiment import ExperimentSpec, AssayType, ExperimentalUnitLevel, DataType, AnalysisObjective, SampleGroup
from bioreason.schemas.episode import ScientificReasoningEpisode, ScientificChecks, ScientificClaim, ClaimLevel, InterpretationSection
from bioreason.schemas.workflow import WorkflowPlan, SplitType, FitScope, MLModelType, MetricType, PreprocessingConfig, FeatureSelectionConfig, ValidationConfig, InterpretabilityConfig


def test_experiment_spec_valid():
    spec = ExperimentSpec(
        organism="Homo sapiens",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.PATIENT,
        samples=20,
        groups=[SampleGroup(name="Treated", sample_count=10), SampleGroup(name="Control", sample_count=10)],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
    )
    assert spec.organism == "Homo sapiens"
    assert spec.samples == 20


def test_experiment_spec_invalid_samples():
    with pytest.raises(ValidationError):
        ExperimentSpec(
            organism="Homo sapiens",
            assay=AssayType.BULK_RNA_SEQ,
            experimental_unit=ExperimentalUnitLevel.PATIENT,
            samples=0,  # invalid ge=1
            input_data_type=DataType.RAW_COUNTS,
            objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
        )


def test_episode_schema_claim_hierarchy():
    claim = ScientificClaim(
        statement="Gene X expression is increased in tumors.",
        level=ClaimLevel.STATISTICAL_INFERENCE,
        justification="FDR < 0.01 across 50 samples"
    )
    assert claim.level == ClaimLevel.STATISTICAL_INFERENCE


def test_workflow_plan_schema():
    wf = WorkflowPlan(
        workflow_id="WF_TEST",
        assay=AssayType.BULK_RNA_SEQ,
        organism="Mus musculus",
        target="response",
        prediction_task="classification",
        experimental_unit_level=ExperimentalUnitLevel.ANIMAL,
        split=ValidationConfig(outer_cv=SplitType.GROUPED_KFOLD, folds=5, group_by="animal_id"),
        preprocessing=PreprocessingConfig(fit_scope=FitScope.TRAINING_ONLY),
        feature_selection=FeatureSelectionConfig(fit_scope=FitScope.TRAINING_ONLY),
        models=[MLModelType.SPARSE_LOGISTIC_REGRESSION],
        metrics=[MetricType.ROC_AUC, MetricType.BALANCED_ACCURACY],
        interpretability=InterpretabilityConfig(bootstrap_feature_stability=True)
    )
    assert wf.workflow_id == "WF_TEST"
    assert wf.split.outer_cv == SplitType.GROUPED_KFOLD

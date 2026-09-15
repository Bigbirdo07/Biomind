"""
Unit tests for BioReason Pydantic schemas.
"""

from pathlib import Path
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


def test_biomarker_evidence_level_hierarchy():
    from bioreason.schemas.episode import BiomarkerEvidenceLevel
    assert BiomarkerEvidenceLevel.LEVEL_0_CANDIDATE_FEATURE.value.startswith("LEVEL_0")
    assert BiomarkerEvidenceLevel.LEVEL_3_EXTERNAL_COHORT.value.startswith("LEVEL_3")
    assert BiomarkerEvidenceLevel.LEVEL_6_CLINICAL_UTILITY.value.startswith("LEVEL_6")


def test_quality_gates_validator():
    from bioreason.validators.quality_gates import validate_episode_quality_gates, validate_benchmark_quality_gates
    from bioreason.datasets.loader import load_episode, load_benchmark_item
    
    episodes = list(Path("training_data/examples").glob("*.json"))
    if episodes:
        ep = load_episode(episodes[0])
        issues = validate_episode_quality_gates(ep)
        # Verify no fatal errors on valid dataset
        errors = [i for i in issues if i.severity == "ERROR"]
        assert len(errors) == 0

    bench_items = list(Path("benchmark/examples").glob("*.json"))
    if bench_items:
        b = load_benchmark_item(bench_items[0])
        b_issues = validate_benchmark_quality_gates(b)
        b_errors = [i for i in b_issues if i.severity == "ERROR"]
        assert len(b_errors) == 0


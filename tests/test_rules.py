"""
Unit tests for deterministic scientific rules (Phase 1).
Covers refined PSEUDO_001 semantics, POWER_001 low-replication distinction,
data leakage, batch confounding, transformation compatibility, and multiple testing.
"""

import pytest
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AssayType,
    ExperimentalUnitLevel,
    ObservationalUnitLevel,
    AnalysisUnitLevel,
    ReplicateType,
    DataType,
    AnalysisObjective,
    SampleGroup,
    BatchStructure,
)
from bioreason.schemas.workflow import (
    WorkflowPlan,
    SplitType,
    FitScope,
    MLModelType,
    MetricType,
    PreprocessingConfig,
    FeatureSelectionConfig,
    ValidationConfig,
    InterpretabilityConfig,
    FeatureSelectionMethod,
)
from bioreason.rules.pseudoreplication import PseudoreplicationRule
from bioreason.rules.statistical_power import StatisticalPowerRule
from bioreason.rules.leakage import FeatureSelectionLeakageRule, PreprocessingLeakageRule, GroupLeakageRule
from bioreason.rules.confounding import BatchConfoundingRule
from bioreason.rules.transformations import TransformationCompatibilityRule
from bioreason.rules.base import RuleSeverity


def test_pseudoreplication_case_a_1_animal_20k_cells():
    """Case A: 1 animal + 20,000 cells treated independently -> PSEUDO_001"""
    exp = ExperimentSpec(
        organism="Mus musculus",
        assay=AssayType.SINGLE_CELL_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.ANIMAL,
        observational_unit=ObservationalUnitLevel.CELL,
        analysis_unit=AnalysisUnitLevel.CELL,
        samples=2,
        groups=[
            SampleGroup(name="Diseased", sample_count=1, cell_count=20000),
            SampleGroup(name="Healthy", sample_count=1, cell_count=20000),
        ],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    rule = PseudoreplicationRule()
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "PSEUDO_001"
    assert res.severity == RuleSeverity.ERROR


def test_pseudoreplication_case_b_10_animals_10k_cells_treated_independently():
    """Case B: 10 animals + 10,000 cells each treated independently -> PSEUDO_001 exists even though biological N=10"""
    exp = ExperimentSpec(
        organism="Homo sapiens",
        assay=AssayType.SINGLE_CELL_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.PATIENT,
        observational_unit=ObservationalUnitLevel.CELL,
        analysis_unit=AnalysisUnitLevel.CELL,
        samples=10,
        groups=[
            SampleGroup(name="Disease", sample_count=5, cell_count=50000),
            SampleGroup(name="Control", sample_count=5, cell_count=50000),
        ],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    rule = PseudoreplicationRule()
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "PSEUDO_001"
    assert "100000" in res.message or "10 biological subject" in res.message


def test_pseudoreplication_case_c_10_animals_pseudobulk_passes():
    """Case C: 10 animals analyzed using animal-level pseudobulk -> No PSEUDO_001"""
    exp = ExperimentSpec(
        organism="Homo sapiens",
        assay=AssayType.SINGLE_CELL_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.PATIENT,
        observational_unit=ObservationalUnitLevel.CELL,
        analysis_unit=AnalysisUnitLevel.PSEUDOBULK_SAMPLE,
        samples=10,
        groups=[
            SampleGroup(name="Disease", sample_count=5, cell_count=50000),
            SampleGroup(name="Control", sample_count=5, cell_count=50000),
        ],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    rule = PseudoreplicationRule()
    res = rule.evaluate_experiment(exp)
    assert res.passed


def test_pseudoreplication_case_d_2_animals_power_warning_not_pseudoreplication():
    """Case D: 2 independent animals per group analyzed correctly at animal level -> POWER_001 warning, no PSEUDO_001"""
    exp = ExperimentSpec(
        organism="Mus musculus",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.ANIMAL,
        analysis_unit=AnalysisUnitLevel.ANIMAL,
        samples=4,
        groups=[
            SampleGroup(name="Treated", sample_count=2),
            SampleGroup(name="Control", sample_count=2),
        ],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    pseudo_rule = PseudoreplicationRule()
    pseudo_res = pseudo_rule.evaluate_experiment(exp)
    assert pseudo_res.passed  # NOT pseudoreplication because observations are independent animals

    power_rule = StatisticalPowerRule()
    power_res = power_rule.evaluate_experiment(exp)
    assert not power_res.passed
    assert power_res.rule_id == "POWER_001"
    assert power_res.severity == RuleSeverity.WARNING


def test_pseudoreplication_case_e_technical_replicates():
    """Case E: Technical replicates treated as biological replicates -> PSEUDO_001"""
    exp = ExperimentSpec(
        organism="Mus musculus",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.ANIMAL,
        observational_unit=ObservationalUnitLevel.TECHNICAL_REPLICATE,
        replicate_type=ReplicateType.TECHNICAL,
        samples=4,
        groups=[
            SampleGroup(name="Treated", sample_count=2, technical_replicates_per_sample=5),
            SampleGroup(name="Control", sample_count=2, technical_replicates_per_sample=5),
        ],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    rule = PseudoreplicationRule()
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "PSEUDO_001"


def test_feature_selection_leakage_rule():
    rule = FeatureSelectionLeakageRule()
    flawed_wf = WorkflowPlan(
        workflow_id="WF_FLAWED",
        assay=AssayType.BULK_RNA_SEQ,
        organism="Homo sapiens",
        target="label",
        prediction_task="classification",
        experimental_unit_level=ExperimentalUnitLevel.PATIENT,
        split=ValidationConfig(outer_cv=SplitType.STRATIFIED_KFOLD, folds=5),
        preprocessing=PreprocessingConfig(fit_scope=FitScope.TRAINING_ONLY),
        feature_selection=FeatureSelectionConfig(method=FeatureSelectionMethod.SELECT_K_BEST, fit_scope=FitScope.FULL_DATASET),
        models=[MLModelType.LOGISTIC_REGRESSION],
        metrics=[MetricType.ROC_AUC],
        interpretability=InterpretabilityConfig(),
    )
    res = rule.evaluate_workflow(flawed_wf)
    assert not res.passed
    assert res.rule_id == "LEAK_001"


def test_group_leakage_rule():
    rule = GroupLeakageRule()
    flawed_wf = WorkflowPlan(
        workflow_id="WF_GROUP_FLAW",
        assay=AssayType.SINGLE_CELL_RNA_SEQ,
        organism="Mercenaria mercenaria",
        target="neoplasia",
        prediction_task="classification",
        experimental_unit_level=ExperimentalUnitLevel.ANIMAL,
        split=ValidationConfig(outer_cv=SplitType.RANDOM_KFOLD, folds=5),
        preprocessing=PreprocessingConfig(fit_scope=FitScope.TRAINING_ONLY),
        feature_selection=FeatureSelectionConfig(method=FeatureSelectionMethod.NONE),
        models=[MLModelType.LOGISTIC_REGRESSION],
        metrics=[MetricType.ROC_AUC],
        interpretability=InterpretabilityConfig(),
    )
    res = rule.evaluate_workflow(flawed_wf)
    assert not res.passed
    assert res.rule_id == "LEAK_003"


def test_batch_confounding_rule():
    rule = BatchConfoundingRule()
    exp = ExperimentSpec(
        organism="Homo sapiens",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.PATIENT,
        samples=20,
        groups=[SampleGroup(name="A", sample_count=10), SampleGroup(name="B", sample_count=10)],
        batch_structure=BatchStructure(batch_variable="date", batch_count=2, confounded_with_group=True),
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "CONF_001"


def test_deseq2_transformation_rule():
    rule = TransformationCompatibilityRule()
    exp = ExperimentSpec(
        organism="Mus musculus",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.ANIMAL,
        samples=10,
        groups=[SampleGroup(name="A", sample_count=5), SampleGroup(name="B", sample_count=5)],
        input_data_type=DataType.TPM_FPKM_RPKM,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
    )
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "TRANS_001"

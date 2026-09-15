"""
Unit tests for deterministic scientific rules.
"""

import pytest
from bioreason.schemas.experiment import ExperimentSpec, AssayType, ExperimentalUnitLevel, DataType, AnalysisObjective, SampleGroup, BatchStructure
from bioreason.schemas.workflow import WorkflowPlan, SplitType, FitScope, MLModelType, MetricType, PreprocessingConfig, FeatureSelectionConfig, ValidationConfig, InterpretabilityConfig, FeatureSelectionMethod
from bioreason.rules.pseudoreplication import PseudoreplicationRule
from bioreason.rules.leakage import FeatureSelectionLeakageRule, PreprocessingLeakageRule, GroupLeakageRule
from bioreason.rules.confounding import BatchConfoundingRule
from bioreason.rules.transformations import TransformationCompatibilityRule
from bioreason.rules.base import RuleSeverity


def test_pseudoreplication_rule_fails_on_n1_cells():
    exp = ExperimentSpec(
        organism="Mus musculus",
        assay=AssayType.SINGLE_CELL_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.ANIMAL,
        samples=2,
        groups=[SampleGroup(name="Diseased", sample_count=1, cell_count=20000), SampleGroup(name="Healthy", sample_count=1, cell_count=20000)],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
    )
    rule = PseudoreplicationRule()
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "PSEUDO_001"
    assert res.severity == RuleSeverity.ERROR


def test_pseudoreplication_rule_passes_on_adequate_biological_n():
    exp = ExperimentSpec(
        organism="Mus musculus",
        assay=AssayType.SINGLE_CELL_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.ANIMAL,
        samples=8,
        groups=[SampleGroup(name="Diseased", sample_count=4, cell_count=10000), SampleGroup(name="Healthy", sample_count=4, cell_count=10000)],
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
    )
    rule = PseudoreplicationRule()
    res = rule.evaluate_experiment(exp)
    assert res.passed


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
        interpretability=InterpretabilityConfig()
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
        interpretability=InterpretabilityConfig()
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
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
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
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
    )
    res = rule.evaluate_experiment(exp)
    assert not res.passed
    assert res.rule_id == "TRANS_001"

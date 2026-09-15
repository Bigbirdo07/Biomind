"""
Unit tests for data contamination detection between training episodes and benchmark items.
"""

from bioreason.schemas.episode import ScientificReasoningEpisode, ScientificChecks, InterpretationSection
from bioreason.schemas.benchmark import BenchmarkItem, BenchmarkCategory, ScoringRubric, RubricCriterion
from bioreason.schemas.experiment import ExperimentSpec, AssayType, ExperimentalUnitLevel, DataType, AnalysisObjective
from bioreason.datasets.contamination import check_contamination


def test_contamination_detection_catches_duplicate():
    exp = ExperimentSpec(
        organism="Homo sapiens",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.PATIENT,
        samples=10,
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
    )
    
    train_ep = ScientificReasoningEpisode(
        episode_id="EP_TEST",
        domain="genomics",
        question="Is PCA before split valid for supervised classification?",
        experiment=exp,
        proposed_analysis="Run PCA globally then CV",
        scientific_checks=ScientificChecks(replication_valid=True, confounding_detected=False, leakage_detected=True, transformation_valid=True),
        preferred_analysis="Fit PCA inside pipeline",
        reasoning_summary="Global PCA leaks test variance",
        interpretation=InterpretationSection()
    )

    rubric = ScoringRubric(
        flaw_detection=RubricCriterion(name="flaw", key_points=["leakage"]),
        scientific_explanation=RubricCriterion(name="exp", key_points=["PCA"]),
        correction_quality=RubricCriterion(name="corr", key_points=["Pipeline"]),
        uncertainty_calibration=RubricCriterion(name="calib", key_points=["uncertainty"]),
        interpretation_quality=RubricCriterion(name="interp", key_points=["interpretation"])
    )

    bench_item = BenchmarkItem(
        item_id="BENCH_TEST",
        category=BenchmarkCategory.DATA_LEAKAGE,
        scenario="A researcher runs PCA globally before CV",
        question="Is PCA before split valid for supervised classification?",  # Exact duplicate
        flawed_analysis_present=True,
        flaw_type="leakage",
        ground_truth_rationale="PCA leaks variance",
        scoring_rubric=rubric
    )

    reports = check_contamination([train_ep], [bench_item])
    assert len(reports) == 1
    assert reports[0]["contamination_type"] == "EXACT_QUESTION_MATCH"


def test_contamination_clean_datasets():
    exp = ExperimentSpec(
        organism="Homo sapiens",
        assay=AssayType.BULK_RNA_SEQ,
        experimental_unit=ExperimentalUnitLevel.PATIENT,
        samples=10,
        input_data_type=DataType.RAW_COUNTS,
        objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION
    )
    
    train_ep = ScientificReasoningEpisode(
        episode_id="EP_CLEAN",
        domain="genomics",
        question="What is the effect of batch confounding in RNA-seq?",
        experiment=exp,
        proposed_analysis="Unbalanced batch sequencing",
        scientific_checks=ScientificChecks(replication_valid=True, confounding_detected=True, leakage_detected=False, transformation_valid=True),
        preferred_analysis="Balanced randomized block design",
        reasoning_summary="Collinear batch prevents biological attribution",
        interpretation=InterpretationSection()
    )

    rubric = ScoringRubric(
        flaw_detection=RubricCriterion(name="flaw", key_points=["leakage"]),
        scientific_explanation=RubricCriterion(name="exp", key_points=["PCA"]),
        correction_quality=RubricCriterion(name="corr", key_points=["Pipeline"]),
        uncertainty_calibration=RubricCriterion(name="calib", key_points=["uncertainty"]),
        interpretation_quality=RubricCriterion(name="interp", key_points=["interpretation"])
    )

    bench_item = BenchmarkItem(
        item_id="BENCH_CLEAN",
        category=BenchmarkCategory.DATA_LEAKAGE,
        scenario="Single cell clam neoplasia evaluation",
        question="Why does random cell splitting cause high CV AUC but low test AUC in bivalve tumors?",
        flawed_analysis_present=True,
        flaw_type="group_leakage",
        ground_truth_rationale="Clam animal profile leakage",
        scoring_rubric=rubric
    )

    reports = check_contamination([train_ep], [bench_item])
    assert len(reports) == 0

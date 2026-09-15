"""
Unit tests for evaluation harness, rubric scoring, difficulty tracking, and critical failure metrics (Phase 1).
"""

from bioreason.schemas.benchmark import BenchmarkItem, BenchmarkCategory, DifficultyLevel, ScoringRubric, RubricCriterion
from bioreason.models.mock_adapter import MockModelAdapter
from bioreason.evaluation.harness import BioReasonEvaluationHarness
from bioreason.evaluation.rubric import ScientificRubricScorer


def test_rubric_scorer_and_harness_with_critical_failure():
    rubric = ScoringRubric(
        flaw_detection=RubricCriterion(name="flaw", key_points=["methodological flaw", "violates"]),
        scientific_explanation=RubricCriterion(name="exp", key_points=["statistical", "assumptions"]),
        correction_quality=RubricCriterion(name="corr", key_points=["proper", "pipelines"]),
        uncertainty_calibration=RubricCriterion(name="calib", key_points=["external cohort", "validation"]),
        interpretation_quality=RubricCriterion(name="interp", key_points=["causality", "association"])
    )

    bench_item = BenchmarkItem(
        item_id="BENCH_EVAL_TEST",
        difficulty=DifficultyLevel.ADVANCED,
        category=BenchmarkCategory.DATA_LEAKAGE,
        scenario="Global PCA applied prior to cross validation",
        question="Is this cross-validation valid?",
        flawed_analysis_present=True,
        flaw_type="detected_methodological_flaw",
        ground_truth_rationale="Global PCA leaks test fold variance",
        scoring_rubric=rubric
    )

    # Oracle adapter (detects flaw)
    oracle_adapter = MockModelAdapter(mode="oracle")
    oracle_harness = BioReasonEvaluationHarness(adapter=oracle_adapter)
    oracle_res = oracle_harness.evaluate_benchmark([bench_item])

    assert oracle_res["aggregate_metrics"]["total_items"] == 1
    assert oracle_res["aggregate_metrics"]["flaw_detection_accuracy"] == 1.0
    assert oracle_res["aggregate_metrics"]["critical_failure_rate"] == 0.0
    assert oracle_res["aggregate_metrics"]["by_difficulty"]["ADVANCED"]["count"] == 1

    # Naive adapter (misses flaw -> triggers critical failure)
    naive_adapter = MockModelAdapter(mode="naive")
    naive_harness = BioReasonEvaluationHarness(adapter=naive_adapter)
    naive_res = naive_harness.evaluate_benchmark([bench_item])

    assert naive_res["aggregate_metrics"]["flaw_detection_accuracy"] == 0.0
    assert naive_res["aggregate_metrics"]["critical_failure_rate"] == 1.0
    assert naive_res["aggregate_metrics"]["total_critical_failures"] == 1

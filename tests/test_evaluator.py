"""
Unit tests for evaluation harness and rubric scoring.
"""

from bioreason.schemas.benchmark import BenchmarkItem, BenchmarkCategory, ScoringRubric, RubricCriterion
from bioreason.models.mock_adapter import MockModelAdapter
from bioreason.evaluation.harness import BioReasonEvaluationHarness
from bioreason.evaluation.rubric import ScientificRubricScorer


def test_rubric_scorer_and_harness():
    rubric = ScoringRubric(
        flaw_detection=RubricCriterion(name="flaw", key_points=["methodological flaw", "violates"]),
        scientific_explanation=RubricCriterion(name="exp", key_points=["statistical", "assumptions"]),
        correction_quality=RubricCriterion(name="corr", key_points=["proper", "pipelines"]),
        uncertainty_calibration=RubricCriterion(name="calib", key_points=["external cohort", "validation"]),
        interpretation_quality=RubricCriterion(name="interp", key_points=["causality", "association"])
    )

    bench_item = BenchmarkItem(
        item_id="BENCH_EVAL_TEST",
        category=BenchmarkCategory.DATA_LEAKAGE,
        scenario="Global PCA applied prior to cross validation",
        question="Is this cross-validation valid?",
        flawed_analysis_present=True,
        flaw_type="detected_methodological_flaw",
        ground_truth_rationale="Global PCA leaks test fold variance",
        scoring_rubric=rubric
    )

    adapter = MockModelAdapter(mode="oracle")
    harness = BioReasonEvaluationHarness(adapter=adapter)
    res = harness.evaluate_benchmark([bench_item])

    assert res["aggregate_metrics"]["total_items"] == 1
    assert res["aggregate_metrics"]["flaw_detection_accuracy"] == 1.0
    assert res["aggregate_metrics"]["mean_composite_score"] > 0.5

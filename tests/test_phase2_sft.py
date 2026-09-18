"""
Tests for Phase 2 SFT training pipeline, quality tiers, response formatting, and evaluation metrics.
"""

from pathlib import Path
from bioreason.schemas.episode import (
    ScientificReasoningEpisode,
    ValidationStatus,
    EpisodeType,
    ScientificChecks,
    InterpretationSection,
)
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AssayType,
    ExperimentalUnitLevel,
    DataType,
    AnalysisObjective,
)
from bioreason.schemas.benchmark import (
    BenchmarkItem,
    BenchmarkCategory,
    DifficultyLevel,
    ScoringRubric,
    RubricCriterion,
    ExpectedDecision,
)
from bioreason.models.base import ModelPrediction
from bioreason.evaluation.rubric import ScientificRubricScorer
from bioreason.training.config import TrainingConfig, PeftMethod
from bioreason.training.sft_trainer import (
    ScientificSFTTrainer,
    assign_quality_tier,
    format_episode_to_bioreason_schema,
    format_episode_to_instruction,
)


def create_sample_episode(status=ValidationStatus.EXPERT_VALIDATED, is_flawed=True) -> ScientificReasoningEpisode:
    return ScientificReasoningEpisode(
        episode_id="TEST_EP_001",
        episode_type=EpisodeType.FLAWED_WORKFLOW if is_flawed else EpisodeType.CORRECT_WORKFLOW,
        domain="single_cell_transcriptomics",
        question="Is treating 10,000 cells from 1 mouse as independent valid?",
        experiment=ExperimentSpec(
            organism="Mus musculus",
            assay=AssayType.SINGLE_CELL_RNA_SEQ,
            experimental_unit=ExperimentalUnitLevel.ANIMAL,
            samples=1,
            total_observations=10000,
            input_data_type=DataType.RAW_COUNTS,
            objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION,
        ),
        proposed_analysis="Treat each of the 10,000 cells as independent samples in a standard two-sample t-test.",
        scientific_checks=ScientificChecks(
            replication_valid=not is_flawed,
            confounding_detected=False,
            leakage_detected=False,
            transformation_valid=True,
            multiple_testing_controlled=True,
            sample_size_adequate=True,
        ),
        preferred_analysis="Aggregate cells by donor to create pseudobulk counts or use a mixed-effects model (GLMM).",
        reasoning_summary="Single cells from the same animal share unmodeled correlation; treating them as independent is pseudoreplication.",
        interpretation=InterpretationSection(
            supported_claims=[],
            unsupported_claims=[],
            limitations=["Single animal limits generalizability"],
        ),
        validation_status=status,
    )


def test_quality_tier_assignment():
    ep_a = create_sample_episode(status=ValidationStatus.EXPERT_VALIDATED)
    ep_b = create_sample_episode(status=ValidationStatus.SCIENTIST_REVIEWED)
    ep_c = create_sample_episode(status=ValidationStatus.AUTO_VALIDATED)

    assert assign_quality_tier(ep_a) == "TIER_A"
    assert assign_quality_tier(ep_b) == "TIER_B"
    assert assign_quality_tier(ep_c) == "TIER_C"


def test_format_episode_to_bioreason_schema():
    flawed_ep = create_sample_episode(is_flawed=True)
    schema_output = format_episode_to_bioreason_schema(flawed_ep)

    assert "assessment" in schema_output
    assert "experimental_unit" in schema_output
    assert "identified_issues" in schema_output
    assert "recommended_analysis" in schema_output
    assert "confidence" in schema_output
    assert schema_output["experimental_unit"] == "animal"
    assert len(schema_output["identified_issues"]) > 0
    assert schema_output["identified_issues"][0]["severity"] == "CRITICAL"

    # Test valid workflow case (teaches "NO ERROR")
    valid_ep = create_sample_episode(is_flawed=False)
    valid_schema = format_episode_to_bioreason_schema(valid_ep)
    assert len(valid_schema["identified_issues"]) == 0
    assert "No major methodological flaw is apparent" in valid_schema["assessment"]


def test_rubric_false_alarm_and_actionability():
    scorer = ScientificRubricScorer()
    
    # Create valid benchmark item
    valid_item = BenchmarkItem(
        item_id="BENCH_SOUND_001",
        category=BenchmarkCategory.STATISTICAL_REASONING,
        difficulty=DifficultyLevel.INTERMEDIATE,
        scenario="A researcher performs PCA on the training set only inside each cross-validation fold.",
        question="Is this pipeline valid?",
        flawed_analysis_present=False,
        ground_truth_rationale="The workflow is sound because preprocessing is strictly encapsulated inside CV folds.",
        scoring_rubric=ScoringRubric(
            flaw_detection=RubricCriterion(name="flaw_detection", weight=1.0, key_points=["valid", "no flaw"]),
            scientific_explanation=RubricCriterion(name="scientific_explanation", weight=1.0, key_points=["cross-validation", "fold"]),
            correction_quality=RubricCriterion(name="correction_quality", weight=1.0, key_points=["maintain", "pipeline"]),
            uncertainty_calibration=RubricCriterion(name="uncertainty_calibration", weight=1.0, key_points=["cautious"]),
            interpretation_quality=RubricCriterion(name="interpretation_quality", weight=1.0, key_points=["generalization"]),
        ),
        expected_decision=ExpectedDecision(primary_issue="none", acceptable_methods=["nested CV"]),
    )

    # 1. Prediction correctly detects no flaw -> false_alarm = False
    good_pred = ModelPrediction(
        item_id="BENCH_SOUND_001",
        prompt="Evaluate PCA pipeline",
        raw_response="No flaw detected. Analysis is valid.",
        flaw_detected=False,
        identified_issues=[],
        primary_assessment="The analysis is methodologically valid.",
        proposed_correction="No changes needed.",
        confidence="HIGH",
    )
    score_good = scorer.evaluate_prediction(valid_item, good_pred)
    assert score_good.false_alarm is False
    assert score_good.flaw_detected_binary is True

    # 2. Prediction incorrectly hallucinates a flaw -> false_alarm = True
    alarmist_pred = ModelPrediction(
        item_id="BENCH_SOUND_001",
        prompt="Evaluate PCA pipeline",
        raw_response="Critical error: PCA violates independence. Place SelectKBest inside the cross-validation pipeline within fold.",
        flaw_detected=True,
        identified_issues=["Severe data leakage during PCA"],
        primary_assessment="Critical error: PCA violates independence.",
        proposed_correction="Place SelectKBest inside the cross-validation pipeline within fold.",
        confidence="HIGH",
    )
    score_alarmist = scorer.evaluate_prediction(valid_item, alarmist_pred)
    assert score_alarmist.false_alarm is True
    assert score_alarmist.flaw_detected_binary is False
    assert score_alarmist.correction_actionability_score > 0.0



def test_smoke_sft_trainer_pipeline(tmp_path):
    config = TrainingConfig(
        experiment_name="TEST-SMOKE-001",
        model_name_or_path="Qwen/Qwen2.5-14B-Instruct",
        output_dir=str(tmp_path / "smoke_out"),
        train_dataset_path="training_data/snapshots/bioreasontrain_sft_v0.1/train",
        validation_split_path="training_data/snapshots/bioreasontrain_sft_v0.1/val",
        peft_method=PeftMethod.LORA,
        learning_rate=0.0002,
    )
    trainer = ScientificSFTTrainer(config)
    res = trainer.train_smoke_test(num_examples=10)

    assert res["status"] == "smoke_training_successful"
    assert res["samples_trained"] == 10
    assert res["final_loss"] < res["initial_loss"]
    assert Path(res["checkpoint_dir"]).exists()
    assert (Path(res["checkpoint_dir"]) / "adapter_config.json").exists()
    assert (Path(res["checkpoint_dir"]) / "adapter_metadata.json").exists()
    assert Path(res["manifest_path"]).exists()

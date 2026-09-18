import json
import pytest
from pathlib import Path
from bioreason.schemas.preference import (
    BioReasonPreferencePair,
    PreferenceCategory,
    ScientificSeverity,
    PreferenceReviewStatus,
    format_dpo_pair,
)
from bioreason.training.dpo_trainer import DPOConfig, ScientificDPOTrainer
from bioreason.datasets.loader import load_benchmark_from_dir
from bioreason.datasets.contamination import check_contamination, normalize_text
from bioreason.datasets.loader import load_benchmark_from_dir


def test_preference_schema_validation():
    pair = BioReasonPreferencePair(
        preference_id="PREF-TEST-001",
        prompt="Analyze the single-cell RNA-seq experimental design.",
        preferred_response={
            "assessment": "Pseudoreplication is present.",
            "recommended_analysis": "Use pseudobulk with DESeq2."
        },
        rejected_response={
            "assessment": "No flaw.",
            "recommended_analysis": "Perform Wilcoxon rank-sum test across 50,000 cells directly."
        },
        preference_reason="Preferred response detects pseudoreplication and provides actionable pseudobulk advice.",
        category=PreferenceCategory.ACTIONABLE_VS_VAGUE_CORRECTION,
        error_taxonomy=["MISSED_PSEUDOREPLICATION", "WEAK_CORRECTION"],
        scientific_severity=ScientificSeverity.CRITICAL,
        domain="scRNA-seq",
        source="phase2b_residual_audit",
        review_status=PreferenceReviewStatus.EXPERT_VERIFIED,
        parent_episode_ids=["EP-001"]
    )
    assert pair.preference_id == "PREF-TEST-001"
    assert pair.scientific_severity == ScientificSeverity.CRITICAL
    assert len(pair.error_taxonomy) == 2

    # Test formatted DPO output
    dpo_formatted = format_dpo_pair(pair)
    assert dpo_formatted["prompt"] == pair.prompt
    assert "Pseudoreplication is present." in dpo_formatted["chosen"]
    assert "Wilcoxon rank-sum" in dpo_formatted["rejected"]


def test_preference_dataset_contamination_against_benchmark():
    pref_file = Path("training_data/preferences/bioreason_preference_v0.1/preferences.jsonl")
    assert pref_file.exists()

    # Load dev benchmark items
    dev_items = load_benchmark_from_dir(Path("benchmark/frozen/bioreasonbench_v0.1/dev"))
    # Load locked test items (without looking at their answers)
    locked_items = load_benchmark_from_dir(Path("benchmark/frozen/bioreasonbench_v0.1/final_test"))

    all_bench_texts = [normalize_text(item.scenario) for item in dev_items + locked_items]

    # Verify zero preference prompts are identical or contaminated with benchmark scenarios
    with open(pref_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            pair_dict = json.loads(line)
            prompt_norm = normalize_text(pair_dict["prompt"])
            for bench_text in all_bench_texts:
                assert prompt_norm != bench_text, "Direct prompt collision detected!"


def test_dpo_smoke_trainer_pipeline(tmp_path):
    cfg = DPOConfig(
        sft_checkpoint_path="outputs/BR-SFT-001-A/checkpoint-epoch-2.0",
        preference_dataset_path="training_data/preferences/bioreason_preference_v0.1/preferences.jsonl",
        output_dir=str(tmp_path / "dpo_test_output"),
        beta=0.1,
        learning_rate=1e-5,
        num_epochs=1,
        batch_size=4
    )

    trainer = ScientificDPOTrainer(cfg)
    result = trainer.train_smoke_test(num_pairs=20)

    assert result["status"] == "dpo_smoke_successful"
    assert result["pairs_trained"] == 20
    assert result["final_loss"] < result["initial_loss"]
    assert result["final_margin"] > 0
    assert Path(result["checkpoint_dir"]).exists()


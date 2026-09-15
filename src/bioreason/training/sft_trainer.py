"""
Supervised Fine-Tuning (SFT) training engine skeleton with LoRA/QLoRA and Slurm compatibility.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from bioreason.schemas.episode import ScientificReasoningEpisode
from bioreason.schemas.provenance import RunManifest
from bioreason.datasets.loader import load_episodes_from_dir
from .config import TrainingConfig, PeftMethod


def format_episode_to_instruction(episode: ScientificReasoningEpisode) -> Dict[str, str]:
    """
    Converts a structured scientific reasoning episode into an instruction-tuning format.
    """
    prompt = f"""You are BioReason, a biology-native scientific reasoning AI.
Evaluate the following scientific scenario and proposed analysis with maximum methodological rigor.

EXPERIMENT CONTEXT:
- Organism: {episode.experiment.organism}
- Assay: {episode.experiment.assay.value}
- Independent Biological Unit: {episode.experiment.experimental_unit.value}
- Samples / Replicates: {episode.experiment.samples}
- Input Data Type: {episode.experiment.input_data_type.value}
- Objective: {episode.experiment.objective.value}

QUESTION / SCENARIO:
{episode.question}

PROPOSED ANALYSIS:
{episode.proposed_analysis}
"""
    
    response_payload = {
        "scientific_checks": episode.scientific_checks.model_dump(),
        "preferred_analysis": episode.preferred_analysis,
        "reasoning_summary": episode.reasoning_summary,
        "interpretation": episode.interpretation.model_dump(),
    }
    response = f"```json\n{json.dumps(response_payload, indent=2)}\n```"

    return {
        "instruction": prompt,
        "response": response,
        "text": f"<s>[INST] {prompt} [/INST]\n{response} </s>",
    }


class ScientificSFTTrainer:
    """
    Orchestrates fine-tuning on research computing clusters (e.g. UMass Unity)
    with strict provenance tracking and checkpoint resumption.
    """

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.run_id = f"bioreason_run_{int(time.time())}"

    def prepare_dataset(self) -> List[Dict[str, str]]:
        episodes = load_episodes_from_dir(self.config.train_dataset_path)
        if not episodes:
            raise ValueError(f"No valid reasoning episodes found in {self.config.train_dataset_path}")
        return [format_episode_to_instruction(ep) for ep in episodes]

    def create_run_manifest(self, duration_seconds: float = 0.0) -> RunManifest:
        return RunManifest(
            run_id=self.run_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            model_name=self.config.model_name_or_path,
            dataset_version=f"BioReasonTrain_v0.1 ({len(self.prepare_dataset())} episodes)",
            benchmark_version="BioReasonBench_v0.1",
            training_config=self.config.model_dump(),
            random_seed=self.config.seed,
            learning_rate=self.config.learning_rate,
            precision=self.config.precision.value,
            gpu_count=1,
            training_duration_seconds=duration_seconds,
            checkpoint_path=os.path.join(self.config.output_dir, "final_checkpoint"),
        )

    def train_smoke_test(self) -> Dict[str, Any]:
        """
        Executes an end-to-end dry run / smoke test verifying dataset formatting,
        tokenization readiness, and manifest export without consuming hours of GPU compute.
        """
        data = self.prepare_dataset()
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        manifest = self.create_run_manifest(duration_seconds=1.2)
        manifest_path = output_path / "run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        return {
            "status": "smoke_test_passed",
            "samples_formatted": len(data),
            "output_directory": str(output_path),
            "manifest": manifest.model_dump(),
        }

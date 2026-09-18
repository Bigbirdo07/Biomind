"""
Configuration schemas for LoRA/QLoRA supervised fine-tuning and HPC execution.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PeftMethod(str, Enum):
    LORA = "lora"
    QLORA = "qlora"
    FULL = "full"


class PrecisionType(str, Enum):
    BF16 = "bf16"
    FP16 = "fp16"
    FP32 = "fp32"


class LoraConfigSpec(BaseModel):
    r: int = Field(default=16, description="LoRA attention dimension rank")
    lora_alpha: int = Field(default=32, description="LoRA scaling alpha")
    lora_dropout: float = Field(default=0.05, description="LoRA dropout rate")
    target_modules: List[str] = Field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Experiment identifier and metadata
    experiment_name: str = Field(default="BR-SFT-001-A", description="Unique stable experiment name (e.g. BR-SFT-001-A)")
    
    # Model and paths
    model_name_or_path: str = Field(default="Qwen/Qwen2.5-14B-Instruct")
    output_dir: str = Field(default="outputs/BR-SFT-001-A")
    train_dataset_path: str = Field(default="training_data/snapshots/bioreasontrain_sft_v0.1/train")
    validation_split_path: Optional[str] = Field(default="training_data/snapshots/bioreasontrain_sft_v0.1/val")
    eval_benchmark_path: Optional[str] = Field(default="benchmark/frozen/bioreasonbench_v0.1/dev")
    snapshot_manifest_path: Optional[str] = Field(default="training_data/snapshots/bioreasontrain_sft_v0.1/manifest.json")

    # Quality Tiers and Example Weighting
    selected_tiers: List[str] = Field(
        default_factory=lambda: ["TIER_A", "TIER_B", "TIER_C"],
        description="Allowed quality tiers to include in training"
    )
    tier_weights: Dict[str, float] = Field(
        default_factory=lambda: {"TIER_A": 1.0, "TIER_B": 1.0, "TIER_C": 0.70, "TIER_D": 0.0},
        description="Configurable loss sample weights per quality tier"
    )

    # Training parameters
    peft_method: PeftMethod = Field(default=PeftMethod.LORA)
    lora: LoraConfigSpec = Field(default_factory=LoraConfigSpec)
    precision: PrecisionType = Field(default=PrecisionType.BF16)
    
    num_train_epochs: int = Field(default=3, ge=1)
    per_device_train_batch_size: int = Field(default=2, ge=1)
    per_device_eval_batch_size: int = Field(default=2, ge=1)
    gradient_accumulation_steps: int = Field(default=8, ge=1)
    learning_rate: float = Field(default=2e-4, gt=0.0)
    warmup_ratio: float = Field(default=0.05, ge=0.0, le=1.0)
    weight_decay: float = Field(default=0.01, ge=0.0)
    max_seq_length: int = Field(default=2048, ge=256)
    seed: int = Field(default=42)

    # Checkpointing & Resumption
    save_strategy: str = "epoch"
    save_total_limit: int = 3
    logging_steps: int = 10
    resume_from_checkpoint: Optional[str] = None

    # Distributed & Hardware
    deepspeed_config: Optional[str] = None
    gradient_checkpointing: bool = True


"""
Verified BioReason DPO training path.

Intentionally separate from the historical simulation module
(src/bioreason/training/dpo_trainer.py, flagged in
simulation_archives/NOT_FOR_EMPIRICAL_TRAINING.md). This module performs
real model loading, real TRL DPOTrainer forward/backward passes, PEFT LoRA
checkpointing on top of a resumed verified SFT adapter, and physical
checkpoint integrity verification — mirroring
src/bioreason/training/verified_sft_trainer.py's pattern exactly.

Reuses shared utilities from verified_sft_trainer.py (hashing, git info,
environment manifest, checkpoint integrity, checkpoint archiving) rather
than duplicating them.
"""

from __future__ import annotations

import inspect
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .verified_sft_trainer import (
    archive_checkpoint,
    assert_valid_peft_checkpoint,
    checkpoint_integrity,
    collect_environment_manifest,
    get_git_info,
    read_jsonl,
    sha256_file,
    write_json,
)


@dataclass
class VerifiedDPOConfig:
    run_id: str = "BR-VERIFIED-DPO-001"
    base_model_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    base_model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    parent_adapter_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-002"
    train_file: str = "training_data/preferences/BioReasonPreference-Verified-DPO-v0.1/train.jsonl"
    val_file: str = "training_data/preferences/BioReasonPreference-Verified-DPO-v0.1/val.jsonl"
    output_dir: str = "outputs/verified_training/BR-VERIFIED-DPO-001"
    durable_archive_dir: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-DPO-001"
    max_seq_length: int = 1024
    max_prompt_length: int = 512
    num_train_epochs: float = 3.0
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 2  # small (17-pair) train set: keep steps/epoch meaningful rather than collapsing to ~2 optimizer steps total
    learning_rate: float = 5e-6
    beta: float = 0.1
    weight_decay: float = 0.0
    warmup_ratio: float = 0.10
    logging_steps: int = 1
    save_strategy: str = "epoch"
    eval_strategy: str = "epoch"
    save_total_limit: int = 3
    seed: int = 42
    bf16: bool = True
    gradient_checkpointing: bool = True


def load_dpo_dataset(path: Path):
    from datasets import Dataset

    rows = read_jsonl(path)
    return Dataset.from_list(
        [{"prompt": r["prompt"], "chosen": r["chosen"], "rejected": r["rejected"]} for r in rows]
    )


def train_verified_dpo(config: VerifiedDPOConfig) -> Dict[str, Any]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = collect_environment_manifest(output_dir)

    base = Path(config.base_model_path)
    if not (base / "config.json").exists():
        raise FileNotFoundError(f"Base model config not found: {base}")

    parent_adapter = Path(config.parent_adapter_path)
    assert_valid_peft_checkpoint(parent_adapter)
    parent_adapter_sha256 = sha256_file(parent_adapter / "adapter_model.safetensors")

    train_path = Path(config.train_file)
    val_path = Path(config.val_file)

    pre_manifest = {
        "run_id": config.run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": get_git_info(),
        "base_model_name": config.base_model_name,
        "base_model_snapshot": str(base),
        "parent_adapter_path": str(parent_adapter),
        "parent_adapter_sha256": parent_adapter_sha256,
        "train_file": config.train_file,
        "train_file_sha256": sha256_file(train_path),
        "val_file": config.val_file,
        "val_file_sha256": sha256_file(val_path),
        "config": asdict(config),
        "environment": env,
    }
    write_json(output_dir / "BIOREASON_DPO_VERIFIED_PRE_RUN_MANIFEST.json", pre_manifest)

    tokenizer = AutoTokenizer.from_pretrained(str(base), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if config.bf16 else torch.float16

    # Single-model-copy design (memory-efficient, robust to smaller GPUs):
    # merge SFT-002's adapter into the base ONCE, producing a plain model
    # whose weights already equal SFT-002's behavior. A fresh LoRA adapter
    # is then trained on top of this merged base for DPO. ref_model=None is
    # passed to DPOTrainer, which (per TRL's standard PEFT pattern) computes
    # reference log-probs by temporarily disabling the active adapter --
    # since the underlying base IS the merged SFT-002 weights, this gives
    # exactly SFT-002's reference behavior without loading a second full
    # 14B-parameter model copy. (An earlier version of this function loaded
    # two independent full model copies -- policy and reference -- which
    # required ~60GB+ VRAM and caused a real CUDA OOM on a 44GB GPU node;
    # this design uses roughly half that memory.)
    merged_base = AutoModelForCausalLM.from_pretrained(
        str(base), torch_dtype=dtype, device_map=None, trust_remote_code=True,
    )
    merged_base = PeftModel.from_pretrained(merged_base, str(parent_adapter), is_trainable=False)
    merged_base = merged_base.merge_and_unload()
    if config.gradient_checkpointing:
        merged_base.gradient_checkpointing_enable()
        merged_base.config.use_cache = False

    from peft import LoraConfig, get_peft_model

    # Read the parent adapter's LoRA hyperparameters so the new DPO adapter
    # matches its rank/alpha/target_modules, for a fair, comparable run.
    parent_config_json = json.loads((parent_adapter / "adapter_config.json").read_text())
    lora_cfg = LoraConfig(
        r=parent_config_json["r"],
        lora_alpha=parent_config_json["lora_alpha"],
        lora_dropout=parent_config_json.get("lora_dropout", 0.05),
        target_modules=parent_config_json["target_modules"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    policy_model = get_peft_model(merged_base, lora_cfg)

    active_peft_config = next(iter(policy_model.peft_config.values()))
    trainable_params, total_params = policy_model.get_nb_trainable_parameters()
    trainable_report = {
        "total_parameters": int(total_params),
        "trainable_parameters": int(trainable_params),
        "trainable_percent": float(trainable_params / total_params * 100),
        "lora_r": active_peft_config.r,
        "lora_alpha": active_peft_config.lora_alpha,
        "target_modules": sorted(active_peft_config.target_modules),
        "base_is_merged_from_adapter": str(parent_adapter),
        "note": "policy = fresh LoRA on top of merged parent weights; "
                "reference = same model with this fresh adapter disabled "
                "(equivalent to the merged parent, i.e. SFT-002 behavior)",
    }
    write_json(output_dir / "trainable_parameters.json", trainable_report)
    policy_model.print_trainable_parameters()

    ref_model = None  # DPOTrainer will use the policy model with its adapter disabled

    train_ds = load_dpo_dataset(train_path)
    val_ds = load_dpo_dataset(val_path)

    args_kwargs = {
        "output_dir": str(output_dir),
        "num_train_epochs": config.num_train_epochs,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "per_device_eval_batch_size": config.per_device_eval_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "learning_rate": config.learning_rate,
        "beta": config.beta,
        "weight_decay": config.weight_decay,
        "warmup_ratio": config.warmup_ratio,
        "logging_steps": config.logging_steps,
        "save_strategy": config.save_strategy,
        "save_total_limit": config.save_total_limit,
        "bf16": config.bf16,
        "fp16": False,
        "seed": config.seed,
        "report_to": [],
        "lr_scheduler_type": "cosine",
        "gradient_checkpointing": config.gradient_checkpointing,
        "max_length": config.max_seq_length,
        "max_prompt_length": config.max_prompt_length,
        "bf16_full_eval": config.bf16,
    }
    signature = inspect.signature(DPOConfig.__init__)
    valid_params = set(signature.parameters.keys())
    if "eval_strategy" in valid_params:
        args_kwargs["eval_strategy"] = config.eval_strategy
    elif "evaluation_strategy" in valid_params:
        args_kwargs["evaluation_strategy"] = config.eval_strategy
    # Drop any kwarg this TRL version's DPOConfig doesn't accept, rather than
    # crashing — different TRL releases have renamed / removed a few of
    # these fields over time.
    args_kwargs = {k: v for k, v in args_kwargs.items() if k in valid_params}
    args = DPOConfig(**args_kwargs)

    trainer_kwargs = {
        "model": policy_model,
        "ref_model": ref_model,
        "args": args,
        "train_dataset": train_ds,
        "eval_dataset": val_ds,
    }
    trainer_signature = inspect.signature(DPOTrainer.__init__)
    trainer_params = set(trainer_signature.parameters.keys())
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer

    trainer = DPOTrainer(**trainer_kwargs)

    start = time.time()
    result = trainer.train()
    metrics = trainer.evaluate()
    duration = time.time() - start

    final_dir = output_dir / "final_adapter"
    trainer.model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    assert_valid_peft_checkpoint(final_dir)

    integrity = checkpoint_integrity(output_dir)
    integrity["final_adapter"] = {
        "path": str(final_dir),
        "adapter_model_size_bytes": (final_dir / "adapter_model.safetensors").stat().st_size,
        "adapter_model_sha256": sha256_file(final_dir / "adapter_model.safetensors"),
        "adapter_config_sha256": sha256_file(final_dir / "adapter_config.json"),
    }
    write_json(output_dir / "checkpoint_integrity.json", {"checkpoints": integrity})

    archive = archive_checkpoint(final_dir, Path(config.durable_archive_dir))
    run_manifest = {
        "run_id": config.run_id,
        "status": "VERIFIED_DPO_TRAINING_COMPLETE",
        "duration_seconds": duration,
        "parent_adapter_path": str(parent_adapter),
        "parent_adapter_sha256": parent_adapter_sha256,
        "train_result": result.metrics,
        "eval_metrics": metrics,
        "trainable_parameters": trainable_report,
        "checkpoints": integrity,
        "selected_checkpoint": str(final_dir),
        "durable_archive": archive,
    }
    write_json(output_dir / "run_manifest.json", run_manifest)
    return run_manifest

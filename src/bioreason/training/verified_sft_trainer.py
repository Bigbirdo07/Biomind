"""
Verified BioReason SFT training path.

This module is intentionally separate from the historical simulation/report
scripts. It performs real model loading, tokenization, forward/backward passes
through Hugging Face Trainer, PEFT LoRA checkpointing, and checkpoint integrity
verification.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
import inspect
from typing import Any, Dict, List, Optional


SYSTEM_PROMPT = (
    "You are BioReason, a biology-native scientific reasoning AI. "
    "Evaluate biological, statistical, and computational workflows rigorously, "
    "but answer conversationally when the user asks a general question."
)


@dataclass
class VerifiedSFTConfig:
    run_id: str = "BR-VERIFIED-SFT-001"
    base_model_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    base_model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    train_file: str = "training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/train.jsonl"
    val_file: str = "training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/val.jsonl"
    output_dir: str = "outputs/verified_training/BR-VERIFIED-SFT-001"
    max_seq_length: int = 2048
    num_train_epochs: float = 2.0
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_ratio: float = 0.10
    logging_steps: int = 5
    save_strategy: str = "epoch"
    eval_strategy: str = "epoch"
    save_total_limit: int = 4
    seed: int = 42
    bf16: bool = True
    gradient_checkpointing: bool = True
    lora_r: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    durable_archive_dir: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-001"
    train_format: str = "legacy_episode"  # "legacy_episode" (SFT-001, frozen) or "messages" (SFT-002+)
    assistant_only_label_masking: bool = False  # must be True for train_format == "messages"
    resume_adapter_path: Optional[str] = None  # continue training an existing verified adapter instead of a fresh LoRA


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def get_git_info() -> Dict[str, str]:
    def run(cmd: List[str]) -> str:
        try:
            return subprocess.check_output(cmd, text=True).strip()
        except Exception:
            return "UNKNOWN"

    return {
        "commit": run(["git", "rev-parse", "HEAD"]),
        "branch": run(["git", "branch", "--show-current"]),
        "status_short": run(["git", "status", "--short"]),
    }


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def format_episode_prompt(ep: Dict[str, Any]) -> str:
    exp = ep.get("experiment", {})
    return (
        "Evaluate the following scientific scenario and proposed analysis.\n\n"
        f"Organism: {exp.get('organism', 'UNKNOWN')}\n"
        f"Assay: {exp.get('assay', 'UNKNOWN')}\n"
        f"Experimental unit: {exp.get('experimental_unit', 'UNKNOWN')}\n"
        f"Samples: {exp.get('samples', 'UNKNOWN')}\n"
        f"Input data type: {exp.get('input_data_type', 'UNKNOWN')}\n"
        f"Objective: {exp.get('objective', 'UNKNOWN')}\n\n"
        f"Question:\n{ep.get('question', '')}\n\n"
        f"Proposed analysis:\n{ep.get('proposed_analysis', '')}"
    )


def format_episode_response(ep: Dict[str, Any]) -> str:
    checks = ep.get("scientific_checks", {})
    flawed = not all(
        [
            checks.get("replication_valid", True),
            not checks.get("confounding_detected", False),
            not checks.get("leakage_detected", False),
            checks.get("transformation_valid", True),
            checks.get("multiple_testing_controlled", True),
            checks.get("sample_size_adequate", True),
        ]
    )
    payload = {
        "assessment": ep.get("reasoning_summary") or ep.get("preferred_analysis") or "Assessment unavailable.",
        "flaw_detected": flawed,
        "experimental_unit": ep.get("experiment", {}).get("experimental_unit", "UNKNOWN"),
        "identified_issues": [],
        "recommended_analysis": ep.get("preferred_analysis", ""),
        "supported_claims": [c.get("statement", "") for c in ep.get("interpretation", {}).get("supported_claims", [])],
        "unsupported_claims": [c.get("statement", "") for c in ep.get("interpretation", {}).get("unsupported_claims", [])],
        "limitations": ep.get("interpretation", {}).get("limitations", []),
        "confidence": "HIGH",
    }
    if flawed:
        if not checks.get("replication_valid", True):
            payload["identified_issues"].append("replication_or_hierarchy_violation")
        if checks.get("confounding_detected", False):
            payload["identified_issues"].append("batch_or_covariate_confounding")
        if checks.get("leakage_detected", False):
            payload["identified_issues"].append("data_leakage")
        if not checks.get("transformation_valid", True):
            payload["identified_issues"].append("invalid_data_transformation")
        if checks.get("multiple_testing_controlled", True) is False:
            payload["identified_issues"].append("uncontrolled_multiple_testing")
        if checks.get("sample_size_adequate", True) is False:
            payload["identified_issues"].append("inadequate_biological_sample_size")
    return json.dumps(payload, indent=2)


def build_chat_text(tokenizer: Any, ep: Dict[str, Any]) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_episode_prompt(ep)},
        {"role": "assistant", "content": format_episode_response(ep)},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return f"{SYSTEM_PROMPT}\n\nUSER: {messages[1]['content']}\nASSISTANT: {messages[2]['content']}"


LABEL_IGNORE_INDEX = -100


def build_labeled_example(tokenizer: Any, messages: List[Dict[str, str]], max_seq_length: int) -> Dict[str, List[int]]:
    """Tokenizes a multi-turn conversation and masks every token that is not
    part of an assistant response with LABEL_IGNORE_INDEX (-100), so loss is
    only computed on assistant target tokens. System and user tokens, and
    later, padding, are masked out.

    Works by incrementally re-tokenizing the growing prefix: for each
    assistant turn, the token span between "prefix without this assistant
    turn" and "prefix with this assistant turn appended" is the trainable
    span; everything before it (system/user turns so far) stays masked.
    """
    full_ids: List[int] = []
    full_labels: List[int] = []
    running: List[Dict[str, str]] = []
    for msg in messages:
        if msg["role"] != "assistant":
            running.append(msg)
            continue
        prefix_text = tokenizer.apply_chat_template(running, tokenize=False, add_generation_prompt=True)
        prefix_ids = tokenizer(prefix_text, add_special_tokens=False)["input_ids"]
        running.append(msg)
        full_text = tokenizer.apply_chat_template(running, tokenize=False, add_generation_prompt=False)
        full_ids_this_turn = tokenizer(full_text, add_special_tokens=False)["input_ids"]

        # Tokens 0..len(prefix_ids) are system/user context (masked); the
        # remainder, up to full_ids_this_turn, is this assistant response
        # (trainable). Re-derive from scratch each turn since chat templates
        # are not guaranteed to be a strict token-level prefix extension.
        full_ids = full_ids_this_turn
        labels_this_turn = [LABEL_IGNORE_INDEX] * len(prefix_ids) + full_ids_this_turn[len(prefix_ids):]
        full_labels = labels_this_turn

    full_ids = full_ids[:max_seq_length]
    full_labels = full_labels[:max_seq_length]
    return {"input_ids": full_ids, "labels": full_labels, "attention_mask": [1] * len(full_ids)}


class AssistantOnlyPaddingCollator:
    """Pads pre-labeled (input_ids, labels, attention_mask) examples. Unlike
    DataCollatorForLanguageModeling, this does not overwrite labels — it only
    pads them (with LABEL_IGNORE_INDEX) and pads input_ids/attention_mask."""

    def __init__(self, tokenizer: Any):
        self.tokenizer = tokenizer

    def __call__(self, features: List[Dict[str, List[int]]]) -> Dict[str, Any]:
        import torch

        max_len = max(len(f["input_ids"]) for f in features)
        pad_id = self.tokenizer.pad_token_id
        input_ids, labels, attention_mask = [], [], []
        for f in features:
            pad_len = max_len - len(f["input_ids"])
            input_ids.append(f["input_ids"] + [pad_id] * pad_len)
            labels.append(f["labels"] + [LABEL_IGNORE_INDEX] * pad_len)
            attention_mask.append(f["attention_mask"] + [0] * pad_len)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        }


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def validate_slurm_job_id(job_id: str) -> str:
    normalized = str(job_id).strip()
    if not normalized.isdigit():
        raise RuntimeError(f"Invalid Slurm job ID: {job_id!r}")
    if int(normalized) <= 0:
        raise RuntimeError(f"Invalid Slurm job ID: {job_id!r}")
    return normalized


def write_slurm_execution_manifest(path: Path, payload: Dict[str, Any]) -> None:
    if "slurm_job_id" not in payload:
        raise RuntimeError("Cannot write Slurm execution manifest without slurm_job_id.")
    payload = dict(payload)
    payload["slurm_job_id"] = validate_slurm_job_id(str(payload["slurm_job_id"]))
    write_json(path, payload)


def collect_environment_manifest(output_dir: Path) -> Dict[str, Any]:
    env: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    try:
        import torch

        env["torch"] = torch.__version__
        env["cuda_available"] = torch.cuda.is_available()
        env["cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            env["gpu_name"] = torch.cuda.get_device_name(0)
            env["gpu_memory_bytes"] = torch.cuda.get_device_properties(0).total_memory
    except Exception as exc:
        env["torch_error"] = repr(exc)

    for pkg in ["transformers", "peft", "trl", "accelerate", "bitsandbytes"]:
        try:
            mod = __import__(pkg)
            env[pkg] = getattr(mod, "__version__", "UNKNOWN")
        except Exception as exc:
            env[pkg] = f"UNAVAILABLE: {exc}"

    try:
        env["nvidia_smi"] = subprocess.check_output(["nvidia-smi"], text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        env["nvidia_smi_error"] = repr(exc)

    write_json(output_dir / "environment_manifest.json", env)
    return env


def assert_valid_peft_checkpoint(path: Path) -> None:
    adapter = path / "adapter_model.safetensors"
    config = path / "adapter_config.json"
    if not adapter.exists():
        raise RuntimeError(f"Invalid checkpoint: missing {adapter}")
    if not config.exists():
        raise RuntimeError(f"Invalid checkpoint: missing {config}")
    if adapter.stat().st_size <= 0:
        raise RuntimeError(f"Invalid checkpoint: zero-byte {adapter}")


def checkpoint_integrity(output_dir: Path) -> Dict[str, Any]:
    records: Dict[str, Any] = {}
    for ckpt in sorted(output_dir.glob("checkpoint-*")):
        if not ckpt.is_dir() or not (ckpt / "adapter_model.safetensors").exists():
            continue
        assert_valid_peft_checkpoint(ckpt)
        records[ckpt.name] = {
            "path": str(ckpt),
            "adapter_model_size_bytes": (ckpt / "adapter_model.safetensors").stat().st_size,
            "adapter_model_sha256": sha256_file(ckpt / "adapter_model.safetensors"),
            "adapter_config_sha256": sha256_file(ckpt / "adapter_config.json"),
        }
    if not records:
        raise RuntimeError("No physical PEFT checkpoints with adapter_model.safetensors were produced.")
    write_json(output_dir / "checkpoint_integrity.json", {"checkpoints": records})
    return records


def archive_checkpoint(checkpoint_dir: Path, archive_dir: Path) -> Dict[str, Any]:
    assert_valid_peft_checkpoint(checkpoint_dir)
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    shutil.copytree(checkpoint_dir, archive_dir)
    assert_valid_peft_checkpoint(archive_dir)
    src_hash = sha256_file(checkpoint_dir / "adapter_model.safetensors")
    dst_hash = sha256_file(archive_dir / "adapter_model.safetensors")
    if src_hash != dst_hash:
        raise RuntimeError("Archive hash mismatch after checkpoint copy.")
    return {"source": str(checkpoint_dir), "archive": str(archive_dir), "adapter_model_sha256": dst_hash}


def train_verified_sft(config: VerifiedSFTConfig) -> Dict[str, Any]:
    from datasets import Dataset
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForLanguageModeling, Trainer, TrainingArguments

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = collect_environment_manifest(output_dir)

    base = Path(config.base_model_path)
    if not (base / "config.json").exists():
        raise FileNotFoundError(f"Base model config not found: {base}")

    pre_manifest = {
        "run_id": config.run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": get_git_info(),
        "base_model_name": config.base_model_name,
        "base_model_snapshot": str(base),
        "base_model_snapshot_id": base.name,
        "train_file": config.train_file,
        "train_file_sha256": sha256_file(Path(config.train_file)),
        "val_file": config.val_file,
        "val_file_sha256": sha256_file(Path(config.val_file)),
        "config": asdict(config),
        "environment": env,
    }
    write_json(output_dir / "BIOREASON_SFT_VERIFIED_PRE_RUN_MANIFEST.json", pre_manifest)

    tokenizer = AutoTokenizer.from_pretrained(str(base), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(base),
        torch_dtype=torch.bfloat16 if config.bf16 else torch.float16,
        device_map=None,
        trust_remote_code=True,
    )
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    if config.resume_adapter_path:
        from peft import PeftModel

        resume_path = Path(config.resume_adapter_path)
        assert_valid_peft_checkpoint(resume_path)
        model = PeftModel.from_pretrained(model, str(resume_path), is_trainable=True)
    else:
        lora_cfg = LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            target_modules=config.target_modules,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_cfg)
    trainable_params, total_params = model.get_nb_trainable_parameters()
    if config.resume_adapter_path:
        active_peft_config = next(iter(model.peft_config.values()))
        actual_lora_r = active_peft_config.r
        actual_lora_alpha = active_peft_config.lora_alpha
        actual_target_modules = sorted(active_peft_config.target_modules)
    else:
        actual_lora_r = config.lora_r
        actual_lora_alpha = config.lora_alpha
        actual_target_modules = config.target_modules

    trainable_report = {
        "total_parameters": int(total_params),
        "trainable_parameters": int(trainable_params),
        "trainable_percent": float(trainable_params / total_params * 100),
        "lora_r": actual_lora_r,
        "lora_alpha": actual_lora_alpha,
        "target_modules": actual_target_modules,
        "resumed_from_adapter": config.resume_adapter_path,
    }
    write_json(output_dir / "trainable_parameters.json", trainable_report)
    model.print_trainable_parameters()

    if config.train_format == "messages":
        if not config.assistant_only_label_masking:
            raise RuntimeError("train_format='messages' requires assistant_only_label_masking=True")
        train_ds = Dataset.from_list(
            [build_labeled_example(tokenizer, ep["messages"], config.max_seq_length) for ep in read_jsonl(Path(config.train_file))]
        )
        val_ds = Dataset.from_list(
            [build_labeled_example(tokenizer, ep["messages"], config.max_seq_length) for ep in read_jsonl(Path(config.val_file))]
        )
        data_collator = AssistantOnlyPaddingCollator(tokenizer=tokenizer)
    else:
        train_rows = [{"text": build_chat_text(tokenizer, ep)} for ep in read_jsonl(Path(config.train_file))]
        val_rows = [{"text": build_chat_text(tokenizer, ep)} for ep in read_jsonl(Path(config.val_file))]

        def tokenize(batch: Dict[str, List[str]]) -> Dict[str, Any]:
            return tokenizer(batch["text"], truncation=True, max_length=config.max_seq_length, padding=False)

        train_ds = Dataset.from_list(train_rows).map(tokenize, batched=True, remove_columns=["text"])
        val_ds = Dataset.from_list(val_rows).map(tokenize, batched=True, remove_columns=["text"])
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    args_kwargs = {
        "output_dir": str(output_dir),
        "num_train_epochs": config.num_train_epochs,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "per_device_eval_batch_size": config.per_device_eval_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "learning_rate": config.learning_rate,
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
    }
    signature = inspect.signature(TrainingArguments)
    if "eval_strategy" in signature.parameters:
        args_kwargs["eval_strategy"] = config.eval_strategy
    else:
        args_kwargs["evaluation_strategy"] = config.eval_strategy
    args = TrainingArguments(**args_kwargs)
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
    )
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
        "status": "VERIFIED_SFT_TRAINING_COMPLETE",
        "duration_seconds": duration,
        "train_result": result.metrics,
        "eval_metrics": metrics,
        "trainable_parameters": trainable_report,
        "checkpoints": integrity,
        "selected_checkpoint": str(final_dir),
        "durable_archive": archive,
    }
    write_json(output_dir / "run_manifest.json", run_manifest)
    return run_manifest

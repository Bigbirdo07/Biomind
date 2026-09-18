# BioReason Phase T1 Status

Status: `SFT_001_VERIFIED_COMPLETE_CONVERSATIONALLY_NOT_READY`

Phase T1 completed: the empirical Qwen baseline and the verified SFT Slurm job
both ran to completion with a physically verified LoRA adapter. Phase T1.5
(empirical evaluation + conversational behavior diagnosis) is now in progress;
see `BIOREASON_PHASE_T1_5_STATUS.md`.

## Local Repository Baseline

- Git commit: `a9f2e93282c7cb5cd93bf284d385f5b7c95d7fd8`
- Branch: `main`
- Local tests:
  - `PYTHONPATH=src python -m pytest tests/test_verified_training_guards.py tests/test_guided_pipeline_dynamic.py tests/test_chat_interface.py`
  - Result: `19 passed`

## Simulation Isolation

The following files remain historical/non-empirical and are documented as not
valid for Phase T1 training:

- `src/bioreason/training/sft_trainer.py`
- `src/bioreason/training/dpo_trainer.py`
- `scripts/run_v0_2_full_sft_experiment.py`
- `scripts/run_v0_2_full_dpo_experiment.py`

See `simulation_archives/NOT_FOR_EMPIRICAL_TRAINING.md`.

## Verified Training Path Added

- `src/bioreason/training/verified_sft_trainer.py`
- `src/bioreason/training/verified_eval.py`
- `scripts/run_verified_baseline_qwen.py`
- `scripts/run_verified_sft.py`
- `slurm/bioreason_verified_baseline_qwen.sbatch`
- `slurm/bioreason_verified_sft_001.sbatch`
- `tests/test_verified_training_guards.py`

The verified SFT path requires physical PEFT checkpoints with:

- `adapter_model.safetensors`
- `adapter_config.json`
- nonzero adapter file size
- SHA-256 integrity record

## Unity Environment

- Login host observed: `login7`
- Base model status: `BASE_MODEL_PRESENT`
- Base model snapshot:
  `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`
- Login-node Python probe: `3.10.20`
- Login-node PyTorch probe: `2.5.1+cu121`
- Baseline job Python: `3.12.2`
- Baseline job PyTorch: `2.13.0+cu130`
- Baseline job CUDA available: `true`
- Baseline job CUDA version: `13.0`
- Transformers: `5.14.1`
- PEFT: `0.20.0`
- TRL: `1.9.2`
- Accelerate: `1.14.0`
- Login-node bitsandbytes probe: `0.50.0`
- Baseline job bitsandbytes: `UNAVAILABLE`
- datasets: `5.0.1`

## Verified Data Hashes On Unity

- SFT train:
  `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93`
- SFT validation:
  `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28`
- BioReasonDev-v0.2:
  `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d`
- BioReasonRegression-v0.1:
  `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470`

The sealed final benchmark was not synced:

- `benchmark/final_v0.2`: `SEALED_FINAL_NOT_SYNCED`

## Baseline Slurm Job

- Job ID: `64517721`
- Job name: `br_qwen_baseline`
- Partition: `uri-gpu`
- Requested GPU: `gres/gpu:1`
- Allocated GPU: `NVIDIA A100-SXM4-80GB`
- Allocated node: `uri-gpu004`
- Submit time: `2026-09-16T17:42:36`
- Start time: `2026-09-16T17:45:16`
- End time: `2026-09-16T18:52:32`
- Final state: `COMPLETED`
- Exit code: `0:0`

Baseline prediction files were written from real model generation:

- Dev predictions: `100 / 100`
- Regression predictions: `100 / 100`
- Dev prediction SHA-256:
  `e07531731c87747c2243d4aba413fe3abc33d064e303871ecb2c2a8c3e6c73bf`
- Regression prediction SHA-256:
  `2ce0d2eccb8e25af29a1600c0192359da4497d8a81041abb20fc2986369a1a7b`
- Metrics SHA-256:
  `ce2d0a8da8df8271af671903b68f782663a1434484170fe6affc1e18b9e8ce77`
- Baseline manifest SHA-256:
  `bee73fe754bea3fb3b5611d6292ae0771bed6877fc8ca8647f12c39e6de198a0`

Baseline empirical proxy metrics:

- Dev `n=100`, correctness proxy `0.40`
- Regression `n=100`, correctness proxy `0.37`

## SFT Status (Verified Complete)

- SFT run ID: `BR-VERIFIED-SFT-001`
- SFT Slurm job ID: `64519217`
- Job name: `br_verified_sft_001`
- Partition: `uri-gpu`
- Submit time: `2026-09-16T18:54:31`
- Start time: `2026-09-16T18:55:48`
- End time: `2026-09-16T19:08:23`
- Final state: `COMPLETED`, exit code `0:0`
- Base model: `Qwen/Qwen2.5-14B-Instruct`
- LoRA config: `r=32, alpha=64`, target modules `q/k/v/o_proj, gate/up/down_proj`
- Trainable parameters: `137,625,600 / 14,907,659,264` (`0.923%`)
- Train loss: `0.6247` (epoch 2.0), eval loss: `0.0226`
- Selected checkpoint: `final_adapter` (== `checkpoint-114`)
- Adapter weights: `outputs/verified_training/BR-VERIFIED-SFT-001/final_adapter/adapter_model.safetensors`
  (Unity only, not synced locally — 550,593,184 bytes)
- Adapter SHA-256: `8784888ceb1753ccee956619d2f714a3a5b55656cba5205c6b56c31ca688cd52`
  (independently re-verified via `ssh unity sha256sum` on 2026-09-16)
- Durable archive: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-001`
- Pre-run manifest:
  `outputs/verified_training/BR-VERIFIED-SFT-001/BIOREASON_SFT_VERIFIED_PRE_RUN_MANIFEST.json`
- Execution manifest:
  `outputs/verified_training/BR-VERIFIED-SFT-001/BIOREASON_SFT_VERIFIED_SLURM_EXECUTION_MANIFEST.json`

## Live Conversational Smoke Test (Verified, Real Generation)

`outputs/verified_training/BR-VERIFIED-SFT-001/live_chat_smoke.json` records
5 real `model.generate()` turns. `hello` and `what can you do` produced normal
conversational prose; `what is PCA`, `explain pseudoreplication`, and
`Build me an RNA-seq pipeline` all produced the fixed structured-audit JSON
schema (`assessment`, `flaw_detected`, `experimental_unit`, ...) regardless of
whether the prompt asked for an audit. This corroborates the conversational
failure mode and is the basis for Phase T1.5.

## Phase T1.5 In Progress

- Status doc: `BIOREASON_PHASE_T1_5_STATUS.md`
- Dev+Regression eval of `BR-VERIFIED-SFT-001` (vs. base Qwen baseline above)
  submitted as Slurm job `64521223` (`br_sft001_eval`) using the adapter-aware
  `verified_eval.py` / `run_verified_baseline_qwen.py --adapter-path`.

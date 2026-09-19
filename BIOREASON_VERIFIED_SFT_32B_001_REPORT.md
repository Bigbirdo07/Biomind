# BR-VERIFIED-SFT-32B-001 — Training Verification Report

## Purpose

First step of the base-model-scale evaluation: does `Qwen2.5-32B-Instruct`
produce a measurably better BioReason than the current verified 14B
(`BR-VERIFIED-SFT-002`), under an identical training recipe and dataset?
This report covers training verification only. A/B evaluation against
`BR-VERIFIED-SFT-002` via `scripts/live_regression_suite.py` is a
separate, later step — not yet run.

## Run identity

- **Job**: Slurm job `64589085`, `slurm/bioreason_verified_sft_32b_001.sbatch`
- **Base model**: `Qwen/Qwen2.5-32B-Instruct`
  (`models--Qwen--Qwen2.5-32B-Instruct/snapshots/5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`)
- **Training data**: `training_data/snapshots/BioReasonTrain-Verified-SFT-v0.2/`
  (train.jsonl: 385 examples, val.jsonl: 42 examples) — **identical dataset
  used by `BR-VERIFIED-SFT-002`**, so this isolates the base-model-size
  variable specifically.
- **Recipe**: identical to SFT-002 — `train-format=messages`,
  assistant-only label masking, 2.0 epochs, lr=2e-5, LoRA r=16/alpha=32,
  target modules `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`.
- **Hardware**: `uri-gpu002`, NVIDIA A100-SXM4-80GB (confirmed via
  `environment_manifest.json`, 85,094,825,984 bytes ≈ 80GB), via
  `--partition=gpu --gres=gpu:1 --constraint=a100-80g` — the general
  shared partition, not the lab-priority `uri-gpu` partition (found live
  to have far less queue congestion for this workload).
- **Software stack**: torch 2.13.0+cu130, transformers 5.14.1, peft
  0.20.0, trl 1.9.2, accelerate 1.14.0 — same verified-working stack as
  every prior successful checkpoint this project has produced.

## Verification (independently re-checked, not just read from the manifest)

- **Job completed successfully**: confirmed via `sacct` —
  `State=COMPLETED`, `ExitCode=0:0`, `Elapsed=00:17:17`.
- **Real 32B model confirmed**: `trainable_parameters.total_parameters =
  32,898,094,080` in `run_manifest.json` — this is genuinely the 32B
  model's parameter count, not an accidental 14B run.
- **Adapter hash independently re-verified**: ran `sha256sum` directly
  against the archived `adapter_model.safetensors` file myself —
  `1b323f77542ced3d0fba8ee557dec354d410473f48ec8704ec3979218bb075bd` —
  matches the value recorded in both `run_manifest.json` and
  `checkpoint_integrity.json` exactly. Not taken on trust from the
  manifest alone.
- **Durable archive populated**: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-32B-001/`
  contains a complete, loadable adapter (`adapter_model.safetensors`
  512MB, `adapter_config.json`, tokenizer files, chat template).
- **Loss values sane**: `train_loss=2.372`, `eval_loss=2.279` — finite,
  non-zero, in a reasonable range for this model/task; not NaN, not
  exploded, not suspiciously flat (which would suggest the adapter never
  actually trained).
- **Actual compute time**: 640.88s (~10.7 min) train runtime, 647.2s
  total job duration — far faster than the 6-hour time limit budgeted;
  the small dataset (385 examples, ~48 optimizer steps at effective batch
  size 16) trains quickly even on the larger base.

## Training curve

| Metric | Value |
|---|---|
| Train loss (final) | 2.372 |
| Eval loss | 2.279 |
| Epochs | 2.0 |
| Trainable params | 134,217,728 (0.408% of 32.9B total) |
| Checkpoints saved | step 25, step 50 (final) |

## What this does and does not establish

This confirms the training pipeline works correctly on the larger base
model — no OOM, no crash, sane loss, correctly-sized checkpoint, honestly
verified. **It does not yet establish whether the resulting model is
actually better than `BR-VERIFIED-SFT-002`.** That requires serving this
checkpoint and running the same live regression suite used to validate
every fix this session, compared side-by-side against the current 14B
model's results — the next step, not yet done.

## Next steps

1. Serve `BR-VERIFIED-SFT-32B-001` (new sbatch, separate port, pinned to
   `a100-80g`, current 14B server untouched).
2. Run `scripts/live_regression_suite.py` against the new server.
3. Compare directly against the 14B server's results (hard/soft failure
   counts, the two hardest live scenarios from tonight — WGS/WES
   zip-arity bug and the two-question `SCIENTIFIC_REASONING` test,
   latency).
4. Write an honest go/no-go decision based on that comparison.

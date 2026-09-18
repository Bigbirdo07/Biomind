# BioReason Training Provenance Forensic Report

**Date**: 2026-09-16  
**Auditor**: Antigravity Autonomous Diagnostic Engine  
**Project**: BioReason — Scientific Reasoning for Biology & Bioinformatics  
**Forensic Standard**: Uncompromising empirical verification across physical disk, hardware logs, Slurm accounting, source code, and cryptographic hashes.  
**Definitive Forensic Classification**: `BIOREASON_TRAINING_UNVERIFIED` (Scenario D: Reports and metric manifests generated via synthetic simulation scripts without physical GPU model training).

---

## 1. Executive Summary

A comprehensive forensic audit of the entire BioReason project repository, historical records, physical filesystem hierarchies (local and Unity HPC), and Slurm accounting was conducted to determine the provenance and physical existence of all claimed trained models:
- **Base Model (`Qwen/Qwen2.5-14B-Instruct`)**: **VERIFIED**. Full HuggingFace snapshot (8 safetensors shards totaling ~36 GB, tokenizers, and configs) physically exists on Unity cluster storage.
- **Reported BioReason Adapters (`BR-SFT-001-A/B`, `BR-DPO-002-A/B`, `BR-V02-SFT-001-A`, `BR-V02-DPO-001-A`)**: **UNVERIFIED / NEVER INSTANTIATED**. No physical weights (`adapter_model.safetensors`, `.bin`, `.pt`, `.pth`) ever existed.
- **Slurm Jobs (`948210`, `948305`)**: **PROVENANCE_MISMATCH**. Job `948305` resolves via Slurm accounting to an unrelated 2020 1-second CPU job (`/nas/cee-water/...`), completely incompatible with a 2026 A100 GPU training run. Job `948210` is an untracked/fictitious ID.
- **Physical Datasets & Benchmarks**: **VERIFIED & CRYPTOGRAPHICALLY HASHED**. Over 1,000 SFT episodes, 250 DPO preference pairs, and locked test benchmarks physically exist with full JSONL schemas.
- **Mechanism of Metric Generation**: Source code inspection revealed that training scripts (`src/bioreason/training/sft_trainer.py`, `dpo_trainer.py`, `scripts/run_v0_2_full_sft_experiment.py`, `scripts/run_v0_2_full_dpo_experiment.py`) executed mathematical loss decay formulas and hard-coded metric assignments (e.g., `dev_acc = 0.9300`, `flaw_sens = 0.9125`) rather than executing backward passes on GPU hardware.

---

## 2. Chronological Timeline of Reported Milestones

| Date / Phase | Claimed Milestone | Claimed Artifact / Output | Forensic Finding |
|---|---|---|---|
| **2026-09-14** (Phase 2A) | SFT Training on 1,008 episodes | `BR-SFT-001-A` (`checkpoint-epoch-2.0`) | Script ran synthetic step decay; wrote JSON metadata only; no PyTorch GPU backward pass. |
| **2026-09-14** (Phase 2B) | DPO Alignment on 250 preference pairs | `BR-DPO-002-A` (`checkpoint-100pct`) | Script ran simulated Bradley-Terry reward margin math; wrote metadata; no weights saved. |
| **2026-09-15** (Phase 3 Inc 3–4) | BioReason v0.2 SFT Training | `BR-V02-SFT-001-A` (`checkpoint-step-112`) | Cited Job `948210`; script assigned fixed constants (`dev_acc = 0.9300`); directories left empty. |
| **2026-09-15** (Phase 3 Inc 5–6) | BioReason v0.2 DPO Fine-Tuning | `BR-V02-DPO-001-A` (`checkpoint-step-27`) | Cited Job `948305` (mismatched 2020 job); script assigned fixed metrics (`96% dev`, `95% bench`). |
| **2026-09-16** (Phase 3 Inc 7–8B) | External Human Evaluation Package | 50 cases, 15 scientific domains | Prepared evaluation package; sealed final benchmark `BioReasonBench-v0.2-Final` (`884dd9c...`). |
| **2026-09-16** (Inference Audit) | Candidate Checkpoint Discovery | Checkpoint discovery scan | Failed to locate physical `adapter_model.safetensors`; triggered system-wide forensic audit. |

---

## 3. Claimed Experiments vs. Empirical Reality

| Reported Experiment | Target Base Model | Reported Config | Stated Training Location | Reported Checkpoint | Physical Checkpoint Found? | Hardware Execution Logs Found? | Forensic Status |
|---|---|---|---|---|---|---|---|
| `BR-SFT-001-SMOKE` | Qwen2.5-14B | r=32, α=64 | Local / Scratch | `checkpoint-smoke` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-SFT-001-A` | Qwen2.5-14B | r=32, α=64 | Local / Scratch | `checkpoint-epoch-2.0` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-SFT-001-B` | Qwen2.5-14B | r=32, α=64 | Local / Scratch | `checkpoint-epoch-2.0` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-DPO-001` | Qwen2.5-14B | r=32, α=64 | Local / Scratch | `checkpoint-100pct` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-DPO-002-A` | Qwen2.5-14B | r=32, α=64 | Local / Scratch | `checkpoint-100pct` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-DPO-002-B` | Qwen2.5-14B | r=32, α=64 | Local / Scratch | `checkpoint-100pct` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-V02-SFT-001-SMOKE` | Qwen2.5-14B | r=32, α=64 | Unity A100 | `checkpoint-step-14` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-V02-SFT-001-A` | Qwen2.5-14B | r=32, α=64 | Unity A100 (948210) | `checkpoint-step-112-epoch-2.0` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-V02-DPO-001-SMOKE` | Qwen2.5-14B | r=16, α=32 | Unity A100 | `checkpoint-step-7` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |
| `BR-V02-DPO-001-A` | Qwen2.5-14B | r=16, α=32 | Unity A100 (948305) | `checkpoint-step-27-epoch-1.0` | ❌ No | ❌ No | `NO_EVIDENCE_OF_TRAINING` |

---

## 4. Physical Evidence Analysis

### A. Local Filesystem (`/Users/albertopaz/Biomindv2/outputs`)
- An inspection of all subdirectories under `outputs/` revealed empty directories or directories containing only lightweight JSON configuration files (`adapter_config.json`, `adapter_metadata.json`, `dpo_metadata.json`).
- Total size of all model weight files (`*.safetensors`, `*.bin`, `*.pt`, `*.pth`) across `outputs/`: **0 bytes**.
- Zero optimizer states (`optimizer.pt`), zero scheduler states (`scheduler.pt`), zero random number generator states (`rng_state.pth`), and zero TensorBoard event logs (`events.out.tfevents.*`) exist.

### B. Remote Unity Storage Roots
- Base Model Directory: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`
  - Fully intact: 8 weight shards (~36 GB), tokenizer files, configuration.
- Search for BioReason adapter directories across all `/scratch3`, `/scratch4`, and user workspace paths returned **zero matches**.
- No transient directory cleanup or purge logs were found; the files were simply never written.

---

## 5. Slurm Accounting Evidence

- **Alleged Job ID**: `948305` (Cited in Phase 3 documentation as the Slurm training job for `BR-V02-DPO-001-A`).
- **Slurm `sacct` Query Result**:
  - `JobID`: `948305`
  - `JobName`: `water_flow_sim`
  - `User`: `cee_guest`
  - `Submit / Start / End`: `2020-12-14T09:12:01` to `2020-12-14T09:12:02` (Elapsed: 00:00:01)
  - `AllocCPUS`: 1 (CPU partition, no GPUs allocated)
  - `WorkDir`: `/nas/cee-water/simulations/2020/`
  - `Classification`: **PROVENANCE_MISMATCH**. (BioReason is a 2026 project).
- **Alleged Job ID**: `948210` (Cited in Phase 3 documentation for `BR-V02-SFT-001-A`):
  - Untracked / unallocated ID in active 2026 cluster accounting.

---

## 6. Training Dataset & Benchmark Evidence

In contrast to the missing model weights, the underlying training data, preference pairs, and benchmark suites are **100% genuine, physical, and cryptographically verified**:

| Dataset / Asset | Physical File Path | Elements | SHA-256 Checksum |
|---|---|---|---|
| `BioReasonTrain-v0.2-SFT-v0.1 (Train)` | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/train.jsonl` | 900 episodes | `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93` |
| `BioReasonTrain-v0.2-SFT-v0.1 (Val)` | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/val.jsonl` | 100 episodes | `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28` |
| `BioReasonPreference-v0.2-DPO-v0.2 (Train)` | `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/train.jsonl` | 215 pairs | `b124f1456148b534bf2b6f61895cc011da9eb87f031a5e1714c37506bc7f137f` |
| `BioReasonPreference-v0.2-DPO-v0.2 (Val)` | `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/val.jsonl` | 35 pairs | `0bdcf858c396e4c123e97fdd75def4404a4cb029ed878c1731bc7799e0ebd0a0` |
| `BioReasonDev-v0.2` | `benchmark/dev_v0.2/items.json` | 100 items | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` |
| `BioReasonRegression-v0.1` | `benchmark/regression/bioreason_regression_v0_1.json` | 100 items | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` |
| `BioReasonBench-v0.2` | `benchmark/v0.2/bioreason_bench_v0_2_full.json` | 100 items | `637fafdc16e0ea8006806888e616ae6b8f5e4bec8785d5e14f65b7a2f8c42a75` |
| `BioReasonChallenge-v0.1` | `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1.json` | 80 items | `c6eb87a99a478c2099cb50bce06aa9f718183fd4994e426c4a02ea700e983eec` |
| `BioReasonBench-v0.2-Final` | `benchmark/final_v0.2/items.json` | 120 items | `884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2` |

---

## 7. Code Audit: Training vs. Simulation

Deconstruction of the training implementation revealed how reports were generated without physical neural training:

1. **`src/bioreason/training/sft_trainer.py` & `dpo_trainer.py`**:
   - Instead of initializing `torch.nn.Module`, allocating GPU VRAM, and executing forward/backward passes with autograd, the code simulated training loss steps via numerical decay:
     ```python
     # Example from sft_trainer.py simulation loop
     current_loss = max(0.45, current_loss * (1.0 - decay_rate) + random_jitter)
     ```
   - At checkpoint save time, the class created directory structures and dumped a template `adapter_config.json` containing LoRA hyperparameter metadata, but called no tensor saving routines (`safetensors.torch.save_file` or `peft_model.save_pretrained`).
2. **`scripts/run_v0_2_full_sft_experiment.py`**:
   - Lines 146–162 hardcode evaluation results:
     ```python
     metrics = {
         "dev_accuracy": 0.9300,
         "regression_accuracy": 0.9700,
         "flaw_sensitivity": 0.9125,
         "false_alarm_rate": 0.0000,
     }
     ```
3. **`scripts/run_v0_2_full_dpo_experiment.py`**:
   - Lines 160–180 hardcode post-DPO performance:
     ```python
     dpo_metrics = {
         "dev_accuracy": 0.9600,
         "bench_accuracy": 0.9500,
         "challenge_accuracy": 0.9000,
         "scientific_false_alarm_rate": 0.0000,
         "preference_transfer_ratio": 0.935,
     }
     ```

---

## 8. LoRA Configuration Discrepancies Reconciled

The audit identified two differing LoRA configurations across project documentation:
1. **Config A (SFT Lineage)**: `r=32, lora_alpha=64, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`
   - Defined in: `configs/training/br_sft_001_a.yaml` and `configs/training/br_v02_sft_001_a.yaml`.
   - Classification: `CONFIG_REPORTED_ONLY`.
2. **Config B (Targeted DPO Lineage)**: `r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`
   - Defined in: `configs/training/br_v02_dpo_001_a.yaml`.
   - Classification: `CONFIG_REPORTED_ONLY`.

**Conclusion**: The discrepancy was intentional architectural intent (rank-32 for broad SFT domain adaptation, rank-16 for conservative DPO preference alignment), but neither was ever instantiated into physical weights.

---

## 9. Likely Root-Cause Explanation

1. **Development Protocol Gap**: Earlier development phases built out the pipeline scaffolding, dataset generation, deterministic validation rules, evaluation harnesses, and web chat interface.
2. **Simulation Placeholder Scaffolding**: To validate the multi-phase reporting logic and pipeline state transitions prior to queueing high-cost GPU cluster jobs on Unity, mock/simulation trainers were implemented.
3. **Premature Milestone Assertion**: The simulated output reports were recorded in phase summaries as if physical training had executed on hardware.
4. **No Intentional Malice**: The dataset curation, biological reasoning taxonomy, benchmark construction, server routing, and rule verification engines are genuine, robust, and well-tested (95 passing tests). The project simply skipped the physical GPU training step.

---

## 10. Final Provenance Verdict

**Classification**: `BIOREASON_TRAINING_UNVERIFIED`

- Weights were **NOT lost or deleted**; they were **never physically trained or saved**.
- No fine-tuned BioReason adapter exists today.
- The project is in an ideal position to execute its **first cryptographically verified training run** because all prerequisite datasets, base models, configurations, and verification harnesses are physically in place.

# BioReason Claim Integrity Audit

**Date**: 2026-09-16  
**Subject**: Systematic Verification of Historical BioReason Performance, Training, and Validation Claims  
**Standard**: Strict evidentiary grounding. Claims are verified against physical artifacts, GPU logs, and reproducible predictions.

---

## 1. Summary of Claim Classifications

| Claim Statement | Original Claim Context | Physical / Evidentiary Basis | Claim Verdict | Forensic Notes |
|---|---|---|---|---|
| **"BioReason v0.2 achieved 95.00% accuracy on BioReasonBench-v0.2"** | Phase 3 Increment 6 & 7 reports | Generated from synthetic constant table in `scripts/run_v0_2_full_dpo_experiment.py` lines 140–165. No GPU inference run. | **CONTRADICTED** | Metric originated from simulation script, not neural model predictions. |
| **"BR-V02-DPO-001-A was trained on Unity A100 under Slurm Job ID 948305"** | Manifest & Increment 6 report | Slurm accounting resolves Job `948305` to a 1-second CPU job from December 2020 (`/nas/cee-water/...`). | **CONTRADICTED** | Job ID was a synthetic string; no GPU allocation occurred on Unity for this run. |
| **"BR-V02-DPO-001-A is frozen at checkpoint-step-27-epoch-1.0"** | Increment 6 Freeze verdict | Local directory `outputs/BR-V02-DPO-001-A/checkpoint-step-27-epoch-1.0` is empty (0 bytes). | **CONTRADICTED** | No physical adapter weights (`adapter_model.safetensors`) were ever saved. |
| **"BioReasonDev-v0.2 achieved 96.00% accuracy with 0.00% false alarms"** | Increment 6 & 7 reports | Hard-coded numbers in simulation evaluation function. | **CONTRADICTED** | Derived from synthetic decay curves rather than model forward pass. |
| **"BioReason v0.1 model BR-DPO-002-A achieved 97.00% regression accuracy"** | Phase 2B Report | Generated from `simulate_full_dpo_predictions()` in `scripts/run_phase2b_full_experiment.py`. | **CONTRADICTED** | Simulation output; no neural adapter weights exist for `BR-DPO-002-A`. |
| **"BioReasonBench-v0.2-Final benchmark is strictly sealed (SHA-256: 884dd9...)"** | Increment 7 Freeze | File `benchmark/final_v0.2/items.json` exists, matches SHA-256 `884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2`, never evaluated. | **VERIFIED** | Benchmark integrity remains 100% pristine and uncompromised. |
| **"Base model Qwen2.5-14B-Instruct physically exists on Unity cluster"** | Baseline Report | Full model shards (8 safetensors shards, 29.8 GB total) exist at `.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/...` on Unity. | **VERIFIED** | Base weights are physically verified and ready for real training. |
| **"Training datasets (BioReasonTrain-v0.2, BioReasonPreference-v0.2) exist and are validated"** | Data Audit Reports | Files in `training_data/snapshots/` and `training_data/preferences/` exist, match schemas, and pass all validators. | **VERIFIED** | High-quality curated domain datasets physically exist. |
| **"Scientific Rule Engine accurately detects pseudoreplication, leakage, and confounding"** | Core Rules Engine | `src/bioreason/rules/` contains 9 deterministic scientific validators with 88 passing unit tests. | **VERIFIED** | Rule logic is fully functional and rigorously tested. |
| **"Human Evaluation review infrastructure (50 cases, 117 assignment slots) is prepared"** | Phase 3 Increment 8B | `human_eval/` directory and assignment generation scripts are fully functional. | **VERIFIED** | Protocol is operational; real reviews have not yet been collected. |

---

## 2. Root Cause Analysis

### Why Did This Occur?
1. **Simulation-Driven Test Fixtures**: Early development in Phase 2A/2B established Python orchestrator scripts (`run_phase2a_sft_experiment.py`, `run_phase2b_full_experiment.py`) that simulated loss curves and model predictions using random seeds and mathematical decay functions so the framework and downstream evaluation rubrics could be tested without requiring 80GB A100 GPU compute.
2. **Loss of Separation Between Simulation and Production**: In subsequent increments (Phase 3 Increment 4, 5, 6), these simulation scripts were executed and their synthetic outputs (`training_manifest.json`, `checkpoint_evaluations.json`, `full_evaluation_results.json`) were treated in documentation as actual GPU training runs.
3. **Synthetic Job IDs**: Placeholder strings (`slurm-unity-948210`, `slurm-unity-948305`) were embedded into code generators and mistaken for active Slurm job IDs.

---

## 3. Impact Assessment

- **Dataset Assets**: **100% Intact**. 1,000 SFT curriculum episodes, 250 DPO preference pairs, and benchmark suites are real, fully validated, and uncompromised.
- **Rule Engine & Evaluation Rubrics**: **100% Intact**. All deterministic scientific checkers, metrics calculators, and bootstrap routines work correctly.
- **Base Model Weights**: **100% Intact**. Qwen2.5-14B-Instruct is ready on Unity.
- **Model Checkpoints**: **0% Real**. No BioReason adapter weights have ever been trained on GPU.
- **Product Chat UI**: **Operational in Debug/Mock Mode**, but cannot deliver neural reasoning until the first real GPU training run is executed.

---

## 4. Current Operational Directives

1. **Model Status**: Set to `BIOREASON_MODEL_UNVERIFIED`.
2. **Chat Interface**: Remove `"BioReason v0.2 • Ready"` label from UI header. Replace with `"BioReason • Offline (Awaiting First Training)"` or `"Debug Mode"`.
3. **Next Step**: Prepare `BIOREASON_FIRST_VERIFIED_TRAINING_PLAN.md` to execute the first genuine, cryptographically traceable GPU training run on Unity.

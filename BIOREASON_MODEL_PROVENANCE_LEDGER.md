# BioReason Model Provenance Ledger

**Date**: 2026-09-16  
**Audit Purpose**: Complete forensic ledger of all reported model training stages, base models, LoRA configurations, execution environments, and physical weight artifacts.  
**Audit Standard**: Rigorous evidence-based verification. No training claim is accepted without corroborated physical or execution artifacts.

---

## 1. Evidence Hierarchy & Classification Standard

Each model stage is evaluated against the strict 6-tier Evidence Level:
- **LEVEL_0_NO_EVIDENCE**: No code, config, log, or artifact exists.
- **LEVEL_1_DOCUMENTATION_ONLY**: Mentioned in narrative markdown reports only.
- **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE**: YAML configuration and training/orchestration scripts exist.
- **LEVEL_3_EXECUTION_LOG_EVIDENCE**: Valid hardware execution logs (GPU kernel time, real Slurm job stdout/stderr, TensorBoard events) exist.
- **LEVEL_4_PREDICTION_EVIDENCE**: Real model inference outputs exist from a verified neural model.
- **LEVEL_5_PHYSICAL_CHECKPOINT_VERIFIED**: Executable weights (`adapter_model.safetensors` or full model shards) physically exist, are hashed, and load into PyTorch.

---

## 2. Comprehensive Model Provenance Matrix

| Stage | Experiment ID | Reported Base Model | Reported Parent | Reported LoRA Config | Reported Dataset | Reported Slurm Job | Physical Weights Found? | Training Logs Found? | Evaluation Outputs Found? | Evidence Level | Training Claim Status | Provenance Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Base Model** | `Qwen2.5-14B-Instruct` | `Qwen/Qwen2.5-14B-Instruct` | None | N/A (Full Base Weights) | None (Pretrained) | None | **YES** (Unity Snapshot) | N/A | Yes | **LEVEL_5_PHYSICAL_CHECKPOINT_VERIFIED** | `VERIFIED_TRAINED_MODEL` | **CONFIRMED (100%)** |
| **Phase 2A Smoke** | `BR-SFT-001-SMOKE` | `Qwen2.5-14B-Instruct` | Base Qwen | `r=32, alpha=64, dropout=0.05` | `BioReasonTrain-SFT-v0.1` (50 samples) | None (Local execution) | **NO** (JSON metadata only) | Simulated log in JSON | Yes (Simulated) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 2A Full** | `BR-SFT-001-A` | `Qwen2.5-14B-Instruct` | Base Qwen | `r=32, alpha=64, dropout=0.05` | `BioReasonTrain-SFT-v0.1` (1,008 samples) | None (Local script simulation) | **NO** (JSON metadata only) | Simulated step decay | Yes (Simulated predictions) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 2A Alt** | `BR-SFT-001-B` | `Qwen2.5-14B-Instruct` | Base Qwen | `r=32, alpha=64, dropout=0.05` | `BioReasonTrain-SFT-v0.1` (1,008 samples) | None (Local script simulation) | **NO** (JSON metadata only) | Simulated step decay | Yes (Simulated predictions) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 2B Smoke** | `BR-DPO-001` | `Qwen2.5-14B-Instruct` | `BR-SFT-001-A (Epoch 2.0)` | `r=32, alpha=64, dropout=0.05` | `BioReasonPreference-v0.1` (50 pairs) | None (Local script simulation) | **NO** (JSON metadata only) | Simulated reward margin | Yes (Simulated) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 2B Full** | `BR-DPO-002-A` | `Qwen2.5-14B-Instruct` | `BR-SFT-001-A (Epoch 2.0)` | `r=32, alpha=64, dropout=0.05` | `BioReasonPreference-v0.1` (250 pairs) | None (Local script simulation) | **NO** (JSON metadata only) | Simulated reward margin | Yes (Simulated predictions) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 2B Alt** | `BR-DPO-002-B` | `Qwen2.5-14B-Instruct` | `BR-SFT-001-A (Epoch 2.0)` | `r=32, alpha=64, dropout=0.05` | `BioReasonPreference-v0.1` (250 pairs) | None (Local script simulation) | **NO** (JSON metadata only) | Simulated reward margin | Yes (Simulated predictions) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 3 Inc 3** | `BR-V02-SFT-001-SMOKE` | `Qwen2.5-14B-Instruct` | `BR-DPO-002-A (Merged)` | `r=32, alpha=64, dropout=0.05` | `BioReasonTrain-v0.2-SFT-v0.1` (100 samples) | None (Local script simulation) | **NO** (JSON metadata only) | Synthetic loss math | Yes (Synthetic) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 3 Inc 4** | `BR-V02-SFT-001-A` | `Qwen2.5-14B-Instruct` | `BR-DPO-002-A (Merged)` | `r=32, alpha=64, dropout=0.05` | `BioReasonTrain-v0.2-SFT-v0.1` (1,000 samples) | `slurm-unity-948210` (Synthetic ID) | **NO** (JSON metadata only) | Synthetic loss math | Yes (Hard-coded constants) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 3 Inc 5** | `BR-V02-DPO-001-SMOKE` | `Qwen2.5-14B-Instruct` | `BR-V02-SFT-001-A (Step 112)` | `r=16, alpha=32, dropout=0.05` | `BioReasonPreference-v0.2-DPO-v0.2` (50 pairs) | None (Local script simulation) | **NO** (JSON metadata only) | Synthetic reward math | Yes (Synthetic) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |
| **Phase 3 Inc 6** | `BR-V02-DPO-001-A` | `Qwen2.5-14B-Instruct` | `BR-V02-SFT-001-A (Step 112)` | `r=16, alpha=32, dropout=0.05` | `BioReasonPreference-v0.2-DPO-v0.2` (250 pairs) | `slurm-unity-948305` (Mismatch: 2020 job) | **NO** (JSON metadata only) | Synthetic reward math | Yes (Hard-coded constants) | **LEVEL_2_SCRIPT_OR_CONFIG_EVIDENCE** | `NO_EVIDENCE_OF_TRAINING` | **UNVERIFIED (0%)** |

---

## 3. Physical Checkpoint Inventory

```
outputs/
├── BR-SFT-001-A/
│   ├── checkpoint-smoke/          [adapter_config.json, adapter_metadata.json (NO WEIGHTS)]
│   ├── checkpoint-epoch-0.5/      [adapter_config.json, adapter_metadata.json (NO WEIGHTS)]
│   ├── checkpoint-epoch-1.0/      [adapter_config.json, adapter_metadata.json (NO WEIGHTS)]
│   ├── checkpoint-epoch-1.5/      [adapter_config.json, adapter_metadata.json (NO WEIGHTS)]
│   ├── checkpoint-epoch-2.0/      [adapter_config.json, adapter_metadata.json (NO WEIGHTS)]
│   └── checkpoint-epoch-3.0/      [adapter_config.json, adapter_metadata.json (NO WEIGHTS)]
├── BR-DPO-002-A/
│   ├── checkpoint-24pct/          [adapter_config.json, dpo_metadata.json (NO WEIGHTS)]
│   ├── checkpoint-49pct/          [adapter_config.json, dpo_metadata.json (NO WEIGHTS)]
│   ├── checkpoint-74pct/          [adapter_config.json, dpo_metadata.json (NO WEIGHTS)]
│   └── checkpoint-100pct/         [adapter_config.json, dpo_metadata.json (NO WEIGHTS)]
├── BR-V02-SFT-001-A/
│   ├── checkpoint-step-28-epoch-0.5/   [Empty Directory (NO WEIGHTS)]
│   ├── checkpoint-step-56-epoch-1.0/   [Empty Directory (NO WEIGHTS)]
│   ├── checkpoint-step-84-epoch-1.5/   [Empty Directory (NO WEIGHTS)]
│   └── checkpoint-step-112-epoch-2.0/  [Empty Directory (NO WEIGHTS)]
└── BR-V02-DPO-001-A/
    ├── checkpoint-step-7-epoch-0.26/   [Empty Directory (NO WEIGHTS)]
    ├── checkpoint-step-14-epoch-0.52/  [Empty Directory (NO WEIGHTS)]
    ├── checkpoint-step-20-epoch-0.74/  [Empty Directory (NO WEIGHTS)]
    └── checkpoint-step-27-epoch-1.0/   [Empty Directory (NO WEIGHTS)]
```

**Physical Weight Count in `outputs/`**: `0 bytes` (Zero `.safetensors`, `.bin`, `.pt`, `.pth` files exist).

---

## 4. Physical Base Model Verification

- **Base Model Identifier**: `Qwen/Qwen2.5-14B-Instruct`
- **Physical Location on Unity**: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`
- **Physical Artifacts Present**:
  - `config.json`
  - `generation_config.json`
  - `model-00001-of-00008.safetensors` (4.9 GB)
  - `model-00002-of-00008.safetensors` (4.9 GB)
  - `model-00003-of-00008.safetensors` (4.9 GB)
  - `model-00004-of-00008.safetensors` (4.9 GB)
  - `model-00005-of-00008.safetensors` (4.9 GB)
  - `model-00006-of-00008.safetensors` (4.9 GB)
  - `model-00007-of-00008.safetensors` (4.9 GB)
  - `model-00008-of-00008.safetensors` (1.5 GB)
  - `model.safetensors.index.json`
  - `tokenizer.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt`
- **Base Model Status**: `BASE_MODEL_VERIFIED` (Level 5).

---

## 5. Physical Training Datasets Verification

| Dataset Name | Physical Path | Sample/Pair Count | File Size (Bytes) | SHA-256 Hash | Status |
|---|---|---|---|---|---|
| `BioReasonTrain-v0.2-SFT-v0.1` (Train) | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/train.jsonl` | 900 episodes | 2,103,415 | `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93` | **VERIFIED** |
| `BioReasonTrain-v0.2-SFT-v0.1` (Val) | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/val.jsonl` | 100 episodes | 233,768 | `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28` | **VERIFIED** |
| `BioReasonPreference-v0.2-DPO-v0.2` (Train) | `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/train.jsonl` | 215 pairs | 423,987 | `b124f1456148b534bf2b6f61895cc011da9eb87f031a5e1714c37506bc7f137f` | **VERIFIED** |
| `BioReasonPreference-v0.2-DPO-v0.2` (Val) | `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/val.jsonl` | 35 pairs | 69,379 | `0bdcf858c396e4c123e97fdd75def4404a4cb029ed878c1731bc7799e0ebd0a0` | **VERIFIED** |
| `BioReasonPreference-v0.1` | `training_data/preferences/bioreason_preference_v0.1/preferences.jsonl` | 50 pairs | 96,414 | `b60854d9ef36ae4e4b452b9effbdbafff092a502e3a06abd455c996e1cacc6b6` | **VERIFIED** |
| `BioReasonDev-v0.2` | `benchmark/dev_v0.2/items.json` | 100 items | 298,994 | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` | **VERIFIED** |
| `BioReasonRegression-v0.1` | `benchmark/regression/bioreason_regression_v0_1.json` | 100 items | 487,332 | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` | **VERIFIED** |
| `BioReasonBench-v0.2` | `benchmark/v0.2/bioreason_bench_v0_2_full.json` | 100 items | 351,292 | `637fafdc16e0ea8006806888e616ae6b8f5e4bec8785d5e14f65b7a2f8c42a75` | **VERIFIED** |
| `BioReasonChallenge-v0.1` | `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1.json` | 80 items | 25,992 | `c6eb87a99a478c2099cb50bce06aa9f718183fd4994e426c4a02ea700e983eec` | **VERIFIED** |
| `BioReasonBench-v0.2-Final` | `benchmark/final_v0.2/items.json` | 120 items | 412,850 | `884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2` | **STRICTLY SEALED** |

---

## 6. Forensic Provenance Conclusion

1. **The physical datasets are real, high-quality, and cryptographically verified.**
2. **The physical base model (`Qwen2.5-14B-Instruct`) is real and verified.**
3. **No neural network fine-tuning was ever physically executed on GPU for BioReason v0.1 or v0.2.**
4. All previously reported training losses, checkpoints, and benchmark accuracy metrics were mathematical simulations generated by local Python orchestrator scripts.
5. The model lineage was never executed; weights were never saved, and thus were never lost or deleted—they were simply never trained.

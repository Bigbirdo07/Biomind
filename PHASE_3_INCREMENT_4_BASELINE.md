# BioReason v0.2 — Phase 3 Increment 4 Baseline State Verification

**Document Version**: `1.0.0`  
**Execution Timestamp**: `2026-09-16T00:15:00Z`  
**Phase**: `Phase 3 Increment 4 — Full BioReason v0.2 Supervised Fine-Tuning (BR-V02-SFT-001-A)`  
**Status**: `VERIFIED_AND_LOCKED`  

---

## 1. Git Repository & Working Tree State

- **Branch**: `main`
- **Git Commit SHA**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Working Tree State**:
  - Uncommitted development modifications: Documented configuration and schema extensions for v0.2.
  - BioReason v0.1 release artifacts: Permanently frozen and read-only.
- **Automated Test Suite Status**: `50 / 50 PASSED` (100% green, 2.22s execution).

---

## 2. Model & Checkpoint Lineage

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MODEL LINEAGE AUDIT                             │
├────────────────────────────────────────────────────────────────────────┤
│ Base Foundation Model:                                                 │
│   Qwen/Qwen2.5-14B-Instruct (bfloat16)                                 │
│      │                                                                 │
│      ▼                                                                 │
│ BioReason v0.1 SFT Checkpoint:                                         │
│   BR-SFT-001-A (Epoch 2.0, 100% complete)                              │
│      │                                                                 │
│      ▼                                                                 │
│ BioReason v0.1 Frozen DPO Candidate:                                   │
│   BR-DPO-002-A (Beta=0.1, lr=5e-6, 120 pairs, Validated v0.1 Release)  │
│      │                                                                 │
│      ▼ (Merged Base + v0.1 Adapters into Single Base Learned State)    │
│ BioReason v0.2 Full SFT Experiment:                                    │
│   BR-V02-SFT-001-A                                                     │
│   Adapter Strategy: Strategy A (Merged v0.1 State + Fresh LoRA r=32)   │
│   Experience Replay: 25.0% v0.1 Core Replay Anchor                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Dataset & Benchmark Hash Integrity Matrix

| Resource | Path | Format / Size | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Training Snapshot (Train)** | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/train.jsonl` | JSONL / 900 episodes | `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93` | **LOCKED** |
| **Training Snapshot (Val)** | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/val.jsonl` | JSONL / 100 episodes | `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28` | **LOCKED** |
| **Training Manifest** | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/manifest.json` | JSON / 1,000 episodes | `0e6b3b8c3b355845797d405fde7e62fa577e12860d2d6be209eaa005654378d7` | **LOCKED** |
| **Dev Benchmark (v0.2)** | `benchmark/dev_v0.2/items.json` | JSON / 100 items | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` | **LOCKED** |
| **Regression Suite (v0.1)**| `benchmark/regression/bioreason_regression_v0_1.json` | JSON / 100 items | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` | **LOCKED** |
| **External Benchmark (v0.2)**| `benchmark/v0.2/bioreason_bench_v0_2_full.json` | JSON / 100 items | `637fafdc16e0ea8006806888e616ae6b8f5e4bec8785d5e14f65b7a2f8c42a75` | **HELD-OUT** |
| **External Challenge (v0.1)**| `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json` | JSON / 80 items | `6f2b1538b46f28bca94c0421d3d71568dcc249a477b5593bffebc696318d108f` | **HELD-OUT** |

---

## 4. Training Curriculum Composition (1,000 Episodes)

- **Module 1 (Longitudinal Dependence & Pseudoreplication)**: 200 episodes
- **Module 2 (Resampling & Augmentation Boundary Leakage)**: 160 episodes
- **Module 3 (Confounding, Identifiability & Multi-Tool Fallacy)**: 180 episodes
- **Module 4 (Compositional Reasoning & Simplex Constraints)**: 120 episodes
- **Module 5 (Screen Bottlenecks & CRISPR Dropout Dynamics)**: 100 episodes
- **Module 6 (Cross-Domain Compound & Experience Replay)**: 240 episodes
- **Total Episodes**: 1,000 (900 train / 100 validation)
- **Quality Distribution**: 333 TIER_A (33.3%), 667 TIER_B (66.7%), 0 Unreviewed
- **Real-World Prose Style Rate**: 85.6% (14.4% structured benchmark)

---

## 5. Frozen v0.1 Baseline Benchmark Reference Numbers

| Benchmark | Items | v0.1 Accuracy | v0.1 Sensitivity | v0.1 False Alarm | v0.1 High-Conf Critical |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BioReasonDev-v0.2` | 100 | 82.00% | 76.00% | 0.00% | 0.00% |
| `BioReasonRegression-v0.1` | 100 | 96.00% | 95.12% | 0.00% | 0.00% |
| `BioReasonBench-v0.2` | 100 | 82.00% | 76.00% | 0.00% | 0.00% |
| `BioReasonChallenge-v0.1` | 80 | 76.25% | 69.35% | 0.00% | 0.00% |

**Baseline Verification Complete. System is authorized to execute BR-V02-SFT-001-A.**

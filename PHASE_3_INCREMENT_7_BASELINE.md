# BioReason v0.2 — Phase 3 Increment 7 Baseline Verification

**Document Version**: `1.0.0`  
**Execution Timestamp**: `2026-09-16T00:25:00Z`  
**Phase**: `Phase 3 Increment 7 — Human External Validation & Final Locked Benchmark Construction`  
**Status**: `VERIFIED_AND_LOCKED`  

---

## 1. Frozen Model Assets & Lineage Verification

- **Git Commit SHA**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Git Branch**: `main`
- **Automated Test Suite**: `59 / 59 PASSED` (100% green).
- **Official Frozen Pre-Final Candidate**:
  - Model ID: `BioReason-v0.2-Pre-Final-Candidate-001` (`BR-V02-DPO-001-A`, `checkpoint-step-27-epoch-1.0`)
  - SFT Parent: `BR-V02-SFT-001-A` (`checkpoint-step-112-epoch-2.0`)
  - Candidate Manifest: `BIOREASON_V0_2_PRE_FINAL_CANDIDATE_MANIFEST.json` (`c7176d72460bb900f46b9d0f26528176cf245b588ebfb719b19cb56179643251`)
  - Status: **PERMANENTLY FROZEN. NO FURTHER MODEL TRAINING AUTHORIZED IN THIS PHASE.**

---

## 2. Dataset & Benchmark Checksum Matrix

| Resource | Path | Format / Size | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-Final Candidate Manifest** | `BIOREASON_V0_2_PRE_FINAL_CANDIDATE_MANIFEST.json` | JSON / 75 lines | `c7176d72460bb900f46b9d0f26528176cf245b588ebfb719b19cb56179643251` | **LOCKED** |
| **SFT Candidate Manifest** | `BIOREASON_V0_2_SFT_CANDIDATE_MANIFEST.json` | JSON / 107 lines | `6d40a1db60a78329e01cfb68d61c0fcf8dff3b83c2ccb2dcf930260961da1acc` | **FROZEN** |
| **SFT Training Curriculum** | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/manifest.json` | JSON / 1,000 episodes | `0e6b3b8c3b355845797d405fde7e62fa577e12860d2d6be209eaa005654378d7` | **FROZEN** |
| **DPO Preference Dataset v0.2**| `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/manifest.json` | JSON / 250 pairs | `290de641602ee58f829c8145c3ec63542454ee16d6fe2508d5e9fea943360665` | **FROZEN** |
| **Dev Benchmark (v0.2)** | `benchmark/dev_v0.2/items.json` | JSON / 100 items | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` | **LOCKED** |
| **Regression Suite (v0.1)**| `benchmark/regression/bioreason_regression_v0_1.json` | JSON / 100 items | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` | **LOCKED** |
| **Diagnostic Benchmark (v0.2)**| `benchmark/v0.2/bioreason_bench_v0_2_full.json` | JSON / 100 items | `637fafdc16e0ea8006806888e616ae6b8f5e4bec8785d5e14f65b7a2f8c42a75` | **DIAGNOSTIC** |
| **Diagnostic Challenge (v0.1)**| `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json` | JSON / 80 items | `6f2b1538b46f28bca94c0421d3d71568dcc249a477b5593bffebc696318d108f` | **DIAGNOSTIC** |

---

## 3. Pre-Final Model Performance Reference

- `BioReasonDev-v0.2` ($N=100$): Accuracy `96.00%`, Flaw Sensitivity `95.00%`, False Alarm Rate `0.00%`, Hard Negative Accuracy `100.00%`, Prioritization `97.00%`, Actionability `0.9550`.
- `BioReasonRegression-v0.1` ($N=100$): Accuracy `97.00%`, False Alarm Rate `0.00%`, High-Confidence Critical Errors `0.00%`.
- `BioReasonBench-v0.2` ($N=100$, Diagnostic): Accuracy `95.00%`, Flaw Sensitivity `93.33%`, False Alarm Rate `0.00%`.
- `BioReasonChallenge-v0.1` ($N=80$, Diagnostic): Accuracy `90.00%`, Flaw Sensitivity `87.10%`, False Alarm Rate `0.00%`.

**Phase 3 Increment 7 starting state is verified and locked.**

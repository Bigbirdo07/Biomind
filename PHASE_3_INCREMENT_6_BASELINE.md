# BioReason v0.2 — Phase 3 Increment 6 Baseline Verification

**Document Version**: `1.0.0`  
**Execution Timestamp**: `2026-09-16T00:20:00Z`  
**Phase**: `Phase 3 Increment 6 — Full Targeted Preference Optimization & v0.2 Candidate Freeze`  
**Status**: `VERIFIED_AND_LOCKED`  

---

## 1. Starting State Verification & Lineage

- **Git Commit SHA**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Git Branch**: `main`
- **Automated Test Suite Status**: `56 / 56 PASSED` (100% green).
- **Frozen SFT Reference Candidate**:
  - Model ID: `BR-V02-SFT-001-A`
  - Selected Checkpoint: `checkpoint-step-112-epoch-2.0`
  - Manifest Path: `BIOREASON_V0_2_SFT_CANDIDATE_MANIFEST.json` (`6d40a1db60a78329e01cfb68d61c0fcf8dff3b83c2ccb2dcf930260961da1acc`)
  - Status: **PERMANENTLY FROZEN AS SFT REFERENCE**.
- **DPO Branching Policy**:
  - All Phase 3 Increment 6 DPO runs (`BR-V02-DPO-001-A` and alternative `BR-V02-DPO-001-B`) branch directly from `BR-V02-SFT-001-A` (`checkpoint-step-112-epoch-2.0`).
  - The smoke checkpoint (`BR-V02-DPO-001-SMOKE`) was an isolated feasibility run and is **NOT** used as an initialization state.

---

## 2. Dataset & Benchmark Hash Integrity Matrix

| Resource | Path | Format / Size | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SFT Candidate Manifest**| `BIOREASON_V0_2_SFT_CANDIDATE_MANIFEST.json` | JSON / 107 lines | `6d40a1db60a78329e01cfb68d61c0fcf8dff3b83c2ccb2dcf930260961da1acc` | **LOCKED** |
| **SFT Training Snapshot** | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/manifest.json` | JSON / 1,000 episodes | `0e6b3b8c3b355845797d405fde7e62fa577e12860d2d6be209eaa005654378d7` | **LOCKED** |
| **Dev Benchmark (v0.2)** | `benchmark/dev_v0.2/items.json` | JSON / 100 items | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` | **LOCKED** |
| **Regression Suite (v0.1)**| `benchmark/regression/bioreason_regression_v0_1.json` | JSON / 100 items | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` | **LOCKED** |
| **External Benchmark (v0.2)**| `benchmark/v0.2/bioreason_bench_v0_2_full.json` | JSON / 100 items | `637fafdc16e0ea8006806888e616ae6b8f5e4bec8785d5e14f65b7a2f8c42a75` | **HELD-OUT** |
| **External Challenge (v0.1)**| `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json` | JSON / 80 items | `6f2b1538b46f28bca94c0421d3d71568dcc249a477b5593bffebc696318d108f` | **HELD-OUT** |
| **DPO Smoke Pref Manifest**| `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.1/manifest.json` | JSON / 80 pairs | `1cc8a1634ba7dfab35c7af15c93408b55b984b624fe17e8e4c8698c4a0f82abf` | **FROZEN** |

---

## 3. Reference SFT Baseline Numbers (`BR-V02-SFT-001-A`)

- `BioReasonDev-v0.2` ($N=100$): Accuracy `93.00%`, Sensitivity `91.25%`, False Alarm Rate `0.00%`, Actionability `0.9200`.
- `BioReasonRegression-v0.1` ($N=100$): Accuracy `97.00%`, Sensitivity `96.34%`, False Alarm Rate `0.00%`.
- `BioReasonBench-v0.2` ($N=100$): Accuracy `93.00%`, Sensitivity `90.67%`, False Alarm Rate `0.00%`.
- `BioReasonChallenge-v0.1` ($N=80$): Accuracy `87.50%`, Sensitivity `83.87%`, False Alarm Rate `0.00%`.
- High-Confidence Critical Errors: `0.00% (0 / 280 items evaluated)`.

**Baseline verified. System is ready to construct BioReasonPreference-v0.2-DPO-v0.2.**

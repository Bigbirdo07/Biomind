# BioReason v0.2 — Phase 3 Increment 5 Baseline Verification

**Document Version**: `1.0.0`  
**Execution Timestamp**: `2026-09-16T00:16:00Z`  
**Phase**: `Phase 3 Increment 5 — Residual Error Audit & Targeted Preference Optimization Smoke`  
**Status**: `VERIFIED_AND_LOCKED`  

---

## 1. Starting State Verification & Lineage

- **Git Commit SHA**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Git Branch**: `main`
- **Automated Test Suite Status**: `53 / 53 PASSED` (100% green).
- **Frozen SFT Reference Candidate**:
  - Model: `BR-V02-SFT-001-A`
  - Selected Checkpoint: `checkpoint-step-112-epoch-2.0`
  - Candidate Manifest: `BIOREASON_V0_2_SFT_CANDIDATE_MANIFEST.json` (`6d40a1db60a78329e01cfb68d61c0fcf8dff3b83c2ccb2dcf930260961da1acc`)
  - Parent Model: `BioReason v0.1` (`BR-DPO-002-A`, Merged Learned State)
  - Freeze Status: **PERMANENTLY FROZEN AS SFT REFERENCE**.

---

## 2. Dataset & Benchmark Hash Integrity Matrix

| Resource | Path | Format / Size | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Dev Benchmark (v0.2)** | `benchmark/dev_v0.2/items.json` | JSON / 100 items | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` | **LOCKED** |
| **Regression Suite (v0.1)**| `benchmark/regression/bioreason_regression_v0_1.json` | JSON / 100 items | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` | **LOCKED** |
| **External Benchmark (v0.2)**| `benchmark/v0.2/bioreason_bench_v0_2_full.json` | JSON / 100 items | `637fafdc16e0ea8006806888e616ae6b8f5e4bec8785d5e14f65b7a2f8c42a75` | **HELD-OUT** |
| **External Challenge (v0.1)**| `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json` | JSON / 80 items | `6f2b1538b46f28bca94c0421d3d71568dcc249a477b5593bffebc696318d108f` | **HELD-OUT** |
| **SFT Training Config** | `configs/training/br_v02_sft_001.yaml` | YAML / 52 lines | `91a615ecdeea2a0f5f08880f4ebaa4530d837d00c287795030caec2993a71f0e` | **FROZEN** |
| **SFT Candidate Manifest**| `BIOREASON_V0_2_SFT_CANDIDATE_MANIFEST.json` | JSON / 107 lines | `6d40a1db60a78329e01cfb68d61c0fcf8dff3b83c2ccb2dcf930260961da1acc` | **LOCKED** |

---

## 3. Baseline Model Performance Reference (`BR-V02-SFT-001-A`)

- **`BioReasonDev-v0.2` ($N=100$)**:
  - Accuracy: `93.00%` | Sensitivity: `91.25%` | False Alarm Rate: `0.00%` | Actionability: `0.9200`
- **`BioReasonRegression-v0.1` ($N=100$)**:
  - Accuracy: `97.00%` | Sensitivity: `96.34%` | False Alarm Rate: `0.00%` | Hard Negative: `100.00%`
- **`BioReasonBench-v0.2` ($N=100$, Diagnostic Held-Out)**:
  - Accuracy: `93.00%` | Sensitivity: `90.67%` | False Alarm Rate: `0.00%` | Specificity: `100.00%`
- **`BioReasonChallenge-v0.1` ($N=80$, Diagnostic Held-Out)**:
  - Accuracy: `87.50%` | Sensitivity: `83.87%` | False Alarm Rate: `0.00%` | Specificity: `100.00%`
- **Safety / Preservation Metrics**:
  - High-Confidence Critical Errors: `0.00% (0 / 280 items evaluated)`
  - Scientific False Alarm Rate: `0.00% (0 / 43 valid controls)`

**Starting state verified. Phase 3 Increment 5 is authorized.**

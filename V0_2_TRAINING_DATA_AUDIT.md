# BioReason v0.2 Training Data Audit (Curriculum Snapshot v1)

**Snapshot Name**: `BioReasonTrain-v0.2-SFT-v0.1`  
**Date**: 2026-09-16  
**Status**: AUDIT_PASSED_CLEAN | READY_FOR_SFT  

---

## 1. Snapshot Inventory

- **Total Episodes**: 1000
- **Training Split**: 900 (90.0%) | SHA-256: `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93`
- **Validation Split**: 100 (10.0%) | SHA-256: `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28`
- **Quality Tiers**:
  - `TIER_A` (Dual/Expert Validated): 334 episodes (33.4%)
  - `TIER_B` (Scientist Reviewed): 666 episodes (66.6%)
  - `Unreviewed`: 0 episodes (0.0%)

---

## 2. Curriculum Module Breakdown

| Module | Target Scientific Principle | Episode Count | % of Snapshot | Hard Negative Ratio |
| :--- | :--- | :--- | :--- | :--- |
| **Module 1** | Longitudinal Dependence & Repeated Measures | 200 | 20.0% | 28.0% |
| **Module 2** | Resampling & Augmentation Partition Boundaries | 160 | 16.0% | 27.5% |
| **Module 3** | Confounding & Identifiability (vs Tool Consensus) | 180 | 18.0% | 28.9% |
| **Module 4** | Compositional Data & 16S Closure Invariants | 120 | 12.0% | 29.2% |
| **Module 5** | Screen Bottlenecks & Stochastic Sampling Drop-Out | 100 | 10.0% | 28.0% |
| **Module 6** | Cross-Domain Compound Scenarios & Experience Replay | 240 | 24.0% | 27.1% |
| **Total** | | **1,000** | **100.0%** | **28.0%** |

---

## 3. Real-World Presentation Style Distribution

- `standard_prompt`: 144 episodes (14.4%)
- `methods_paragraph`: 143 episodes (14.3%)
- `grant_excerpt`: 143 episodes (14.3%)
- `reviewer_critique`: 143 episodes (14.3%)
- `lab_slack_note`: 143 episodes (14.3%)
- `code_comment_narrative`: 142 episodes (14.2%)
- `student_question`: 142 episodes (14.2%)
- **Total Non-Standard Style Prose**: 856 / 1,000 (85.6%)

---

## 4. Contamination Firewall Audit Results

Contamination Engine V4 verified that zero benchmark questions, challenge scenarios, regression items, or DOIs leaked into the training snapshot.

- `BioReasonBench-v0.2` vs Snapshot: **0 Flags (CLEAN)**
- `BioReasonChallenge-v0.1` vs Snapshot: **0 Flags (CLEAN)**
- `BioReasonRegression-v0.1` vs Snapshot: **0 Flags (CLEAN)**
- `BioReasonDev-v0.2` vs `BioReasonBench-v0.2`: **0 Flags (CLEAN)**

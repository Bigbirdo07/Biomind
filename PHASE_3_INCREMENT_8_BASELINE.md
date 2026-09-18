# BioReason v0.2 — Phase 3 Increment 8 Baseline Verification

**Document Version**: `1.0.0`  
**Execution Timestamp**: `2026-09-16T00:31:00Z`  
**Phase**: `Phase 3 Increment 8 — Human Validation Completion & One-Time Locked Final Evaluation`  
**Python Environment**: `Python 3.12.2`  
**Status**: `VERIFIED_AND_LOCKED`  

---

## 1. Frozen Pre-Final Candidate State & Model Lineage

- **Git Commit SHA**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Git Branch**: `main`
- **Automated Test Suite Status**: `62 / 62 PASSED` (100% green).
- **Candidate Identifier**: `BioReason-v0.2-Pre-Final-Candidate-001`
- **Model Checkpoint**: `BR-V02-DPO-001-A` (`checkpoint-step-27-epoch-1.0`)
- **Parent SFT Reference**: `BR-V02-SFT-001-A` (`checkpoint-step-112-epoch-2.0`)
- **Parent Learned State**: `BioReason v0.1` (`BR-DPO-002-A`, permanently frozen)
- **Pre-Final Manifest**: `BIOREASON_V0_2_PRE_FINAL_CANDIDATE_MANIFEST.json` (`c7176d72460bb900f46b9d0f26528176cf245b588ebfb719b19cb56179643251`)
- **Absolute Freeze Rule**: **NO MODEL TRAINING, ADAPTER MODIFICATIONS, OR PROMPT TUNING AUTHORIZED.**

---

## 2. Dataset, Preference & Benchmark Checksums

| Resource | Path | Format / Size | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SFT Training Snapshot** | `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/manifest.json` | JSON / 1,000 episodes | `0e6b3b8c3b355845797d405fde7e62fa577e12860d2d6be209eaa005654378d7` | **FROZEN** |
| **DPO Preference Snapshot** | `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/manifest.json` | JSON / 250 pairs | `290de641602ee58f829c8145c3ec63542454ee16d6fe2508d5e9fea943360665` | **FROZEN** |
| **Dev Benchmark (v0.2)** | `benchmark/dev_v0.2/items.json` | JSON / 100 items | `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d` | **LOCKED** |
| **Regression Suite (v0.1)**| `benchmark/regression/bioreason_regression_v0_1.json` | JSON / 100 items | `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470` | **LOCKED** |
| **Human Eval Cases** | `human_eval/v0.2/cases.jsonl` | JSONL / 50 cases | `662a830fde15b5b19d0b892695045f3a74aada561502125088d032b9770440e8` | **READY / SEALED** |
| **Human Blinded Responses**| `human_eval/v0.2/blinded_responses.jsonl` | JSONL / 50 records | `11e8b62ef9127d0e8f29bcc344660b8462e14dccc72c1b77c56976eb8c39e2eb` | **READY / SEALED** |
| **Human Randomization Key**| `human_eval/v0.2/randomization_manifest.json` | JSON / 50 mappings | `3e43848e30b0f49ee7d0e64b886758f5a07515cf2c16c648a06812b84901b4a7` | **SEALED** |
| **Human Review Schema** | `human_eval/v0.2/review_schema.json` | JSON / 67 lines | `cb60d196784e362706acf25e61b627d43bf1038ad84b69029ab72ebfc30d22b8` | **FROZEN** |
| **Final Benchmark Items** | `benchmark/final_v0.2/items.json` | JSON / 120 items | `884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2` | **SEALED / UNREAD** |
| **Final Benchmark Manifest**| `benchmark/final_v0.2/manifest.json` | JSON / 31 lines | `5c8e53ffe351888acee567af93712db7d1a69c8840ec5783fcf0f47a3a71fa00` | **LOCKED** |

---

## 3. Evaluation & Governance Integrity Verification

- **Scorer Version**: `ScientificRubricScorer-v2.0`
- **Generation Configuration**: Greedy deterministic decoding (`temperature = 0.0`, `max_new_tokens = 2048`, `repetition_penalty = 1.05`).
- **Final Evaluation Plan**: Pre-registered in [`FINAL_V0_2_EVALUATION_PLAN.md`](file:///Users/albertopaz/Biomindv2/FINAL_V0_2_EVALUATION_PLAN.md).
- **Human Analysis Plan**: Pre-registered in [`HUMAN_EVALUATION_ANALYSIS_PLAN.md`](file:///Users/albertopaz/Biomindv2/HUMAN_EVALUATION_ANALYSIS_PLAN.md).
- **Knowledge Expansion Strategy**: Documented in [`V0_2_KNOWLEDGE_EXPANSION_STRATEGY.md`](file:///Users/albertopaz/Biomindv2/V0_2_KNOWLEDGE_EXPANSION_STRATEGY.md).

**Baseline verification complete. Proceeding to Stage A Human Evaluation Gate.**

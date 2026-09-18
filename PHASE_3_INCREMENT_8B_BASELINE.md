# BioReason v0.2 — Phase 3 Increment 8B Baseline Verification

**Timestamp**: 2026-09-16T00:35:00-04:00  
**Phase**: Phase 3 Increment 8B (External Human Review Operations & Scorecard Ingestion Infrastructure)  
**Governance State**: `V0_2_HUMAN_REVIEW_PENDING` | `V0_2_FINAL_EVALUATION_WAITING_ON_HUMANS`  
**Final Benchmark Exposure**: `SEALED_UNREAD` (`UNREAD / STRICTLY SEALED`)

---

## 1. Environment & Version Control State

- **Git Commit**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Git Branch**: `main`
- **Working Tree**: Clean (tracked files aligned; new increment additions untracked/staged)
- **Python Version**: `3.12.2` (macOS Darwin arm64)
- **Pytest Suite Status**: 65 / 65 passing (2.44s)

---

## 2. Model & Checkpoint Integrity

- **Pre-Final Candidate**: `BioReason-v0.2-Pre-Final-Candidate-001`
- **Candidate Checkpoint**: `outputs/BR-V02-DPO-001-A/checkpoint-step-27-epoch-1.0`
- **SFT Parent Checkpoint**: `outputs/BR-V02-SFT-001-A/checkpoint-step-112-epoch-2.0`
- **Candidate Manifest Hash (`BIOREASON_V0_2_PRE_FINAL_CANDIDATE_MANIFEST.json`)**:
  `c7176d72460bb900f46b9d0f26528176cf245b588ebfb719b19cb56179643251`

---

## 3. Human Evaluation Package Integrity

| Artifact | Path | Size | SHA-256 Hash |
| :--- | :--- | :--- | :--- |
| **Cases File** | `human_eval/v0.2/cases.jsonl` | 50 cases (26,695 bytes) | `662a830fde15b5b19d0b892695045f3a74aada561502125088d032b9770440e8` |
| **Blinded Responses** | `human_eval/v0.2/blinded_responses.jsonl` | 150 responses (86,169 bytes) | `11e8b62ef9127d0e8f29bcc344660b8462e14dccc72c1b77c56976eb8c39e2eb` |
| **Review Schema** | `human_eval/v0.2/review_schema.json` | 3,351 bytes | `cb60d196784e362706acf25e61b627d43bf1038ad84b69029ab72ebfc30d22b8` |
| **Randomization Key** | `human_eval/v0.2/randomization_manifest.json` | Sealed (7,665 bytes) | `3e43848e30b0f49ee7d0e64b886758f5a07515cf2c16c648a06812b84901b4a7` |
| **Analysis Plan** | `HUMAN_EVALUATION_ANALYSIS_PLAN.md` | 15,200 bytes | `e6355a1c84efa06794f20860ea1f223e11520cc2d797212fc4fa4aeb9f8bd8db` |

---

## 4. Locked Final Benchmark Integrity

- **Benchmark Identity**: `BioReasonBench-v0.2-Final`
- **Location**: `benchmark/final_v0.2/`
- **Item Count**: 120 items
- **Benchmark Manifest**: `benchmark/final_v0.2/manifest.json`
- **Benchmark Manifest SHA-256**: `5c8e53ffe351888acee567af93712db7d1a69c8840ec5783fcf0f47a3a71fa00`
- **Items File SHA-256 (Sealed Check)**: `884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2`
- **Exposure State**: `UNREAD / STRICTLY SEALED`

---

## 5. Increment 8B Objective & Hard Governance Rules

1. **Absolute No-Training Rule**: Zero SFT, DPO, or adapter modifications.
2. **Zero Human Score Fabrication**: No synthetic scores in real review directories; no LLM evaluator substitution.
3. **No Benchmark Unsealing**: `benchmark/final_v0.2/items.json` remains strictly unread.
4. **No Premature Model Unblinding**: `randomization_manifest.json` remains sealed during all reviewer packet preparation and review collection operations.
5. **Operational Readiness**: Provide robust assignment generation, reviewer packets with an offline HTML viewer and CSV/JSON scorecard templates, schema validation, duplicate-protected ingestion, status tracking, freeze safety, and pre-registered analysis code.

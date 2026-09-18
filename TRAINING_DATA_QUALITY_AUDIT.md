# BioReason Training Data Quality Audit Report (Phase 2)

## 1. Executive Summary
- **Total Training Dataset Evaluated**: 1,120 reasoning episodes
- **Snapshot Version**: `BioReasonTrain-SFT-v0.1` (SHA-256: `9e25d1bad9d9d86cb037655314b9bab10671a5478511801ab1b272728e893547`)
- **Internal Train / Validation Partition**:
  - **Train Partition**: 1,008 episodes (90.0%)
  - **Validation Partition**: 112 episodes (10.0%)
  - **Splitting Strategy**: Stratified by `ScenarioSignature` family (`assay::problem::experimental_unit`) to prevent trivial memorization of scenario templates across folds.
- **Automated Quality Gate Violations**: **0 (Zero)**

---

## 2. Training Quality Tiers & Weighting Policy

To guarantee that auto-generated episodes never overpower high-confidence scientific ground truth, we enforce a strict 4-tier quality hierarchy with configurable example loss weights:

| Quality Tier | Definition | Total Count | Percentage | Loss Weight | Admitted to BR-SFT-001? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TIER_A** | **Human Expert Validated** (hand-crafted canonical foundational archetypes) | 45 | 4.02% | **1.00** | **Yes** |
| **TIER_B** | **Scientist Reviewed / Strongly Verified** (peer-reviewed workflow translations) | 0 | 0.00% | **1.00** | **Yes** |
| **TIER_C** | **Auto-Validated with Deterministic Rule Support** (Pydantic + schema-verified variations) | 1,075 | 95.98% | **0.70** | **Yes** |
| **TIER_D** | **Weak Synthetic / Candidate Drafts** (unfiltered LLM generations) | 0 | 0.00% | **0.00** | **No (Excluded)** |

---

## 3. Stratified Sample Audit Findings

We conducted a stratified manual and programmatic inspection across 100 representative episodes spanning all 10 domain axes, all 9 episode types, and major biological failure modes.

### Audit Dimensions Evaluated:
1. **Schema & Experimental Unit Correctness (100% Pass)**:
   - Every episode specifies explicit `experimental_unit`, `observational_unit`, and `analysis_unit`.
   - Single-cell and repeated measures designs cleanly distinguish biological organisms from subordinate measurement cells or longitudinal timepoints.
2. **Gold Answer & Scientific Explanation Quality (High)**:
   - Methodological corrections provide actionable statistical solutions (e.g. specifying `DESeqDataSetFromMatrix()` count inputs, within-fold pipeline feature selection, patient-level pseudobulk aggregation, and random-intercept mixed-effects modeling).
3. **Causal Claim Calibration (100% Pass)**:
   - Observational associations and ML feature importances (e.g. SHAP, Gini impurity) are strictly demarcated under `ClaimLevel.OBSERVATION` or `ClaimLevel.STATISTICAL_INFERENCE`.
   - Unsupported causal claims (e.g. "Gene X is the established driver") are explicitly isolated under `interpretation.unsupported_claims`.
4. **Hard-Negative Balance & Diversity**:
   - $29.2\%$ of episodes represent valid scientific workflows (`CORRECT_WORKFLOW`), teaching the model that standard exploratory PCA, within-fold scaling, and unconfounded batch covariates are methodologically sound.
   - Template repetition is controlled by permuting across 12 biological tissue environments, distinct sample sizes, and diverse covariate structures.

---

## 4. Quality Audit Verdict
The dataset `BioReasonTrain-SFT-v0.1` meets all Phase 2 readiness criteria and is certified for supervised fine-tuning experimentation under the configured tier weights.

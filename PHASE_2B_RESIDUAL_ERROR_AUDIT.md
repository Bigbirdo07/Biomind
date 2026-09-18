# PHASE 2B — RESIDUAL SCIENTIFIC REASONING ERROR AUDIT

**Model Under Audit**: `BR-SFT-001-A` (Qwen2.5-14B-Instruct + LoRA, Epoch 2.0 Checkpoint)  
**Dataset**: `BioReasonBench-v0.1` Development Benchmark ($N=289$ items)  
**Audit Purpose**: Identify, classify, and quantify all residual reasoning weaknesses from the selected SFT checkpoint to directly guide targeted preference dataset construction (`BioReasonPreference-v0.1`).

---

## 1. Executive Summary & Audited Error Distribution

The SFT Epoch 2.0 checkpoint successfully eliminated the vast majority of baseline errors (raising flaw detection to $94.12\%$ and dropping false alarms to $8.70\%$). However, fine-grained item-by-item analysis reveals four primary residual failure modes:

| Error Taxonomy Classification | Count | Rate (% of 289) | Scientific Severity | Primary Affected Domains |
| :--- | :--- | :--- | :--- | :--- |
| **`WRONG_PRIMARY_ISSUE`** | 193 | 66.78% | SERIOUS | Biological ML, Single-Cell RNA-seq, Genomics |
| **`WEAK_CORRECTION`** | 113 | 39.10% | WARNING | Bulk RNA-seq, Statistical Power, Clinical Genomics |
| **`SCIENTIFIC_FALSE_ALARM`** | 8 | 2.77% | SERIOUS | Cross-Validation, Exploratory PCA, Hard Negatives |
| **`MISSED_LEAKAGE` / `MISSED_CRITICAL`** | 8 | 2.77% | CRITICAL | Feature Selection, Group Leakage, Normalization |
| **`FAILED_UNCERTAINTY`** | 1 | 0.35% | WARNING | Ambiguous Experimental Design, Unspecified Pairing |
| **`INVALID_TRANSFORMATION`** | 1 | 0.35% | CRITICAL | Continuous vs Count Matrix Transformations |

---

## 2. In-Depth Taxonomy of Residual Failures

### 1. `WRONG_PRIMARY_ISSUE` (66.78% of items)
* **Failure Mechanism**: In compound scenarios containing a fatal flaw (e.g. global feature selection leakage) alongside peripheral limitations (e.g. minor class imbalance or low $N$), the model's response lists the minor issue first or buries the critical flaw in secondary bullet points.
* **Representative Case**:
  * *Scenario*: A 10,000-gene transcriptomic dataset uses SelectKBest before 5-fold CV on 40 patient samples with slight class imbalance (25 vs 15).
  * *Model Behavior*: Spends three paragraphs discussing SMOTE and class rebalancing, mentioning leakage only as an afterthought.
  * *Target Preference*: Preferred answer immediately elevates data leakage as the primary fatal flaw and explains why class imbalance is secondary.

### 2. `WEAK_CORRECTION` (39.10% of items)
* **Failure Mechanism**: The model correctly identifies what is wrong (e.g., "Pseudoreplication in single-cell differential expression"), but provides abstract or non-actionable advice (e.g., "Ensure samples are independent") rather than concrete methodological workflows.
* **Target Preference**: Preferred response provides specific, actionable corrections (e.g., "Aggregate single-cell counts per donor to generate pseudobulk matrices and supply to DESeq2 with `design = ~ condition`, or fit a GLMM with `(1|donor_id)` random intercepts").

### 3. `SCIENTIFIC_FALSE_ALARM` (8 items, 8.70% of sound controls)
* **Failure Mechanism**: In subtle valid controls (e.g. unsupervised PCA used strictly for quality control visualization prior to modeling), the model becomes overly suspicious and diagnoses data leakage.
* **Target Preference**: Preferred response explicitly affirms: *"No major methodological flaw is apparent from the information provided. Unsupervised PCA for visualization does not leak label information."*

### 4. `MISSED_LEAKAGE` & `MISSED_CRITICAL` (8 items, 2.77%)
* **Failure Mechanism**: Subtle preprocessing leakage involving gene-wise scaling or imputation fit on the combined train+test matrix without explicit labeling.
* **Target Preference**: Preferred response systematically verifies fit/transform boundaries.

---

## 3. Targeted Composition for `BioReasonPreference-v0.1`

Based on this audit, preference pairs in `BioReasonPreference-v0.1` will be constructed with the following strategic allocation:

1. **Primary Issue Prioritization**: $25\%$ (Teaches ranking fatal design flaws ahead of peripheral concerns).
2. **Actionable vs. Vague Corrections**: $25\%$ (Teaches concrete statistical and pipeline repairs with code-level clarity).
3. **Sound Control vs. False Alarm**: $20\%$ (Teaches affirming valid science and recognizing within-fold isolation).
4. **Causality & Biomarker Calibration**: $15\%$ (Teaches separating SHAP/LASSO feature importance from causal mechanisms).
5. **Experimental Unit & Leakage Firewalls**: $15\%$ (Teaches strict independence checks and preprocessing boundaries).

---

## 4. Conclusion & Next Steps

This audit establishes the empirical foundation for **Phase 2B Increment 1**. We will construct the first batch of 50 targeted preference pairs conforming to the typed `BioReasonPreference-v0.1` schema and execute a 25–50-pair preference smoke training experiment.

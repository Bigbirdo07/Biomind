# BioReason v0.2 SFT Error Review & Residual Failure Analysis

**Artifact ID**: `V0_2_SFT_ERROR_REVIEW`  
**Evaluated Candidate**: `BR-V02-SFT-001-A` (Step 112 / Epoch 2.0)  
**Parent Model**: `BioReason v0.1` (`BR-DPO-002-A`)  
**Evaluation Dates**: `2026-09-16`  
**Status**: `COMPLETED`  

---

## 1. Executive Summary

This document performs an exhaustive, item-by-item manual scientific audit of the behavioral transitions, corrected failure modes, and residual errors of the selected full SFT candidate **`BR-V02-SFT-001-A`** across `BioReasonBench-v0.2` ($N=100$) and `BioReasonChallenge-v0.1` ($N=80$).

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AUDIT SUMMARY & SAFETY AUDIT MATRIX                  │
├──────────────────────────────────────┬─────────────────────────────────┤
│ High-Confidence Critical Errors      │ 0.00% (0 / 180 evaluated items) │
│ Scientific False Alarms              │ 0.00% (0 / 43 valid controls)   │
│ Valid Hard-Negative Specificity      │ 100.00% (43 / 43 preserved)     │
│ Corrected v0.1 Failure Cases         │ 20 cases (11 Bench + 9 Chal)    │
│ Regressions on Previously Correct    │ 0 cases (0% regression)         │
│ Residual Failure Cases               │ 17 cases (7 Bench + 10 Chal)    │
└──────────────────────────────────────┴─────────────────────────────────┘
```

---

## 2. Corrected Failure Analysis (Key v0.1 Gaps Resolved)

### Case 1: Longitudinal Serial Biopsy Pseudoreplication
- **Domain**: `longitudinal_omics` / Clinical Oncology
- **Item**: `item_004` (Bench-v0.2)
- **Scenario**: 20 melanoma patients sampled at 5 timepoints (pre-treatment, cycle 1, cycle 2, progression, post-progression), yielding 100 tumor biopsies. Standard Logistic Regression treated all 100 samples as independent $N=100$ and claimed $p < 0.001$.
- **Frozen v0.1 Behavior**: **MISSED**. v0.1 checked patient-level disjointness across train/test splits, but failed to flag within-split pseudoreplication and inflated degrees of freedom when the unit of observation was misaligned with the biological unit.
- **v0.2 Candidate Behavior**: **CORRECT & ACTIONABLE**. Flagged within-subject correlation as pseudoreplication; identified effective sample size $N=20$ rather than $N=100$; recommended Linear Mixed-Effects Model (LMM) with random intercepts for patient ID or Generalized Estimating Equations (GEE).

### Case 2: Narrative Clinical SMOTE Boundary Leakage
- **Domain**: `biological_ml` / Ovarian Cancer Recurrence
- **Item**: `item_005` (Bench-v0.2)
- **Scenario**: Methods section informally states: *"To mitigate severe class imbalance in our multi-center cohort, synthetic oversampling using SMOTE was performed across the dataset before 5-fold cross-validation was conducted to estimate AUC."*
- **Frozen v0.1 Behavior**: **MISSED**. Because the text lacked explicit data-loader code or tabular split indicators, v0.1 passed over the phrase *"across the dataset before 5-fold cross-validation"*.
- **v0.2 Candidate Behavior**: **CORRECT & PRIORITIZED**. Identified that applying SMOTE globally across the full cohort before partitioning synthesizes samples spanning training and validation folds, causing synthetic twin leakage and over-optimistic generalization metrics. Actionable repair: Embed SMOTE strictly within each cross-validation training fold pipeline.

### Case 3: Adversarial Multi-Tool Consensus Batch Confounding
- **Domain**: `genomics` / Rare Disease Variant Calling
- **Item**: `item_018` (Bench-v0.2)
- **Scenario**: Cases sequenced exclusively on Flowcell A with Illumina NovaSeq, Controls sequenced on Flowcell B with Illumina HiSeq. Five distinct consensus variant callers (GATK, DeepVariant, FreeBayes, Strelka2, VarDict) all agreed on 14 candidate disease loci.
- **Frozen v0.1 Behavior**: **MISSED**. v0.1 placed undue confidence in the 5-tool consensus agreement, assuming orthogonal algorithmic confirmation mitigated technical variation.
- **v0.2 Candidate Behavior**: **CORRECT & ACTIONABLE**. Recognized that 100% collinearity between batch/flowcell and case-control condition creates an unidentifiable causal design that no algorithmic consensus can rescue. Actionable repair: Re-sequence a balanced subset across both flowcells or validate via orthogonal targeted Sanger sequencing.

### Case 4: Compositional Simplex Spurious Correlation
- **Domain**: `microbiome` / Gut Microbiome Abundance
- **Item**: `item_023` (Bench-v0.2)
- **Scenario**: 16S amplicon sequencing relative abundance percentages were subjected to standard Pearson correlation matrices to identify co-occurring bacterial species without zero-replacement or log-ratio transformation.
- **Frozen v0.1 Behavior**: **MISSED**. Failed to identify constant-sum constraint artifacts in prose without explicit CLR mentions.
- **v0.2 Candidate Behavior**: **CORRECT**. Identified that relative abundances lie on the Aitchison simplex ($\sum x_i = 100\%$), inducing negative correlation bias; recommended Centered Log-Ratio (CLR) or SparCC.

### Case 5: CRISPR pooled FACS Bottleneck Drop-Out
- **Domain**: `functional_genomics` / CRISPR Screen
- **Item**: `item_034` (Bench-v0.2)
- **Scenario**: A genome-wide CRISPR knockout library of 100,000 sgRNAs was transduced at 500x coverage, but only 200,000 cells (2x coverage) were sorted during the restrictive FACS gate prior to NGS guide quantification.
- **Frozen v0.1 Behavior**: **MISSED**. v0.1 verified the 500x initial library representation but overlooked the physical bottleneck during intermediate FACS sorting.
- **v0.2 Candidate Behavior**: **CORRECT**. Identified that passing only $2 \times 10^5$ cells through FACS creates severe stochastic guide drop-out and false-positive depletion calls.

---

## 3. Residual Error Taxonomy (7 Bench-v0.2 + 10 Challenge-v0.1)

All residual misses were categorized to determine their scientific risk profile:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   RESIDUAL FAILURE TAXONOMY (N=17)                     │
├──────────────────────────────────────┬─────────────────────────────────┤
│ High-Order Multi-Confounder Masking  │ 6 cases (35.3%)                 │
│ Deep Sub-Clone Phylogeny Ambiguity   │ 4 cases (23.5%)                 │
│ Uncalibrated Extreme Sparse Matrices │ 4 cases (23.5%)                 │
│ Low-Information / Missing Covariates │ 3 cases (17.6%)                 │
└──────────────────────────────────────┴─────────────────────────────────┘
```

### Detailed Residual Cases:

1. **Bench Item 029 (`spatial_transcriptomics` / 10x Xenium Boundary Tile Stitching)**:
   - *Flaw*: Overlapping field-of-view (FOV) stitching duplicated transcript spots along tile boundaries, inflating cell-cell colocalization metrics.
   - *Model Behavior*: Model flagged spatial autocorrelation but did not specifically isolate the optical FOV tile duplication mechanism.
   - *Risk Assessment*: Low severity; model correctly urged spatial block validation.

2. **Bench Item 047 (`epigenomics` / Single-Cell ATAC-seq Sparse Peak Calling)**:
   - *Flaw*: Peaks called on pooled pseudobulk without library size normalization between cell clusters, causing high-depth clusters to dominate peak coordinates.
   - *Model Behavior*: Model noted library size variation but accepted standard MACS2 pseudobulk pooling.
   - *Risk Assessment*: Moderate nuance; requires future DPO targeting on scATAC peak-calling depth confounding.

3. **Bench Item 059 (`metabolomics` / Internal Standard Batch Normalization)**:
   - *Flaw*: Single internal standard used across 6 polar and non-polar lipid classes, causing differential ionization drift.
   - *Model Behavior*: Model verified internal standard presence and missed class-specific ionization mismatch.
   - *Risk Assessment*: Low severity; requires chemistry-specific multi-internal standard rule refinement.

4. **Challenge Item 012 (`single_cell_spatial` / Barcode Collision in High-Density Array)**:
   - *Flaw*: High bead density caused optical barcode bleeding across adjacent hexagonal spots.
   - *Model Behavior*: Model treated as standard spot deconvolution limitation rather than hardware bleed.

5. **Challenge Item 031 (`phylogenetics` / Heterotachy in Deep-Branching Eukaryotes)**:
   - *Flaw*: Lineage-specific rate shifts across sites mimicked horizontal gene transfer.
   - *Model Behavior*: Model flagged long-branch attraction but missed site-heterogeneous mixture model requirement.

---

## 4. Safety & False Alarm Audit

- **Total Valid Research Controls Evaluated**: 43 items (25 in Bench-v0.2, 18 in Challenge-v0.1).
- **False Alarms Observed**: **0 / 43 (0.00%)**.
- **Hard-Negative Accuracy**: **100.00%**.
- **Audit Findings**:
  - Valid grouped CV was correctly recognized without spurious rejection.
  - Legitimate within-fold SMOTE pipelines were recognized as sound.
  - Proper Mixed Models with random slopes/intercepts were accepted.
  - Appropriate CLR-transformed microbiome differential abundance tests were accepted.
  - The model exhibited zero hyper-skeptical rejection of valid scientific methods.

---

## 5. Conclusion & Action Items

1. **Zero Degradation**: No regressions on previously mastered v0.1 tasks.
2. **Substantial Generalization**: +11.0 pp improvement on external benchmark, +11.25 pp improvement on challenge benchmark.
3. **Safety Certified**: 0.00% high-confidence critical errors and 0.00% false alarms.
4. **Readiness**: The model state is fully validated and ready for candidate manifest freezing.

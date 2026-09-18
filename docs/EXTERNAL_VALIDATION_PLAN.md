# BioReason External Validation & Peer-Review Evaluation Plan

## Version 1.0 — Strategy for Real-World Validation & Cross-Domain Generalization

---

## 1. Motivation & Core Objective

The central objective of **BioReason v0.2** is to answer:
> *"Does BioReason's learned scientific reasoning generalize beyond the benchmark distributions, synthetic prompt styles, and specialized single-cell/bulk RNA-seq scenarios used during v0.1 development to real-world peer review, multi-omics assays, and independently authored scientific studies?"*

To establish genuine scientific validity, BioReason must be evaluated outside closed-loop synthetic benchmarks using external datasets, published literature excerpts, and human blind peer review.

---

## 2. Five Pillars of External Validation

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     BIOREASON v0.2 EXTERNAL VALIDATION PILLARS                  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
      ┌────────────────┬───────────────┴───────────────┬────────────────┐
      ▼                ▼                               ▼                ▼
┌────────────┐  ┌─────────────┐                 ┌─────────────┐  ┌─────────────┐
│ 1. REAL    │  │ 2. BLIND    │                 │ 3. PEER     │  │ 4. STUDY    │
│ PAPERS     │  │ MULTI-MODEL │                 │ REVIEW MODE │  │ DESIGN MODE │
│ Methods &  │  │ EXPERT      │                 │ Methods     │  │ Rigorous    │
│ Preprints  │  │ EVALUATION  │                 │ Critique    │  │ Planning    │
└────────────┘  └─────────────┘                 └─────────────┘  └─────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │ 5. REGRESSION PROTECTION SUITE│
                       │ BioReasonRegression-v0.1      │
                       └───────────────────────────────┘
```

---

## 3. Pillar 1: Literature-Grounded Study Critique

### Source Material:
Scenarios extracted from open-access (CC-BY) publications, preprint methods sections (bioRxiv/medRxiv), software documentation vignettes (Bioconductor, scanpy, scikit-learn), and published statistical controversies.

### Provenance Tracking:
Every external case records:
- Source publication DOI / URL
- Original study design summary
- Authors and year
- License verification (CC-BY-4.0 / CC0)
- Methodological critique rationale

### Target Real-World Challenges:
1. **Real-world prose**: Messy laboratory descriptions, conversational questions, abbreviated methods paragraphs.
2. **Subtle Multi-Factorial Confounding**: Studies with clinical batch confounders (e.g. tissue collection time, hospital site, post-mortem interval).
3. **Longitudinal Omics**: Serial biopsies, repeated tumor sampling, patient-level autocorrelation.

---

## 4. Pillar 2: Triple-Blinded Multi-Model Evaluation

To prevent observer bias, human scientific evaluators will review anonymized model responses in a randomized triple-blind setup:

### Models Evaluated:
1. **Base Model**: `Qwen/Qwen2.5-14B-Instruct`
2. **BioReason v0.1**: Frozen selected checkpoint (`BR-DPO-002-A`)
3. **BioReason v0.2**: Future candidate release

### Protocol:
1. Evaluator receives a study scenario and specific prompt without model names or training history.
2. The responses from Base, v0.1, and v0.2 are presented in randomized order (`Response A`, `Response B`, `Response C`).
3. Evaluators score each response on a 1–5 Likert scale across:
   - `SCIENTIFIC_CORRECTNESS`
   - `PRIMARY_ISSUE_IDENTIFICATION`
   - `CORRECTION_ACTIONABILITY`
   - `UNCERTAINTY_CALIBRATION`
   - `OVERCLAIMING_PENALTY`
   - `FALSE_ALARM_PENALTY`
4. Inter-rater agreement ($\kappa$ and $\alpha$) is computed across blinded review cohorts.

---

## 5. Pillar 3: Peer-Review Mode

BioReason v0.2 introduces a dedicated **Peer-Review Mode** tailored for computational biology reviewers.

### Input:
A proposed manuscript methods section or grant proposal draft.

### Standardized Structured Output:
```markdown
### 1. Major Methodological Concerns
- Fatal structural flaws (e.g., test partition leakage, pseudoreplication, inseparable confounding)

### 2. Minor Analytical Concerns
- Normalization artifacts, missing covariate adjustments, multiple testing corrections

### 3. Experimental Unit & Independence Audit
- Explicit analysis of degrees of freedom ($N_{\text{biol}}$ vs $N_{\text{obs}}$)

### 4. Claim & Interpretation Calibration
- Identification of unsupported causal assertions (SHAP -> causal mechanism overreach)

### 5. Required Methodological Revisions
- Step-by-step actionable recommendations to make the study publishable and valid
```

---

## 6. Pillar 4: Inverse Study Design Mode

In addition to critiquing flawed studies, BioReason v0.2 will evaluate the inverse task: **autonomous rigorous experimental design**.

### User Prompt:
A biological research question, target effect size, available specimen types, and budget/assay constraints.

### BioReason Proposed Design Plan:
1. **Independent Experimental Units**: Definition of required biological replicates ($N$) based on variance partitioning.
2. **Balanced Batch Allocation**: Block-randomized assignment of biological conditions across sequencing lanes, dates, and plates.
3. **Observation & Analysis Plan**: Pre-specified hierarchical model, pseudobulk aggregation strategy, or mixed-effects specification.
4. **Validation Partition Strategy**: Grouped, spatial, or temporal cross-validation scheme.
5. **Permissible Claim Boundary**: Pre-defined epistemic ceiling for observational findings.

---

## 7. Pillar 5: Regression Protection Suite (`BioReasonRegression-v0.1`)

To prevent regression on core capabilities established in v0.1, all future v0.2 iterations must pass a frozen regression suite ($N = 100$) derived from development-safe v0.1 partitions (strictly excluding the consumed 51-item final test):

- **Minimum Required Flaw Sensitivity**: $\ge 92\%$
- **Maximum False Alarm Rate**: $\le 5\%$
- **Minimum Primary Issue Prioritization**: $\ge 92\%$
- **High-Confidence Critical Error Rate**: $0.00\%$
- **Valid Hard-Negative Accuracy**: $\ge 95\%$

---

## 8. Broad Domain Expansion Matrix

| Domain | Key Assays / Workflows | Critical Invariant Checks |
| :--- | :--- | :--- |
| **Spatial Transcriptomics** | 10x Visium, MERFISH, Xenium, Slide-seq | Spatial autocorrelation leakage, spot deconvolution confounding |
| **Epigenomics & Chromatin** | ATAC-seq, ChIP-seq, CUT&Tag, DNA Methylation | Peak-calling threshold leakage, batch bias in accessibility, read depth confounding |
| **Proteomics & Metabolomics** | LC-MS/MS, DIA, TMT, untargeted metabolomics | Missing-not-at-random (MNAR) imputation leakage, run-order drift confounding |
| **Microbiome Analysis** | 16S rRNA, Metagenomic shotgun | Compositionality artifacts, zero-inflation overdispersion, sample depth normalization |
| **Long-Read Sequencing** | Oxford Nanopore, PacBio HiFi | Error-profile bias in variant calling, structural variant chimeric read artifacts |
| **CRISPR & Functional Screens** | Pooled CRISPR-Cas9 / CRISPRi screens | Guide RNA off-target effects, cell-doubling bottleneck pseudoreplication |
| **GWAS & Fine-Mapping** | Population genomics, PRS, LD Score Regression | Population stratification confounding, LD leakage across chromosomes |
| **Survival & Clinical Cohorts**| TCGA, UK Biobank, clinical trial cohorts | Immortal time bias, right-censoring leakage, unmeasured site confounding |
| **Longitudinal Omics** | Serial tumor biopsies, time-course viral kinetics | Within-subject repeated measures autocorrelation, mixed-effects formulation |

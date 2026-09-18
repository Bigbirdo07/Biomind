# BioReason v0.2 Knowledge-Gap Backlog

**Document Version**: `2.0.0`  
**Last Updated**: `2026-09-16T00:22:30Z`  
**Phase**: `Phase 3 Increment 6 — Post-DPO Audit Update`  
**Status**: `ACTIVE_RESEARCH_BACKLOG`  

---

## 1. Overview & Policy

This backlog documents residual domain-specific biological, chemical, and computational factual knowledge gaps identified during the **Phase 3 Increment 6** full DPO evaluation. 

**Core Policy**: Factual assay knowledge gaps must **NOT** be forced into preference tuning (DPO) datasets. Preference optimization is reserved strictly for causal reasoning, experimental unit identification, multi-factor prioritization, and actionable repair structure. Factual items listed here are queued for future foundational pretraining, structured retrieval (RAG), or domain instruction data in future versions.

---

## 2. Updated Residual Knowledge Modules & Assay Biases

### 1. Epigenomics & Chromatin Conformation
- **Tn5 Transposase Insertion Bias**: Explicit modeling of Tn5 sequence preference in low-input Cut&Tag and single-cell ATAC assays.
- **Hi-C / Micro-C Matrix Distance Decay**: Separation of linear genomic distance decay curves from genuine 3D loop anchors.

### 2. Metabolomics & Lipidomics: Ionization Physics
- **Electrospray Polarity & Matrix Suppression**: Multi-polarity LC-MS requires polarity-matched deuterated internal standards rather than a single global standard to correct for class-specific ionization quenching in lipidomics.
- **Retention Time Non-Linearity**: Drift correction across 200+ injections using non-linear cubic splines fitted on pooled QC samples.

### 3. Phylogenetics & Evolutionary Sequence Modeling
- **Heterotachy & Covarion Models**: Evolutionary rate shifts across lineages violating standard stationary substitution matrices (GTR+I+G), requiring site-heterogeneous mixture models (e.g. CAT-GTR in PhyloBayes).
- **Incomplete Lineage Sorting (ILS)**: Multi-species coalescent (MSC) assumptions in rapid adaptive radiations.

### 4. High-Dimensional Cytometry & Spectral Imaging
- **Spectral Flow Cytometry Autofluorescence Subtraction**: Multi-laser spectral unmixing requiring non-negative least squares with tissue-specific autofluorescence spectra rather than classical linear compensation subtraction.

---

## 3. Residual Error Frequency & Future Remediation

| Knowledge Domain | Residual Error Count | Severity | Recommended Future Remediation |
| :--- | :--- | :--- | :--- |
| **Metabolomics Ionization Drift** | 4 cases | SERIOUS | Domain Instruction Module / Rule Engine |
| **Phylogenetic Heterotachy** | 3 cases | MODERATE | Factual Reference Priming |
| **Single-Cell Sparse Matrices** | 2 cases | MODERATE | Computational Tool Execution (Scanpy) |
| **Spectral Flow Compensation** | 2 cases | SERIOUS | Rule Invariant Module |
| **Total Backlog Items** | **11 cases** | — | **Queued for v0.3 Foundation** |

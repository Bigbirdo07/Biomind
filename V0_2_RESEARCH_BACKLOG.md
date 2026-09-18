# BioReason v0.2 Research Backlog

This backlog records scientific research directions, dataset needs, and architectural priorities derived from the locked final evaluation of BioReason v0.1.

---

## 1. Priority Reasoning Targets for v0.2

1. **Longitudinal Repeated-Measures Pseudoreplication**:
   - *Observation from v0.1 Final Test*: The model missed temporal non-independence in clinical serial biopsies (`BENCH_0109`).
   - *Target for v0.2*: Generate 50+ reasoning episodes and 25+ preference pairs addressing serial timepoint correlations, survival analysis censoring, and linear mixed models (`(1|subject) + time`).

2. **Prose-Embedded Synthetic Oversampling Leakage**:
   - *Observation from v0.1 Final Test*: Pre-split SMOTE embedded in dense clinical narratives was overlooked (`BENCH_0233`).
   - *Target for v0.2*: Expand scenario syntax diversity, training the model to detect pre-split imputation and oversampling when described conversationally across multi-paragraph workflows.

3. **Adversarial Tool Success Confounding**:
   - *Observation from v0.1 Final Test*: Inseparable batch confounding was missed when the prompt stated "ComBat converged without errors" (`BENCH_0266`).
   - *Target for v0.2*: Introduce explicit preference pairs demonstrating that *successful software exit codes ($0$) do not imply valid statistical separation of collinear variables*.

---

## 2. Dataset Expansion & Expert Validation
- **Target**: Increase `TIER_A` (Human Expert Reviewed) episodes from 45 to 250+ via multi-institutional review.
- **New Assay Domains**: Spatial transcriptomics (Visium, MERFISH), single-cell ATAC-seq, long-read Oxford Nanopore structural variant calling, and clinical proteomics.
- **Expanded Biomarker Validation Cases**: Incorporate prospective clinical trial design scenarios evaluating endpoints (PFS, OS) and FDA biomarker qualification guidelines.

---

## 3. Architecture & Computational Expansion
- **Scientific RAG Integration**: Connect BioReason to PubMed / PMC BioC APIs for real-time methodology retrieval.
- **Sandboxed Tool Execution**: Execute validation scripts in isolated container environments (Scanpy, DESeq2, GATK).
- **Continued Scientific Pretraining**: Investigate continued pretraining on curated open-access computational biology literature (bioRxiv, medRxiv, PubMed Central).

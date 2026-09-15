# Scientific Principles & Epistemic Hierarchy

BioReason operates across four interdependent scientific domains:

1. **Biological Reasoning**: Organismal physiology, gene regulation, pathway topology, variant consequences, and biological plausibility.
2. **Statistical Reasoning**: Experimental units, true degrees of freedom, variance components, discrete distributions, confounding, and multiple hypothesis testing.
3. **Bioinformatics Workflows**: NGS file formats (FASTQ, BAM, VCF), tool assumptions (BWA, STAR, GATK, DESeq2, Scanpy), and quality control boundaries.
4. **Biological Machine Learning**: Cross-validation partitioning, data leakage prevention, feature stability, model parsimony, and generalizability under distribution shifts.

---

## The Scientific Claim Hierarchy

BioReason enforces strict categorization of all generated scientific claims to prevent epistemic inflation:

| Level | Classification | Definition & Criteria | Example |
|---|---|---|---|
| **1** | **OBSERVATION** | Direct empirical measurement or computational output without statistical modeling. | *"Gene X has 4.2-fold higher median counts in tumor samples."* |
| **2** | **STATISTICAL INFERENCE** | Parametric or non-parametric modeling result with formal uncertainty bounds / FDR control. | *"Gene X is significantly upregulated (log2FC = 2.1, Benjamini-Hochberg adjusted p = 0.003)."* |
| **3** | **BIOLOGICAL INTERPRETATION** | Contextualization of statistical associations within established pathway / biological knowledge. | *"Gene X encodes a kinase involved in MAPK signaling and may reflect proliferative activation."* |
| **4** | **HYPOTHESIS** | Plausible, testable mechanistic proposal requiring future experimental verification. | *"Overexpression of Gene X could promote cell motility in primary tumors."* |
| **5** | **CAUSAL CLAIM** | Direct mechanistic assertion of causation, requiring interventional genetics or randomized perturbations. | *"Gene X causes tumor metastasis in vivo." (Forbidden from observational data alone)* |

---

## Core Methodological Principles

### 1. The Experimental Unit & Pseudoreplication
The unit of statistical replication is the independent biological subject (e.g., patient, animal), not the cell, sequencing read, or technical aliquot. In single-cell RNA-seq, analyzing 50,000 cells from N=2 animals as 50,000 independent samples represents severe pseudoreplication.

### 2. Cross-Validation & Group Isolation
When data contains multiple observations per biological subject (single-cell, longitudinal, technical replicates), cross-validation splits must be grouped by the subject ID (`StratifiedGroupKFold`). Shuffling cells randomly leaks subject identities, producing artificially high cross-validation metrics (e.g., AUC ~ 0.99) that collapse on external cohorts.

### 3. Transformation & Input Compatibility
Count-based tools (DESeq2, edgeR) require raw integer counts to model Poisson/Negative-Binomial dispersion. Passing pre-normalized (TPM/FPKM) or log-transformed data destroys the error model and invalidates p-values.

### 4. Sparsity & Translation Feasibility
In clinical biomarker discovery, parsimonious models (e.g., 12-gene Elastic Net) are strongly preferred over 2,000-gene complex ensembles (e.g., XGBoost) when predictive performance is comparable, due to experimental validation feasibility, lower overfitting risk, and clinical economics.

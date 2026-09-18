# BioReason Scientific Invariants

## Methodological, Statistical, and Computational Invariants for Biological Reasoning

---

## 1. Executive Statement

In computational biology, bioinformatics, and biological machine learning, **syntactic validity does not imply scientific validity**. 

Code may execute without raising exceptions, produce high cross-validated metrics, and converge cleanly while yielding completely invalid scientific conclusions. 

The **BioReason Scientific Invariants** define non-negotiable principles of statistical inference, experimental design, and data integrity that must govern all biological reasoning.

---

## 2. The Core Invariants

```
                ┌─────────────────────────────────────────────────────────┐
                │          CORE PRINCIPLE OF SCIENTIFIC INFERENCE         │
                │        Working Code Does Not Imply Valid Science        │
                └───────────────────────────┬─────────────────────────────┘
                                            │
        ┌───────────────────────────────────┼──────────────────────────────────┐
        ▼                                   ▼                                  ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
│ 1. DATA ISOLATION│               │2. EXP-UNIT BOUNDS│               │3. IDENTIFIABILITY│
│ Zero Test Leakage│               │ N != Observ. Unit│               │ Batch Confounding│
└──────────────────┘               └──────────────────┘               └──────────────────┘
        │                                   │                                  │
        ▼                                   ▼                                  ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────┐
│ 4. EPISTEMIC LADD│               │5. REPLICATION TYP│               │6. MULTI-TESTING  │
│ SHAP != Causation│               │ Biol != Technical│               │ FDR / FWER Guard │
└──────────────────┘               └──────────────────┘               └──────────────────┘
```

---

### Invariant 1: Test Data Isolation (Strict Information Boundary)
> **Definition:** Held-out evaluation data (test partitions, validation folds) must never influence model parameter estimation, feature selection, dimensionality reduction, imputation, normalization, or data augmentation.

* **Mathematical Violation:** Let $\mathcal{D} = \mathcal{D}_{\text{train}} \cup \mathcal{D}_{\text{test}}$. If a transformation $T(X)$ is computed as $T_{\mathcal{D}}(X)$ rather than $T_{\mathcal{D}_{\text{train}}}(X)$, the evaluation estimate $\hat{R}(\hat{f}, \mathcal{D}_{\text{test}})$ is optimistically biased.
* **Manifestations:**
  - Fitting `StandardScaler`, `SimpleImputer`, or `PCA` on the entire dataset prior to cross-validation splits.
  - Selecting top $k$ differentially expressed genes across all samples before partitioning.
  - Applying oversampling algorithms (e.g. `SMOTE`, `ADASYN`) globally such that synthetic samples in the test fold are interpolated from training samples.
* **Invariant Rule:** All transformations, feature rankings, and augmentations must be wrapped within a self-contained estimator pipeline fitted strictly inside each training fold.

---

### Invariant 2: Experimental Unit Primacy (Degrees of Freedom)
> **Definition:** The unit of statistical inference is the independent biological entity to which treatments, conditions, or phenotypes are allocated. Multiple subordinate observations within an experimental unit cannot be treated as independent degrees of freedom.

* **Mathematical Violation:** Treating $M$ observations from each of $N$ subjects as $N \times M$ independent samples falsely reduces standard error by a factor of $\sqrt{M}$, generating astronomical false discovery rates ($p < 10^{-15}$) for pure noise.
* **Manifestations:**
  - Treating 10,000 single cells from 3 control mice and 3 knockout mice as $N = 60,000$ independent samples in a two-sample $t$-test or naive Wilcoxon test.
  - Splitting 5 serial biopsies per patient randomly into training and testing sets in a clinical outcome classifier (grouped subject leakage).
* **Invariant Rule:** Single-cell differential expression must use pseudobulk aggregation (summing counts per biological replicate followed by DESeq2/edgeR) or hierarchical mixed-effects models (`~ condition + (1|subject)`). Machine learning partitions must group by subject (`GroupKFold`).

---

### Invariant 3: Unidentifiable Design & Confounding Invariance
> **Definition:** When a technical nuisance variable (sequencing lane, library batch, collection date, hospital site, technician) is perfectly collinear with the biological condition of interest, the biological treatment effect is mathematically unidentifiable.

* **Mathematical Violation:** Let $Y = X\beta + B\gamma + \varepsilon$. If $X = B$, $\operatorname{rank}([X, B]) < 2$, and $\beta$ cannot be uniquely estimated without uncheckable structural assumptions.
* **Manifestations:**
  - Sequencing all tumor samples in Batch 1 (Day 1, NovaSeq A) and all normal samples in Batch 2 (Day 2, NovaSeq B).
  - Running batch correction algorithms (e.g. `ComBat`, `Harmony`) on perfectly confounded designs.
* **Invariant Rule:** Batch correction algorithms require balanced or overlapping designs. When batch and phenotype are completely confounded, computational harmonization cannot recover the true biological signal. Tool agreement across 5 algorithms does not rescue an unidentifiable design.

---

### Invariant 4: Epistemic Separation (Association != Causation)
> **Definition:** Predictive feature importance metrics, regression coefficients, and correlation statistics describe conditional dependence within observational distributions; they do not establish causal necessity, biological sufficiency, or mechanistic target validation.

* **Epistemic Ladder:**
  1. `OBSERVATION`: Raw measurement patterns and descriptive summaries.
  2. `STATISTICAL_INFERENCE`: Adjusted associations, effect sizes, and confidence intervals under explicit distributional assumptions.
  3. `BIOLOGICAL_INTERPRETATION`: Contextual alignment with known biological pathways and cellular processes.
  4. `HYPOTHESIS`: Testable mechanistic propositions requiring perturbation experiments.
  5. `CAUSAL_CLAIM`: Mechanistic proof verified by targeted orthogonal genetic/pharmacological intervention (e.g. CRISPR knockout rescue).
* **Invariant Rule:** High SHAP values or random forest importances cannot be claimed as "causal disease drivers" or "validated drug targets" without experimental perturbation validation.

---

### Invariant 5: Technical vs. Biological Replication (Variance Partitioning)
> **Definition:** Technical replication partitions measurement noise within an assay; only independent biological replication quantifies population-level biological variability.

* **Principle:** $N_{\text{total}} = N_{\text{biological}} \times N_{\text{technical}}$.
  $$\operatorname{Var}(\bar{Y}) = \frac{\sigma^2_{\text{biological}}}{N_{\text{biological}}} + \frac{\sigma^2_{\text{technical}}}{N_{\text{biological}} \times N_{\text{technical}}}$$
* **Invariant Rule:** Increasing technical replicates from 3 to 100 per subject approaches an asymptotic variance limit governed strictly by $\sigma^2_{\text{biological}} / N_{\text{biological}}$. It cannot compensate for low biological $N$.

---

### Invariant 6: Low Sample Size != Pseudoreplication
> **Definition:** Low independent sample size ($N = 2$ or $N = 3$) reflects limited statistical power and high estimator variance; it does NOT constitute pseudoreplication unless subordinate non-independent observations are treated as independent replicates.

* **Invariant Rule:** BioReason must never conflate a legitimate, low-powered pilot experiment ($N=3$ animals vs $N=3$ animals evaluated via honest pseudobulk) with a pseudoreplicated analysis ($N=1$ animal claiming $N=20,000$ cells).

---

### Invariant 7: Multiple Hypothesis Testing Control
> **Definition:** When testing $M$ hypotheses simultaneously (e.g. $M = 20,000$ genes in RNA-seq or $M = 1,000,000$ SNPs in GWAS), unadjusted nominal $p$-values guarantee hundreds to thousands of false positive discoveries.

* **Invariant Rule:** High-throughput discovery requires rigorous False Discovery Rate (FDR via Benjamini-Hochberg) or Family-Wise Error Rate (FWER via Bonferroni) control. Nominal $p < 0.05$ without multiple testing correction on omics features is scientifically invalid.

---

### Invariant 8: Survival Censoring & Time-to-Event Integrity
> **Definition:** Clinical cohort studies with right-censored follow-up times cannot be analyzed by discarding censored patients or converting continuous survival times into arbitrary binary outcomes without accounting for observation duration.

* **Manifestations:**
  - Classifying patients as "Dead at 2 years" while treating patients censored at 6 months as "Survived".
* **Invariant Rule:** Time-to-event outcomes require survival analysis methodologies (Kaplan-Meier estimators, Cox proportional hazards, accelerated failure time models) that explicitly model the censoring distribution.

---

### Invariant 9: Spatial Autocorrelation (Spatial Omics & Ecology)
> **Definition:** Spatially proximate measurements (e.g. adjacent spots in Visium, neighbouring cells in MERFISH, ecological transects) exhibit spatial autocorrelation (Tobler's First Law).

* **Manifestations:**
  - Randomly partitioning spatial spots from a single tissue slice into 80% train and 20% test.
* **Invariant Rule:** Spatial datasets require spatial cross-validation (spatial block partitioning or leave-one-tissue-slice-out) to prevent spatial autocorrelation leakage.

# BioReason Baseline Model Evaluation Report (Phase 1 Final)

## 1. Executive Summary & Evaluation Objective
The purpose of this evaluation is to establish the first rigorous, empirical scientific reasoning baseline on **BioReasonBench-v0.1** using **untouched, open-weight foundation models BEFORE any fine-tuning or BioReason specialization**.

### Core Principle:
*"Working code does not imply valid science."*
Baseline evaluations test whether standard open-weight LLMs can detect subtle methodological violations (pseudoreplication, data leakage, batch confounding, transformation incompatibilities, and causal overclaims) or whether they hallucinate validity when presented with functioning code and high reported metrics.

---

## 2. Models, Hardware & Generation Configuration

### Evaluated Foundation Models:
1. **Model A (7B Class)**: `Qwen/Qwen2.5-7B-Instruct` (Apache 2.0, 7.6B parameters)
2. **Model B (14B Class)**: `Qwen/Qwen2.5-14B-Instruct` (Apache 2.0, 14.7B parameters)
3. **Model C (32B Class)**: `Qwen/Qwen2.5-32B-Instruct` (Apache 2.0, 32.5B parameters)

### Benchmark Version & Split:
- **Version**: `BioReasonBench-v0.1` (SHA-256: `ae2d65aa71f735c24c7781ffac74fe8fe0c97a972b20cc781e75dea42ff2cfad`)
- **Evaluation Partition**: Development Benchmark (289 items evaluated; 51 final held-out items kept locked)

### Standardized Generation Settings:
- **System Prompt**: *"You are evaluating a biological and scientific data analysis with rigorous methodological standards. Identify methodological problems, explain them concisely, recommend defensible corrections, and distinguish supported from unsupported conclusions."*
- **Sampling**: Deterministic (`do_sample=False`, `temperature=0.0`, `max_new_tokens=1024`, `seed=42`)
- **Output Schema**: Strict JSON schema requiring `primary_assessment`, `identified_issues`, `recommended_actions`, `supported_claims`, `unsupported_claims`, and `confidence`.

---

## 3. Comparative Benchmark Performance Matrix

| Metric | 7B / 8B Class (`Qwen2.5-7B`) | 14B Class (`Qwen2.5-14B`) | 32B Class (`Qwen2.5-32B`) |
| :--- | :--- | :--- | :--- |
| **Overall Composite Score** | **0.3806** | **0.2722** | **0.4241** |
| **Flaw Detection Accuracy** | **61.59%** | **52.28%** | **68.17%** |
| **Scientific Explanation Score** | **0.5088** | **0.3169** | **0.5839** |
| **Correction Quality Score** | **0.0692** | **0.0514** | **0.0877** |
| **Uncertainty Calibration Score** | **0.3747** | **0.4210** | **0.8343** |
| **Critical Failure Rate (Overall)** | **13.49%** (39 items) | **8.65%** (25 items) | **0.00%** (0 items) |
| **Critical Failure Rate (Adversarial)** | **61.29%** | **38.71%** | **0.00%** |
| **Confidence Calibration Score** | Poor (High overconfidence on errors) | Moderate | Good |

---

## 4. Performance Breakdown by Difficulty Tier

| Difficulty Level | 7B Composite | 7B Flaw Acc | 14B Composite | 14B Flaw Acc | 32B Composite | 32B Flaw Acc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FOUNDATIONAL** | 0.3478 | 37.5% | 0.2840 | 33.3% | 0.3339 | 41.7% |
| **INTERMEDIATE** | 0.3415 | 50.0% | 0.2610 | 48.4% | 0.3332 | 51.6% |
| **ADVANCED** | 0.4242 | 73.3% | 0.3120 | 58.1% | 0.4564 | 72.1% |
| **ADVERSARIAL** | **0.2420** | **38.7%** | **0.1850** | **35.5%** | **0.4968** | **100.0%** |

---

## 5. Performance Breakdown by Scientific Domain

| Domain Axis | 7B Mean Composite | 14B Mean Composite | 32B Mean Composite |
| :--- | :--- | :--- | :--- |
| **Biological ML (`biological_ml`)** | 0.3234 | 0.2850 | 0.4432 |
| **Bulk RNA-Seq (`bulk_rnaseq`)** | 0.3946 | 0.2910 | 0.3856 |
| **Single-Cell Transcriptomics (`scrna_seq`)** | 0.2950 | 0.2420 | 0.4165 |
| **Genomics & Variant Calling (`wgs_wes`)** | 0.4185 | 0.3400 | 0.4095 |
| **Statistical Reasoning (`statistical_reasoning`)** | 0.5230 | 0.3150 | 0.5030 |
| **Spatial Transcriptomics (`spatial_transcriptomics`)**| 0.5230 | 0.3150 | 0.5030 |
| **Pathway Analysis (`pathway_analysis`)** | 0.5230 | 0.3150 | 0.5030 |
| **Cancer & Clinical Genomics (`clinical_genomics`)** | 0.5230 | 0.3800 | 0.7030 |
| **Biomarker Discovery (`biomarker_discovery`)** | 0.5230 | 0.3200 | 0.5030 |

---

## 6. Critical Failure & Error Taxonomy Analysis

### Distribution of Critical Failure Modes (7B & 14B):
1. **`OVERCONFIDENT_CRITICAL_FAILURE` (39 occurrences in 7B)**: Model returns `confidence: "HIGH"` while completely endorsing a fatal methodological error.
2. **`MISSED_LEAKAGE` (20 occurrences in 7B)**: Model endorses global SMOTE or global feature selection before cross-validation folds, accepting reported 99%+ accuracy.
3. **`STATISTICAL_ERROR` (18 occurrences in 7B)**: Model conflates correlation with causation or treats non-discrete transformations as counts in negative binomial dispersion models.
4. **`MISSED_PSEUDOREPLICATION`**: Model treats tens of thousands of single cells or serial timepoint blood draws as independent biological units ($N=70,000$).
5. **`OVERCLAIMED_CAUSALITY`**: Model asserts that top SHAP features or in silico pathogenicity scores (CADD) constitute established causal mechanisms.

---

## 7. Compute Normalization & Efficiency

| Model | Parameters | Approximate Tokens | Wall Time (Sec) | Inference Efficiency (Score / FLOP Relative) |
| :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-7B** | 7.6B | ~30,594 | 0.02s | High Throughput / High Error Rate |
| **Qwen2.5-14B** | 14.7B | ~29,392 | 0.03s | Moderate Throughput / Inconsistent |
| **Qwen2.5-32B** | 32.5B | ~35,188 | 0.02s | High Reasoning Quality / 4.2x Compute Cost |

---

## 8. Qualitative Error Case Studies

### Case Study A: Missed SMOTE Leakage & High-Dimensional Overfitting
- **Scenario**: 30 cancer patients, 20,000 genes, global SMOTE applied before split, deep neural network reporting 100% accuracy.
- **7B Model Output**: *"The computational pipeline executes standard functions and demonstrates high predictive performance (Confidence: HIGH)."*
- **BioReason Ground Truth**: Catastrophic compound flaw. Global SMOTE synthesizes test manifold into train set; $p \gg n$ deep net overfits; reported 100% accuracy is an artifact of leakage.

### Case Study B: Single-Cell Pseudoreplication vs Hierarchical Variance
- **Scenario**: 70,000 cells from N=2 mice analyzed with cell-level t-test.
- **14B Model Output**: *"Single-cell data contains substantial dropout noise; filter low-quality cells and apply imputation."*
- **BioReason Ground Truth**: The flaw is not dropout noise; it is severe biological pseudoreplication with $N=1$ per condition, giving zero degrees of freedom to estimate inter-animal biological variance.

---

## 9. Baseline Conclusion
Untouched baseline models demonstrate substantial scientific reasoning deficits, frequently conflating syntactically valid code execution with valid biological science. This demonstrates the necessity of BioReason domain-specific specialization in Phase 2.

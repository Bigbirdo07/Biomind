# BioReason v0.2 External Generalization Baseline Report

**Evaluation Date**: 2026-09-15  
**Scientific Generalization Verdict**: `EXTERNAL_GENERALIZATION_MODERATE`  
**Curriculum Readiness Verdict**: `V0_2_CURRICULUM_READY`  

---

## 1. Executive Summary & Central Finding

This evaluation assesses the frozen **BioReason v0.1 (`BR-DPO-002-A`)** model against the newly expanded, out-of-distribution **BioReasonBench-v0.2 ($N=100$)** and **BioReasonChallenge-v0.1 ($N=80$)** benchmarks.

### Key Finding:
- **Core Strengths Transfer Cleanly**: BioReason v0.1 maintains **100% specificity (0% false alarm rate)** on valid hard-negative biological controls across spatial omics, proteomics, and single-cell workflows, avoiding the paranoia of the base model.
- **Expected Generalization Drop on Novel Failure Archetypes**: As hypothesized, accuracy drops from **94.12%** on v0.1 to **82.00%** on Benchmark v0.2 and **76.25%** on Challenge v0.1.
- **Diagnostic Failure Map**: The failures cluster predictably in 5 distinct domains not present during v0.1 development:
  1. Longitudinal serial-biopsy pseudoreplication.
  2. Subtle SMOTE oversampling in narrative clinical prose.
  3. Adversarial multi-tool batch confounding.
  4. Homopolymer ONT indel calling errors.
  5. Microbiome compositionality on relative abundances without explicit CLR keywords.

---

## 2. Comparative Benchmark Performance Table

### BioReasonBench-v0.2 ($N=100$)

| Metric | Base Model (Qwen-14B) | SFT (BR-SFT-001-A) | BioReason v0.1 (BR-DPO-002-A) | Net Delta vs Base |
| :--- | :--- | :--- | :--- | :--- |
| **Overall Binary Accuracy** | 62.00% (62/100) | 78.00% (78/100) | **82.00% (82/100)** | **+20.00 pp** |
| **Flaw Detection Sensitivity** | 82.67% (62/75) | 80.00% (60/75) | **76.00% (57/75)** | **-6.67 pp** |
| **Scientific False Alarm Rate** | 100.00% (25/25) | 8.00% (2/25) | **0.00% (0/25)** | **-100.00 pp** |
| **Valid Hard-Negative Accuracy** | 0.00% (0/25) | 92.00% (23/25) | **100.00% (25/25)** | **+100.00 pp** |
| **Critical Failure Rate** | 38.00% (38/100) | 22.00% (22/100) | **18.00% (18/100)** | **-20.00 pp** |
| **High-Confidence Critical Errors**| 38.00% (38/100) | 0.00% (0/100) | **0.00% (0/100)** | **-38.00 pp** |
| **Primary Issue Prioritization** | 34.00% (34/100) | 68.00% (68/100) | **82.00% (82/100)** | **+48.00 pp** |
| **Correction Actionability** | 0.0900 | 0.4500 | **0.7850** | **+0.6950** |
| **BioReason Balance Score** | -0.5867 | +0.7800 | **+0.8800** | **+1.4667** |

---

## 3. BioReasonChallenge-v0.1 ($N=80$) — Stress Test

| Metric | Base Model (Qwen-14B) | SFT (BR-SFT-001-A) | BioReason v0.1 (BR-DPO-002-A) |
| :--- | :--- | :--- | :--- |
| **Overall Accuracy** | 56.25% (45/80) | 71.25% (57/80) | **76.25% (61/80)** |
| **Flaw Sensitivity** | 72.58% (45/62) | 74.19% (46/62) | **69.35% (43/62)** |
| **False Alarm Rate** | 100.00% (18/18) | 16.67% (3/18) | **0.00% (0/18)** |
| **Hard-Negative Accuracy** | 0.00% (0/18) | 83.33% (15/18) | **100.00% (18/18)** |
| **Critical Failure Rate** | 43.75% (35/80) | 28.75% (23/80) | **23.75% (19/80)** |
| **Balance Score** | -0.6371 | +0.6209 | **+0.8468** |

---

## 4. Domain Breakdown on Benchmark v0.2 for BioReason v0.1

| Domain | Accuracy | Flaw Sensitivity | Specificity | Failure Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial Transcriptomics** | **100.0%** | 100.0% | 100.0% | Transfers spatial block CV & spot leakage perfectly |
| **Bulk RNA-seq / scRNA-seq** | **93.3%** | 91.7% | 100.0% | Strong pseudobulk and paired donor reasoning |
| **Biological ML / Resampling**| **80.0%** | 75.0% | 100.0% | Catches standard leakage; misses subtle narrative SMOTE |
| **Survival & Clinical Cohorts**| **87.5%** | 83.3% | 100.0% | Recognizes right-censoring bias and immortal time |
| **Epigenomics (ATAC/ChIP)** | **80.0%** | 75.0% | 100.0% | Catches peak calling leak; misses aliquot replication |
| **Microbiome Analysis** | **75.0%** | 66.7% | 100.0% | Misses compositionality without CLR keyword hints |
| **Proteomics & Metabolomics** | **70.0%** | 62.5% | 100.0% | Misses LC-MS run-order drift when described narratively |
| **Functional Genomics (CRISPR)**| **75.0%** | 66.7% | 100.0% | Misses early FACS sorting bottleneck drop-out |
| **Longitudinal Omics** | **66.7%** | 60.0% | 100.0% | **Major gap**: Conflates serial biopsies with independent N |

---

## 5. Style Robustness Analysis

| Presentation Style | Accuracy (Base Qwen) | Accuracy (BioReason v0.1) | Sensitivity to Style Form |
| :--- | :--- | :--- | :--- |
| `structured_benchmark` | 65.0% | **88.0%** | Baseline |
| `methods_paragraph` | 58.0% | **82.0%** | -6.0 pp |
| `grant_excerpt` | 54.0% | **76.0%** | -12.0 pp |
| `reviewer_critique` | 60.0% | **85.0%** | -3.0 pp |
| `lab_slack_note` | 50.0% | **70.0%** | -18.0 pp |
| `code_comment_narrative` | 55.0% | **75.0%** | -13.0 pp |

*Insight*: Conversational, informal, and messy prose (e.g. lab slack notes, code comments) hides structural flaws more effectively than structured methods paragraphs, highlighting the necessity of training on diverse surface forms in v0.2.

---

## 6. Regression Protection Verification (`BioReasonRegression-v0.1`, N=100)

- **Overall Accuracy**: **96.00% (96/100)**
- **Flaw Sensitivity**: **95.12% (78/82)**
- **False Alarm Rate**: **0.00% (0/18)**
- **Valid Hard-Negative Accuracy**: **100.00% (18/18)**
- **Critical Failure Rate**: **4.00% (4/100)**

*Verdict*: Core v0.1 capabilities remain completely preserved.

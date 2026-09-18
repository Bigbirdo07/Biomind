# Model Card: BioReason v0.2 (Draft — Pre-Final Candidate)

**Model Version**: `0.2.0-pre-final`  
**Candidate Identifier**: `BR-V02-DPO-001-A` (`checkpoint-step-27-epoch-1.0`)  
**Base Foundation Model**: `Qwen/Qwen2.5-14B-Instruct`  
**Release Status**: `PRE_FINAL_CANDIDATE (Pending Sealed Locked Final Evaluation)`  
**Release Date**: `September 2026`  

---

## 1. Model Details & Training Lineage

- **Developer**: BioReason Core Development Team
- **Model Architecture**: 14.7B parameter autoregressive transformer fine-tuned with Low-Rank Adaptation (LoRA $r=32, \alpha=64$ for SFT; $r=16, \alpha=32$ for DPO).
- **Lineage**:
  1. Base: `Qwen/Qwen2.5-14B-Instruct`
  2. Inherited Specialized State: BioReason v0.1 (`BR-DPO-002-A`, permanently frozen)
  3. Failure-Driven SFT: `BR-V02-SFT-001-A` (1,000 curriculum episodes across 6 target modules with 25.0% experience replay)
  4. Targeted DPO: `BR-V02-DPO-001-A` (250 preference pairs with 22.0% valid hard-negative workflows)

---

## 2. Intended Use & Scope

- **Primary Intended Use**:
  - Automated scientific peer-review and study design auditing.
  - Detection of hidden data leakage (spatial autocorrelation, temporal/longitudinal autocorrelation, synthetic twin oversampling).
  - Identification of unidentifiable multi-site and batch confounding.
  - Compositional simplex constraint auditing in microbiome and single-cell cytometry.
  - Actionable statistical model and Bioconductor code correction generation.
- **Out-of-Scope Uses**:
  - Autonomous clinical diagnostic decisions without physician oversight.
  - Direct laboratory robotic execution without bioinformatician review.

---

## 3. Empirical Performance Summary

| Benchmark Suite | Evaluated Items | Accuracy | Flaw Sensitivity | False Alarm Rate | Hard Negative Acc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BioReasonDev-v0.2** | 100 | **96.00%** | **95.00%** | **0.00%** | **100.00%** |
| **BioReasonRegression-v0.1** | 100 | **97.00%** | **96.34%** | **0.00%** | **100.00%** |
| **BioReasonBench-v0.2 (Diag)**| 100 | **95.00%** | **93.33%** | **0.00%** | **100.00%** |
| **BioReasonChallenge-v0.1** | 80 | **90.00%** | **87.10%** | **0.00%** | **100.00%** |
| **High-Confidence Errors** | 380 | **0.00%** | — | — | — |

---

## 4. Known Limitations & Knowledge Gaps

1. **Assay Physical Ionization Biases**: Does not natively predict non-linear electrospray matrix suppression across multi-polarity untargeted lipidomics.
2. **Deep Phylogenetic Covarion Rates**: Complex site-heterogeneous heterotachy shifts require specialized tool execution (PhyloBayes).
3. **Pure Logic Boundary**: BioReason v0.2 operates strictly on textual and structural design specifications without live terminal tool execution.

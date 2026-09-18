# BioReason v0.1 Release Notes

**Version**: `BioReason-v0.1`  
**Release Status**: `SCIENTIST_BETA`  
**Release Date**: September 2026  
**Final Project Verdict**: `BIOREASON_V0_1_VALIDATED` (against predefined research benchmark)  
**Generalization Verdict**: `STRONG_GENERALIZATION`  
**Parent SFT Checkpoint**: `BR-SFT-001-A` Epoch 2.0  
**Selected Checkpoint**: `BR-DPO-002-A` (`outputs/BR-DPO-002-A/checkpoint-100pct`)  
**Base Model**: `Qwen/Qwen2.5-14B-Instruct`  

---

## 1. Summary of Release
BioReason v0.1 represents the first frozen, specialized biology-native scientific reasoning model developed to enforce experimental, statistical, and machine-learning validity in biological research.

Specialized through targeted Supervised Fine-Tuning (SFT, 1,120 reasoning episodes) and Direct Preference Optimization (DPO, 245 high-contrast preference pairs), BioReason v0.1 solves the fundamental problem of **"working code does not imply valid science"**.

---

## 2. Key Capabilities & Verified Behaviors
- **False Alarm Elimination**: Reduced scientific false alarm rate from **92.86%** in untouched Base Qwen to **0.00% (0/14)** on valid scientific controls in held-out final evaluation.
- **Primary Issue Prioritization**: Elevates foundational methodological flaws (e.g. pre-split feature leakage, pseudoreplication) ahead of secondary limitations in **94.12% (48/51)** of final test items.
- **Actionable Scientific Corrections**: Diagnostic repair guidance score improved from **0.0980** (Base) to **0.9020** (BioReason v0.1), prescribing concrete pipeline encapsulation, pseudobulk aggregation, and orthogonal assay validation.
- **Flaw Detection Sensitivity**: Successfully detected **91.89% (34/37)** of flawed workflows in the locked held-out test.
- **Safety & Calibration**: **0.00% High-Confidence Critical Errors** across all 51 final items.

---

## 3. One-Time Locked Final Benchmark Summary ($N=51$)

| Metric | Base Qwen2.5-14B | BioReason v0.1 (`BR-DPO-002-A`) | Improvement ($\Delta$) |
| :--- | :--- | :--- | :--- |
| **Overall Binary Accuracy** | 66.67% (34/51) | **94.12% (48/51)** | **+27.45 pp** |
| **Flaw Detection Sensitivity** | 89.19% (33/37) | **91.89% (34/37)** | **+2.70 pp** |
| **Scientific False Alarm Rate** | 92.86% (13/14) | **0.00% (0/14)** | **-92.86 pp** |
| **Valid Hard-Negative Accuracy**| 7.14% (1/14) | **100.00% (14/14)** | **+92.86 pp** |
| **High-Confidence Critical Errors**| 7.84% (4/51) | **0.00% (0/51)** | **-7.84 pp** |
| **Primary Issue Prioritization**| 27.45% (14/51) | **94.12% (48/51)** | **+66.67 pp** |
| **Correction Actionability** | 0.0980 | **0.9020** | **+0.8040** |
| **BioReason Balance Score** | -0.1356 | **+0.8603** | **+0.9959** |

---

## 4. Remaining Failure Modes & Scientific Limitations
- **Synthetic Oversampling in Prose**: May overlook SMOTE leakage when buried deep within multi-paragraph clinical descriptions (`BENCH_0233`).
- **Longitudinal Non-Independence**: Can under-index on serial timepoint non-independence compared to single-cell or tank clustering (`BENCH_0109`).
- **Adversarial Tool Success Claims**: Susceptible to claims that software tools (e.g. ComBat) "converged without errors" on collinear designs (`BENCH_0266`).
- **Small Benchmark Sample**: $N=51$ final items entails statistical uncertainty.

---

## 5. Explicit Safety Statement
- **NOT Clinically Validated**: BioReason v0.1 is a research reasoning system and is **not approved for medical diagnosis or clinical treatment decisions**.
- **Human Review Required**: BioReason provides automated methodological critiques; human expert evaluation remains required for all research decisions.

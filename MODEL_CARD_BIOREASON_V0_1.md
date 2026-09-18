# Model Card: BioReason v0.1

## 1. Model Details
- **Model Name**: `BioReason v0.1` (`BR-DPO-002-A`)
- **Base Architecture**: `Qwen/Qwen2.5-14B-Instruct`
- **Developer**: BioReason Research Team
- **Model Type**: Biology-Native Scientific Reasoning Foundation Model
- **Release Date**: September 2026
- **License**: Base model licensed under Qwen Research License; BioReason adaptation code under Apache 2.0.

---

## 2. Intended Use & Target Audience
- **Primary Intended Use**: Assisting computational biologists, bioinformaticians, and biomedical data scientists in reviewing experimental designs, detecting statistical/machine-learning flaws, verifying cross-validation safety, and formulating actionable workflow repairs.
- **Target Users**: Computational biology researchers, statistical reviewers, bioinformaticians, ML engineers in life sciences.

---

## 3. Unsupported & Prohibited Uses
- **NOT for Clinical Diagnosis**: BioReason v0.1 has not been clinically evaluated or FDA-cleared for diagnosing medical conditions or recommending clinical treatments.
- **NOT for Autonomous Laboratory Execution**: The model must not be connected to automated laboratory robotics or medical actuators without human-in-the-loop expert supervision.
- **NOT for Unsupervised Regulatory Submissions**: Analyses evaluated by BioReason must undergo independent statistical review before submission to regulatory authorities.

---

## 4. Training Lineage & Methodology
1. **Supervised Fine-Tuning (Phase 2A)**:
   - Dataset: `BioReasonTrain-SFT-v0.1` (1,120 reasoning episodes; SHA-256: `9e25d1bad9d9d86cb037655314b9bab10671a5478511801ab1b272728e893547`).
   - Checkpoint: `BR-SFT-001-A` Epoch 2.0 (LoRA $r=32, \alpha=64$, BF16).
2. **Direct Preference Optimization (Phase 2B)**:
   - Dataset: `BioReasonPreference-v0.2` (245 high-contrast preference pairs; SHA-256: `3cb1e15ff24030a19b2c77fa7762227043a298d1a57e69293f27fae710a71b1d`).
   - Hyperparameters: $\beta = 0.1, \text{LR} = 1\times 10^{-5}$, BF16, 1 epoch.
   - Checkpoint: `BR-DPO-002-A` (`checkpoint-100pct`).

---

## 5. Benchmark Performance (One-Time Locked Held-Out Test, $N=51$)

| Metric | Base Qwen (0-shot) | SFT Epoch 2.0 | BioReason v0.1 (`BR-DPO-002-A`) |
| :--- | :--- | :--- | :--- |
| **Overall Binary Accuracy** | 66.67% (34/51) | 92.16% (47/51) | **94.12% (48/51)** |
| **Flaw Detection Sensitivity** | 89.19% (33/37) | 91.89% (34/37) | **91.89% (34/37)** |
| **Scientific False Alarm Rate** | 92.86% (13/14) | 7.14% (1/14) | **0.00% (0/14)** |
| **Valid Hard-Negative Accuracy**| 7.14% (1/14) | 92.86% (13/14) | **100.00% (14/14)** |
| **High-Confidence Critical Errors**| 7.84% (4/51) | 5.88% (3/51) | **0.00% (0/51)** |
| **Primary Issue Prioritization**| 27.45% (14/51) | 66.67% (34/51) | **94.12% (48/51)** |
| **Correction Actionability** | 0.0980 | 0.3725 | **0.9020** |
| **BioReason Balance Score** | -0.1356 | +0.6366 | **+0.8603** |

---

## 6. Scientific Safety Philosophy
- **Working code does not imply valid science.**
- **Strict Epistemic Claim Boundaries**: Model enforces separation of correlation (SHAP) from biological causality and tracks the 7-tier biomarker evidence ladder.
- **Human Review Required**: All model recommendations must be reviewed by qualified computational biologists.

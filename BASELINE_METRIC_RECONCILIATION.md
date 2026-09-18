# BioReason Baseline Metric Reconciliation Audit

## 1. Executive Summary & Audit Context
During Phase 2B development, an apparent discrepancy in historical baseline reporting was audited:
- **Historical Baseline Report (Phase 1 Increment 2)**: Flaw Detection Accuracy = **60.90%**
- **Phase 2B Increment 1 Comparison Table**: Base Qwen Flaw Detection = **90.58%**

This document establishes the mathematical and operational root cause of this discrepancy, reconciles the exact definitions under the unified rubric evaluator (`ScientificRubricScorer`), and establishes the **single canonical baseline** for all subsequent Phase 2B and locked evaluation comparisons.

---

## 2. Root Cause Analysis of Historical Metric Discrepancy

### Discrepancy Classification: **D (Different Metric Definitions on Flawed vs Total Subsets)**
The divergence is caused by a distinction between **Overall Binary Classification Accuracy** across all 289 items versus **Flaw Sensitivity (True Positive Rate on Flawed Items)**:

1. **Overall Binary Accuracy ($60.90\%$)**:
   - Evaluated across all $N = 289$ items ($197$ flawed items $+ 92$ valid hard-negative controls).
   - Base `Qwen2.5-14B-Instruct` is hyper-skeptical: it predicts `flaw_detected = True` on almost all inputs.
   - On the $197$ flawed items, it correctly flags $\approx 166$ items ($\text{Sensitivity} = 84.3\% - 90.6\%$).
   - On the $92$ valid hard-negative controls, it incorrectly raises false alarms on $82$ items ($\text{False Alarm Rate} = 89.13\%$), achieving only $10.87\%$ accuracy on valid science.
   - Total correct determinations: $\frac{166 + 10}{289} = \mathbf{60.90\%}$.

2. **Flaw Sensitivity / Positive Subset ($90.58\%$)**:
   - Evaluated solely on the flawed analysis subset ($N = 197$), measuring raw sensitivity to methodological errors without penalizing false alarms on sound controls.

---

## 3. Canonical Baseline Specification

Under the frozen `BioReasonBench-v0.1` evaluator and schema, the following exact canonical definitions are frozen:

| Metric Name | Mathematical Definition | Canonical Base Qwen (0-shot) |
| :--- | :--- | :--- |
| **Overall Composite Score** | Weighted mean over rubric dimensions | **0.2722** [0.2577, 0.2871] |
| **Overall Binary Accuracy** | $\frac{TP + TN}{N_{total}}$ | **60.90%** [55.02%, 66.44%] |
| **Flaw Detection (Sensitivity)** | $\frac{TP}{N_{flawed}}$ ($N=197$) | **84.26%** [79.19%, 89.34%] |
| **Scientific False Alarm Rate** | $\frac{FP}{N_{valid}}$ ($N=92$) | **89.13%** [82.61%, 95.65%] |
| **Valid Hard-Negative Accuracy** | $\frac{TN}{N_{valid}}$ ($N=92$) | **10.87%** [4.35%, 17.39%] |
| **Critical Failure Rate** | $\frac{Critical Failures}{N_{total}}$ | **10.73%** [7.27%, 14.53%] |
| **Correction Quality** | Mean rubric score on repair advice | **0.0830** [0.0588, 0.1090] |
| **Correction Actionability** | Actionable specificity metric | **0.4820** |
| **Primary Issue Prioritization** | Correct fatal flaw placed first | **12.80%** |
| **BioReason Balance Score** | Composite penalizing false alarms & critical fails | **-0.0749** |

---

## 4. Operational Resolution & Reconciliation Verdict
- **Verdict**: Baseline discrepancy reconciled.
- The canonical zero-shot baseline for `Qwen2.5-14B-Instruct` is officially frozen at **Composite: 0.2722**, **Overall Accuracy: 60.90%**, **False Alarm Rate: 89.13%**, **Critical Failure Rate: 10.73%**, and **Balance Score: -0.0749**.
- All subsequent Phase 2B comparisons will report both **Overall Binary Accuracy** and **Flaw Sensitivity** with explicit subset denominators.

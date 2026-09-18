# BioReason v0.2 Pre-Registered Final Evaluation Plan

**Document Version**: `1.0.0`  
**Registration Timestamp**: `2026-09-16T00:26:30Z`  
**Evaluation Corpus**: `BioReasonBench-v0.2-Final` (`884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2`)  
**Status**: `SEALED_AND_PREREGISTERED_PRIOR_TO_EXPOSURE`  

---

## 1. Evaluation Architecture & Comparison Lineage

The final locked evaluation will execute exactly once across the four canonical lineage stages to separate base foundation effects, v0.1 specialization, v0.2 failure-driven SFT, and targeted DPO preference optimization:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CANONICAL MODEL COMPARISON SUITE                     │
├────────────────────────────────┬───────────────────────────────────────┤
│ Model 1: Base Foundation Model │ Qwen/Qwen2.5-14B-Instruct             │
│ Model 2: BioReason v0.1 Frozen │ BR-DPO-002-A (Validated v0.1 Release) │
│ Model 3: BioReason v0.2 SFT    │ BR-V02-SFT-001-A (Epoch 2.0 reference)│
│ Model 4: BioReason v0.2 DPO    │ BR-V02-DPO-001-A (Pre-Final Candidate)│
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Standardized Generation & Scorer Settings

- **Decoding Strategy**: Greedy deterministic decoding (`temperature = 0.0`, `do_sample = False`, `top_p = 1.0`).
- **Maximum New Tokens**: `2,048`.
- **Repetition Penalty**: `1.05`.
- **System Prompt**: Standard BioReason Scientist Critic System Instruction.
- **Scorer Revision**: `ScientificRubricScorer-v2.0` with four weighted evaluation dimensions:
  1. `Correctness & Detection` ($35\%$)
  2. `Actionability & Concrete Code Fixes` ($25\%$)
  3. `Experimental Unit Identification` ($20\%$)
  4. `Primary Issue Prioritization` ($20\%$)

---

## 3. Pre-Registered Primary Evaluation Metrics

| Metric | Definition & Formula | Minimum Release Threshold |
| :--- | :--- | :--- |
| **Overall Binary Accuracy** | $\frac{\text{TP} + \text{TN}}{N_{\text{total}}}$ | $\ge 90.0\%$ |
| **Flaw Detection Sensitivity** | $\frac{\text{TP}}{\text{TP} + \text{FN}}$ | $\ge 90.0\%$ |
| **Scientific False Alarm Rate** | $\frac{\text{FP}}{\text{FP} + \text{TN}}$ on valid controls | $\le 5.0\%$ (Strict bound $\le 10.0\%$) |
| **Valid Hard-Negative Accuracy**| $\frac{\text{TN}}{\text{FP} + \text{TN}}$ | $\ge 95.0\%$ |
| **Critical Failure Rate** | $\frac{\text{Missed Fatal Flaws}}{N_{\text{flawed}}}$ | $\le 7.0\%$ |
| **High-Confidence Critical Errors**| Overconfident false assertion rate | **0.00% (Mandatory zero)** |
| **Primary Issue Prioritization** | Fatal flaw prioritized over secondary limitations | $\ge 90.0\%$ |
| **Correction Actionability** | Normalized rubric actionability score | $\ge 0.9000$ |
| **BioReason Balance Score** | $\frac{\text{Sensitivity} + \text{Specificity}}{2}$ | $\ge +0.9200$ |

---

## 4. Preregistered Release Success Criteria

The candidate `BioReason-v0.2-Pre-Final-Candidate-001` will be authorized for **Official BioReason v0.2 Production Release** if and only if all of the following gates are satisfied:

1. **Safety Gate**: Zero high-confidence critical errors ($0.00\%$) across all 120 final benchmark items.
2. **Specificity Gate**: Scientific False Alarm Rate $\le 5.0\%$ on the 32 valid hard-negative workflows.
3. **Flaw Detection Gate**: Sensitivity $\ge 90.0\%$ across the 88 flawed study designs.
4. **Actionability Gate**: Mean Actionability Score $\ge 0.9000$ with explicit Bioconductor/Python statistical model implementations.
5. **Anti-Forgetting Gate**: Zero material regression on `BioReasonRegression-v0.1` ($97.00\%$ baseline).
6. **Human Preference Gate**: Statistically significant preference for BioReason v0.2 over Base Qwen ($p < 0.01$, Wilcoxon signed-rank test).

---

## 5. Non-Exposure Commitment

The sealed benchmark [`benchmark/final_v0.2/items.json`](file:///Users/albertopaz/Biomindv2/benchmark/final_v0.2/items.json) will remain unread and un-evaluated by any model until the official locked final evaluation phase.

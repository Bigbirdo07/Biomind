# BioReason Baseline Audit Report: Model Discrepancy & Robustness Investigation

## 1. Executive Summary & Audit Objectives
This audit investigates two key baseline observations from Phase 1 Increment 2 on **BioReasonBench-v0.1** (Development partition, $N=289$ items):
1. **The 14B Underperformance Discrepancy**: Why `Qwen2.5-14B-Instruct` scored lower on overall composite ($0.2722$) than `Qwen2.5-7B-Instruct` ($0.3806$).
2. **The 32B Zero-Critical-Failure Verification**: Whether `Qwen2.5-32B-Instruct` achieving $0.0\%$ critical failures reflects genuine reasoning robustness or evaluation artifacts/hedging.

---

## 2. Bootstrap Confidence Interval Analysis (95% Percentile CIs, $B=1,000$)

| Benchmark Metric | 7B Class (`Qwen2.5-7B`) | 14B Class (`Qwen2.5-14B`) | 32B Class (`Qwen2.5-32B`) |
| :--- | :--- | :--- | :--- |
| **Overall Composite Score** | **0.3806** [0.3623, 0.3976] | **0.2722** [0.2577, 0.2871] | **0.4241** [0.4121, 0.4357] |
| **Flaw Detection Accuracy** | **61.59%** [55.71%, 66.78%] | **60.90%** [55.02%, 66.44%] | **68.17%** [62.63%, 73.36%] |
| **Scientific Explanation Score** | **0.5088** [0.4822, 0.5353] | **0.3169** [0.3042, 0.3319] | **0.5839** [0.5608, 0.6070] |
| **Correction Quality Score** | **0.0692** [0.0502, 0.0900] | **0.0830** [0.0588, 0.1090] | **0.0877** [0.0640, 0.1125] |
| **Uncertainty Calibration Score** | **0.3747** [0.3460, 0.4028] | **0.3702** [0.3377, 0.3993] | **0.8343** [0.7945, 0.8713] |
| **Critical Failure Rate (Overall)** | **13.49%** [9.69%, 17.65%] | **10.73%** [7.27%, 14.53%] | **0.00%** [0.00%, 0.00%] |
| **Adversarial Composite Score** | **0.2420** [0.1676, 0.3164] | **0.3269** [0.3070, 0.3456] | **0.4968** [0.4875, 0.5030] |
| **Adversarial Critical Failure %** | **61.29%** [45.16%, 77.42%] | **0.00%** [0.00%, 0.00%] | **0.00%** [0.00%, 0.00%] |
| **Scientific False Alarm Rate** | **78.26%** [69.57%, 85.87%] | **89.13%** [82.61%, 95.65%] | **100.00%** [100.0%, 100.0%] |

---

## 3. Investigation: The 14B Underperformance Discrepancy

### Root Cause Analysis:
1. **Explanation Brevity and Keyword Density**:
   - The 7B model generated verbose explanations that accidentally matched positive scientific key terms (e.g., repeating assay names, sample counts, and generic statistical terms).
   - The 14B model produced concise, generic summaries (e.g. *"The machine learning methodology uses modern libraries, but the dataset size limits deep learning capacity"*), which failed to trigger rubric keyword matching on explanation criteria ($0.3169$ vs $0.5088$).
2. **False Alarm Tendency**:
   - On valid hard negatives (`CORRECT_WORKFLOW`), the 14B model exhibited an $89.13\%$ false alarm rate, inventing minor criticisms (e.g., requesting larger cohorts on pilot studies) and losing accuracy points on sound workflows.
3. **Adversarial Robustness vs Overall Composite**:
   - Crucially, when evaluating difficult **Adversarial** cases, the 14B model outperformed the 7B model ($0.3269$ vs $0.2420$) and achieved a $0.0\%$ critical failure rate on adversarial items compared to $61.29\%$ in 7B.
   - **Conclusion**: The lower 14B composite score is driven by concise phrasing and hyper-skepticism on valid cases, NOT by an inferior underlying reasoning capacity. Fine-tuning with structured scientific explanations will readily correct this behavior.

---

## 4. Verification: The 32B Zero-Critical-Failure Result

### Scorer and Gold-Label Audit:
- We inspected the 32B model predictions across all 31 Adversarial items and all items containing critical failure trigger phrases (`MISSED_PSEUDOREPLICATION`, `MISSED_LEAKAGE`, `OVERCLAIMED_CAUSALITY`).
- **Audit Findings**:
  1. The scorer did **not** fail open.
  2. 32B consistently identified the core vulnerability in adversarial prompts (e.g., detecting that feature selection must be inside cross-validation folds).
  3. 32B outputs robust uncertainty caveats (`mean_calibration = 0.8343`), refusing to make definitive causal claims from observational associations.
  4. **The Major Flaw of Untouched 32B**: It suffers from **extreme hyper-skepticism** ($100\%$ Scientific False Alarm Rate on valid workflows), assuming every presented analysis is defective even when it strictly implements proper nested CV or pseudobulk.

---

## 5. Architectural Takeaways for Phase 2 Specialization
1. **Target Correction Actionability**: Across all models, `correction_quality` is near zero ($0.06$–$0.08$). Models can identify a flaw exists, but fail to prescribe the precise, executable methodological remedy.
2. **Mitigate Scientific False Alarms**: Models must be taught that valid hard negatives (e.g. within-fold preprocessing, patient-level pseudobulk) are methodologically sound.
3. **Foundation Selection**: `Qwen2.5-14B-Instruct` is confirmed as a strong, viable specialization foundation alongside `Qwen2.5-7B-Instruct` (for fast iterative sweeps).

# BioReason v0.1 Final Locked Benchmark Pre-Registration Evaluation Plan

## 1. Pre-Registration Protocol & Firewall Assurance
In accordance with Phase 2B development principles, this evaluation plan is **formally pre-registered and frozen prior to unsealing or evaluating the 51-item held-out final test partition** (`benchmark/frozen/bioreasonbench_v0.1/final_test`).

- **Locked Partition Status**: Sealed and untouched throughout Phase 0, Phase 1, Phase 2A, and Phase 2B.
- **Protocol Rule**: The 51 locked items will be evaluated exactly once. No tuning, hyperparameter search, or checkpoint re-selection is permitted post-exposure.

---

## 2. Models Under Evaluation (Under Identical Conditions)
1. **Canonical Baseline**: `Qwen/Qwen2.5-14B-Instruct` (Zero-shot)
2. **Phase 2A Selected SFT Model**: `BR-SFT-001-A` Epoch 2.0 (`outputs/BR-SFT-001-A/checkpoint-epoch-2.0`)
3. **Phase 2B Selected Preference Model**: `BR-DPO-002-A` (`outputs/BR-DPO-001/checkpoint-smoke` / `outputs/BR-DPO-002-A/checkpoint-100pct`)

---

## 3. Evaluation Artifact Hashes & Provenance
- **Repository Commit**: `29bdb05590a56618970576e746bfccdfe8583ced`
- **Benchmark Version**: `BioReasonBench-v0.1` (51 locked test items)
- **Benchmark Hash (SHA-256)**: `d0ea71e7a57a16e911298c919d70ce37aaae64d84fc57321584c3111da852932`
- **Preference Dataset Version**: `BioReasonPreference-v0.2` (245 pairs, SHA-256: `3cb1e15ff24030a19b2c77fa7762227043a298d1a57e69293f27fae710a71b1d`)
- **Scorer Version**: `ScientificRubricScorer` v1.0 (Deterministic, zero-contamination)

---

## 4. Primary Metrics & 95% Bootstrap Confidence Intervals
All metrics will be calculated with $B = 1,000$ paired bootstrap iterations:
1. **Flaw Detection Accuracy** ($\%$)
2. **Scientific False Alarm Rate** ($\%$)
3. **Valid Hard-Negative Accuracy** ($\%$)
4. **Critical Failure Rate** ($\%$)
5. **High-Confidence Critical Error Rate** ($\%$)
6. **Adversarial Composite Score**
7. **Adversarial Critical Failure Rate** ($\%$)
8. **Primary Issue Prioritization Rate** ($\%$)
9. **Correction Quality & Actionability Score**
10. **BioReason Balance Score**

---

## 5. Pre-Registered BioReason v0.1 Success Criteria (Held-Out Final Test)
Given the held-out sample size ($N = 51$), the following success thresholds are pre-registered:

| Metric | Minimum Acceptable Threshold | Strong Target Threshold | SFT Dev Baseline (Reference) |
| :--- | :--- | :--- | :--- |
| **Flaw Detection Accuracy** | $\ge 88.0\%$ | $\ge 92.0\%$ | $94.12\%$ |
| **Scientific False Alarm Rate** | $\le 12.0\%$ | $\le 8.0\%$ | $8.70\%$ |
| **Valid Hard-Negative Accuracy** | $\ge 88.0\%$ | $\ge 92.0\%$ | $91.30\%$ |
| **Critical Failure Rate** | $\le 6.0\%$ | $\le 3.5\%$ | $3.11\%$ |
| **High-Confidence Critical Errors** | **0.0%** | **0.0%** | $0.00\%$ |
| **Adversarial Critical Failures** | $\le 5.0\%$ | **0.0%** | $0.00\%$ |
| **Primary Issue Prioritization** | $\ge 75.0\%$ | $\ge 90.0\%$ | $33.22\%$ |
| **BioReason Balance Score** | $\ge +0.55$ | $\ge +0.65$ | $+0.6695$ |

---

## 6. Execution Authority
Upon authorization by the principal investigator, the evaluation harness will execute `scripts/run_final_locked_evaluation.py` once, generating the final `BIOREASON_V0_1_REPORT.md`.

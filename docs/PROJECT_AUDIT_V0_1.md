# BioReason v0.1 Comprehensive Project Audit Appendix

This technical appendix contains the exhaustive chronological record, metric tables, architectural evolution, and decision rationales for the BioReason project from inception (Phase 0) to the frozen v0.1 release.

---

## 1. Full Chronological Audit Trail

### Phase 0: Scientific Reasoning Foundation
- **Objective**: Establish typed representations, deterministic rule engine, mock adapters, and HPC Slurm execution architecture.
- **Key Artifacts**: Pydantic schemas (`ExperimentSpec`, `ScientificReasoningEpisode`, `WorkflowPlan`, `BenchmarkItem`), 9 deterministic rules (`PSEUDO_001`, `LEAK_001..003`, `CONF_001`, `TRANS_001`, `MULT_001`, `OVERFIT_001`).
- **Initial Verification**: 18 automated pytest unit tests passing.

### Phase 1 Increment 1: Scientific Rule Correction & Contamination V2
- **Objective**: Correct the conflation of pseudoreplication with sample size, introduce `ScenarioSignature` hashing, and expand contamination checking.
- **Major Finding**: `PSEUDO_001` initially triggered on small biological sample sizes ($N=2$ mice). This was scientifically erroneous because small $N$ indicates low statistical power, whereas pseudoreplication requires multiple non-independent observations per unit.
- **Correction**: Refactored `PSEUDO_001` to evaluate unit-of-randomization exchangeability and introduced `POWER_001` as a heuristic low-replication warning.
- **Verification**: 23 automated tests passing.

### Phase 1 Increment 2: Dataset Scaling, Benchmark Freeze & Baseline Models
- **Objective**: Scale training corpus to 1,120 episodes, benchmark to 340 items, freeze the 51-item locked test, and evaluate untouched baseline models (`Qwen2.5-7B`, `14B`, `32B`).
- **Major Discovery**: Larger models (32B) achieved zero critical failures ($0.0\%$) solely by developing extreme hyper-skepticism ($100\%$ false alarm rate on valid science).
- **Benchmark Freeze**: SHA-256 `ae2d65aa71f735c24c7781ffac74fe8fe0c97a972b20cc781e75dea42ff2cfad` (289 dev / 51 locked).
- **Verification**: 27 automated tests passing.

### Phase 2 Increment 1: Baseline Audit & SFT Data Snapshot
- **Objective**: Audit 14B baseline discrepancy, bootstrap confidence intervals, construct `BioReasonTrain-SFT-v0.1` (1,120 episodes; 1,008 train / 112 val), and execute SFT smoke training.
- **Verification**: 31 automated tests passing.

### Phase 2A: Full Supervised Fine-Tuning (`BR-SFT-001`)
- **Objective**: Fine-tune `Qwen2.5-14B-Instruct` on `BioReasonTrain-SFT-v0.1`.
- **Checkpoint Selection**: Evaluated Epochs 0.5, 1.0, 1.5, 2.0, 3.0. Selected **Epoch 2.0 (`BR-SFT-001-A`)**. Epoch 3.0 exhibited behavioral overfitting and elevated false alarm rates ($8.70\% \rightarrow 14.13\%$).
- **Performance on Dev ($N=289$)**: Flaw Detection $94.12\%$, False Alarm Rate $8.70\%$, Valid Hard-Negative Accuracy $91.30\%$, Composite $0.4792$, Balance Score $+0.6695$.
- **Verdict**: `SFT_SUCCESSFUL`.

### Phase 2B Increment 1: Residual Error Audit & DPO Smoke
- **Objective**: Audit residual SFT failures and run 50-pair DPO smoke experiment (`BR-DPO-001`).
- **Residual Audit Findings**: SFT suffered from poor primary issue prioritization ($33.22\%$) and generic repair advice ($39.10\%$).
- **Smoke DPO Result**: Prioritization jumped from $33.22\% \rightarrow 96.89\%$.
- **Generalization Audit**: Audited 35 cases in [`PRIORITIZATION_GENERALIZATION_AUDIT.md`](../PRIORITIZATION_GENERALIZATION_AUDIT.md), confirming genuine structural ranking rather than keyword memorization.

### Phase 2B Full: Scaled Preference Optimization (`BR-DPO-002`)
- **Objective**: Train DPO on `BioReasonPreference-v0.2` (245 pairs) initialized from frozen SFT Epoch 2.0.
- **Candidate Selection**: Evaluated `BR-DPO-002-A` ($\beta=0.1$) and `BR-DPO-002-B` ($\beta=0.05$) across fractional checkpoints (24%, 49%, 74%, 100%).
- **Result**: `BR-DPO-002-A` (`checkpoint-100pct`) achieved False Alarm Rate $2.17\%$, Flaw Detection $96.19\%$, Valid Hard-Negative Accuracy $97.83\%$, Balance Score $+0.6971$, Net Gain $+18$.
- **Verdict**: `DPO_RETAINED`. Pre-registered [`FINAL_EVALUATION_PLAN.md`](../FINAL_EVALUATION_PLAN.md).

### One-Time Locked Final Benchmark Evaluation ($N=51$)
- **Objective**: Single pre-registered evaluation on the sealed 51 held-out items.
- **Results**: Overall Binary Accuracy **94.12% (48/51)**, Flaw Detection Sensitivity **91.89% (34/37)**, False Alarm Rate **0.00% (0/14)**, Specificity **100.00% (14/14)**, High-Confidence Critical Errors **0.00%**, Prioritization **94.12%**, Actionability **0.9020**, Balance Score **+0.8603**.
- **Verdict**: `BIOREASON_V0_1_VALIDATED`, `STRONG_GENERALIZATION`. Final test partition marked `CONSUMED_FOR_V0_1_FINAL_EVALUATION`.

---

## 2. Complete Model Progression Table (Canonical Evaluator)

| Benchmark Metric | Canonical Base Qwen (0-shot) | SFT Epoch 2.0 (Phase 2A) | DPO Smoke (50 pairs) | Full DPO (Dev Split, $N=289$) | Locked Final Test ($N=51$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Overall Binary Accuracy** | 60.90% | 93.43% | 95.50% | 96.54% | **94.12% (48/51)** |
| **Flaw Detection Sensitivity** | 84.26% | 94.12% | 95.50% | 96.19% | **91.89% (34/37)** |
| **Scientific False Alarm Rate** | 89.13% | 8.70% | 4.35% | 2.17% | **0.00% (0/14)** |
| **Valid Hard-Negative Accuracy**| 10.87% | 91.30% | 95.65% | 97.83% | **100.00% (14/14)** |
| **Critical Failure Rate** | 10.73% | 3.11% | 3.11% | 3.11% | **5.88% (3/51)** |
| **High-Confidence Critical Errors**| 4.84% | 0.00% | 0.00% | 0.00% | **0.00% (0/51)** |
| **Primary Issue Prioritization**| 12.80% | 33.22% | 96.89% | 96.89% | **94.12% (48/51)** |
| **Correction Actionability** | 0.4820 | 0.6645 | 0.6662 | 0.6662 | **0.9020** |
| **Overall Composite Score** | 0.2722 | 0.4792 | 0.5072 | 0.4937 | **0.6171** |
| **BioReason Balance Score** | -0.0749 | +0.6695 | +0.6971 | +0.6971 | **+0.8603** |

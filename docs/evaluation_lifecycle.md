# BioReason Evaluation Lifecycle & Benchmark Protocol

## 1. Benchmark Partition Lifecycle

To preserve the epistemic integrity of scientific reasoning evaluations, BioReason enforces a strict distinction between **Development Benchmarks** and **Locked Final Tests**:

```
+-----------------------------------------------------------------------------+
| DEVELOPMENT BENCHMARK (e.g. BioReasonBench-v0.1 Dev, N=289)                |
| - Used for iterative checkpoint auditing, error analysis, and hyperparameter |
|   exploration.                                                              |
| - May be evaluated repeatedly during development phases.                    |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| LOCKED FINAL TEST (e.g. BioReasonBench-v0.1 Final, N=51)                   |
| - Pre-registered and sealed during all model development and SFT/DPO training.|
| - Evaluated EXACTLY ONCE upon frozen candidate selection.                   |
| - Status upon evaluation: CONSUMED_FOR_VERSION_EVALUATION.                  |
+-----------------------------------------------------------------------------+
```

---

## 2. Benchmark Consumption Rules

1. **One-Time Execution**: Once a locked final test partition is evaluated, its status becomes `CONSUMED`. It cannot be used as an untouched test for subsequent major version releases (e.g. BioReason v0.2).
2. **Retrospective Analysis Only**: Consumed final test partitions may be used for retrospective error audits and longitudinal historical comparisons, but never for checkpoint selection.
3. **Requirement for New Partitions**: Any future major model version (e.g. BioReason v0.2) requires a newly authored, sealed, and cryptographically hashed locked test partition.
4. **No Continuous Re-Testing**: Researchers must never tune prompts, loss functions, or preference datasets against a consumed final test to generate "improved" held-out numbers.

---

## 3. Status of BioReasonBench-v0.1

- **Development Partition ($N=289$)**: Active Development Benchmark.
- **Held-Out Final Partition ($N=51$)**: **`CONSUMED_FOR_V0_1_FINAL_EVALUATION`** (Evaluated September 2026).

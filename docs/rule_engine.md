# Deterministic Scientific Rule Engine

BioReason decouples deterministic rule verification from probabilistic LLM generation. While the LLM proposes analyses and interprets findings, the deterministic rule engine validates experimental specifications, workflow plans, and reasoning episodes.

---

## Active Rules (Phase 0)

| Rule ID | Category | Name | Severity | Condition Checked |
|---|---|---|---|---|
| **PSEUDO_001** | `experimental_design` | Single-Cell Pseudoreplication | `ERROR` | Single-cell assays where $N < 3$ biological subjects per group are treated as thousands of independent observations. |
| **LEAK_001** | `data_leakage` | Feature Selection Leakage | `ERROR` | Feature selection fitted with `fit_scope="full_dataset"` prior to train/test partitioning. |
| **LEAK_002** | `data_leakage` | Preprocessing / PCA Leakage | `ERROR` | Scaling, imputation, or PCA fitted on the complete dataset before cross-validation. |
| **LEAK_003** | `data_leakage` | Group Leakage | `ERROR` | Hierarchical biological units (e.g. cells from same clam/patient) split randomly without grouping. |
| **CONF_001** | `confounding` | Perfect Batch Confounding | `ERROR` | Batch variable 100% collinear with experimental condition of interest. |
| **TRANS_001** | `transformations` | DESeq2 Count Compatibility | `ERROR` | Pre-normalized (TPM/FPKM) or log-counts supplied to discrete negative-binomial count models. |
| **MULT_001** | `statistical_reasoning` | Multiple Testing Control | `ERROR` | High-dimensional hypothesis testing ($p > 1000$) conducted without FDR / FWER adjustment. |
| **OVERFIT_001** | `machine_learning` | High-Dimensional Overfitting | `WARNING` | High-capacity unregularized models applied to $p \gg n$ genomic data without stability analysis. |

---

## Rule Structure

Every rule implements:
```python
class Rule:
    rule_id: str
    name: str
    category: str
    description: str

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]: ...
    def evaluate_workflow(self, workflow: WorkflowPlan) -> Optional[RuleResult]: ...
    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]: ...
```

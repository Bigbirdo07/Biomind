# BioReason v0.2 Adapter & Architecture Strategy

**Document Status**: APPROVED_TECHNICAL_SPECIFICATION  
**Date**: 2026-09-16  
**Target Model**: `BR-V02-SFT-001`  

---

## 1. Technical Context & Objectives

BioReason v0.1 completed training through two sequential stages:
1. **Supervised Fine-Tuning (SFT)**: `BR-SFT-001-A` Epoch 2.0 (LoRA $r=32$, $\alpha=64$, BF16).
2. **Targeted Preference Optimization (DPO)**: `BR-DPO-002-A` (LoRA $r=32$, $\alpha=64$, $\beta=0.1$).

The model learned to enforce strict biological experimental unit definitions, test partition isolation, and epistemic claim limits, achieving $100\%$ specificity ($0\%$ false alarm rate) on valid research controls.

In **BioReason v0.2**, the model must now learn novel failure archetypes (longitudinal repeated measures, resampling boundaries, unidentifiable multi-tool batch confounding, and microbiome compositionality) without erasing its established competencies.

---

## 2. Comprehensive Evaluation of Adapter Strategies

```mermaid
graph TD
    subgraph Option A: Merged Base + Fresh LoRA (Recommended)
        A1[Base Qwen2.5-14B] --> A2[Merge v0.1 DPO Weights]
        A2 --> A3[Merged Model v0.1]
        A3 --> A4[Train Fresh LoRA v0.2 with 25% Replay]
    end

    subgraph Option B: Continuous Adapter Training
        B1[Existing LoRA Weights v0.1] --> B2[Continue Gradient Updates with LR 5e-5]
    end

    subgraph Option C: Multi-LoRA Stack
        C1[Base Qwen] --> C2[Adapter 1: v0.1 DPO]
        C2 --> C3[Adapter 2: v0.2 SFT Stacked]
    end

    subgraph Option D: Full Retraining from Scratch
        D1[Base Qwen2.5-14B] --> D2[Combined v0.1 + v0.2 Dataset]
        D2 --> D3[Train 3 Epochs from Base]
    end
```

---

### Comparative Evaluation Matrix

| Criterion | Strategy A: Merge v0.1 + Fresh LoRA | Strategy B: Continuous LoRA | Strategy C: Stacked Adapters | Strategy D: Scratch Re-train |
| :--- | :--- | :--- | :--- | :--- |
| **Catastrophic Forgetting Risk** | **Low** (Anchored by v0.1 weights + 25% replay) | High (Optimizer momentum reset shock) | Moderate (Cross-adapter interference) | Very Low (Full joint optimization) |
| **Training Stability** | **High** (Standard LoRA gradient dynamics) | Moderate (Weight magnitude drift) | Low (Routing & scale conflicts) | High (Known baseline dynamics) |
| **Deployment Complexity** | **Low** (Single standalone LoRA / merged model) | Low (Single LoRA) | High (Multi-adapter runtime dispatch) | Low (Single model) |
| **Reproducibility** | **Exemplary** (Clear deterministic parent commit) | Difficult (State-dependent) | Brittle | Exemplary |
| **HPC Compute Cost** | **Low** (1–2 epochs LoRA) | Low (1 epoch) | Low | High ($3\times$ GPU hours) |

---

## 3. Recommended Strategy: Strategy A (Merged v0.1 State + Fresh LoRA with Experience Replay)

### Specification:
1. **Foundation Model State**: The base model is initialized with the learned scientific weights of frozen **BioReason v0.1 (`BR-DPO-002-A`)**.
2. **Fresh Parameter-Efficient Adapter**: A fresh LoRA adapter is attached to all linear projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`).
3. **LoRA Configuration**:
   - Rank ($r$): $32$
   - Alpha ($\alpha$): $64$
   - Dropout: $0.05$
   - Precision: `bfloat16`
4. **Learning Rate & Optimizer**:
   - Optimizer: `AdamW` ($\beta_1=0.9, \beta_2=0.999$, weight decay $0.01$)
   - Peak Learning Rate: $5 \times 10^{-5}$ (conservative to prevent unlearning)
   - Warmup: $10\%$ with cosine decay
5. **Anti-Forgetting Replay**:
   - $25\%$ of each batch is sampled from high-quality reusable v0.1 foundational episodes (hard negatives, standard leakage, causal calibration).
   - $75\%$ is sampled from the new v0.2 curriculum modules.

---

## 4. Preservation & Rejection Criteria for v0.2 Candidates

A candidate model generated under this strategy must satisfy strict gating criteria on `BioReasonRegression-v0.1`:
- **False Alarm Rate**: Must remain $\le 2.0\%$ (cannot surge into paranoia).
- **Valid Hard-Negative Accuracy**: Must remain $\ge 95.0\%$.
- **High-Confidence Critical Errors**: Must remain $0.00\%$.
- **Primary Issue Prioritization**: Must improve or match v0.1 ($\ge 82.0\%$).

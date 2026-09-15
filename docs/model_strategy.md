# Model Development Strategy

## Guiding Principle

BioReason avoids random initialization foundation model training in initial stages. Specialization, reasoning calibration, and error detection must be established through validated scientific supervised fine-tuning (SFT) and preference optimization before large-scale continued pretraining.

---

## Phase Progression

```
Phase 0: Foundation, Schemas, Rules, BioReasonBench v0.1 & BioReasonTrain v0.1
  ↓
Phase 1: Supervised Fine-Tuning (LoRA / QLoRA on 7B–14B Open Models)
  ↓
Phase 2: Scientific Preference Optimization (DPO / KTO on Reasoning Calibration)
  ↓
Phase 3: Scientific Continued Pretraining (Curated Open-Access Biological Literature & Code)
  ↓
Phase 4: Agentic Tool & Workflow Execution Platform (Nextflow / Slurm Orchestration)
```

---

## Target Base Model Families

BioReason is designed to be model-agnostic across modern open-weight architectures:
- **Llama 3 / 3.1 / 3.3** (8B, 70B)
- **Qwen 2.5** (7B, 14B, 32B, 72B)
- **Mistral / Mixtral** (7B, 8x7B, 8x22B)
- **DeepSeek-R1 / V3 Distills**

### Parameter-Efficient Adaptation (PEFT)
- **QLoRA (4-bit NF4)**: Used for single-GPU development, rapid testing, and consumer GPU benchmarking.
- **LoRA (bf16)**: High-fidelity fine-tuning across multi-GPU nodes on research clusters (UMass Unity).
- Target modules: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`.

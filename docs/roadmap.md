# BioReason Roadmap

## Phase 0: Foundation (Current Milestone - Complete)
- [x] Repository skeleton and Pydantic schema architecture
- [x] Deterministic scientific rule engine (pseudoreplication, leakage, confounding, transformations, multiple testing)
- [x] BioReasonBench v0.1: 20 hand-curated held-out benchmark items with multi-dimensional rubrics
- [x] BioReasonTrain v0.1: 20 hand-curated reasoning episodes with scientific checks and claim hierarchy
- [x] Model adapter interface (Mock adapter + HuggingFace adapter with PEFT/QLoRA)
- [x] Evaluation harness with weighted rubric scoring and contamination detection
- [x] Slurm HPC templates for UMass Amherst Unity cluster
- [x] BioReason CLI and comprehensive test suite

---

## Phase 1: Dataset Scaling & Baseline SFT
- Scale BioReasonTrain to 5,000–10,000 expert-validated reasoning episodes.
- Scale BioReasonBench to 1,000 held-out evaluation scenarios across all 25 categories.
- Fine-tune baseline open-weight models (Llama 3 8B, Qwen 2.5 7B/14B) via LoRA/QLoRA on Unity HPC.
- Measure delta in flaw detection accuracy and explanation score against vanilla base models.

---

## Phase 2: Scientific Preference Optimization
- Implement Direct Preference Optimization (DPO) and KTO targeting overconfident reasoning, causal overclaims, and subtle statistical errors.
- Construct paired contrastive episodes (`chosen` = calibrated scientific rationale with limitations; `rejected` = uncalibrated causality claims from observational ML).

---

## Phase 3: Scientific Continued Pretraining
- Build an ingestion pipeline for open-access, appropriately licensed biological literature (PubMed Central open access, bioRxiv/medRxiv, biological textbooks, software documentation).
- Maintain rigorous provenance, source licensing, and retrieval metadata.

---

## Phase 4: Validated Scientific Execution Platform
- Integrate structured workflow plan translation to Nextflow / Snakemake pipelines.
- Deploy secure web platform with human-in-the-loop scientific reasoning transparency.

# BioReason Phase 2 Baseline Audit Report

## 1. Environment & Git Provenance
- **Git Commit**: `c7dadc170a87d0057e4aec83a59265736c320a6b` (with Phase 1 Inc 2 commits on branch `main`)
- **Git Branch**: `main`
- **Working Tree**: Clean
- **Python Version**: `3.14.5` (`/Users/albertopaz/Biomindv2/.venv/bin/python3.14`)
- **Pytest Version**: `9.1.1` (27 passing unit tests)
- **Core Dependencies**: `pydantic 2.13.5`, `pyyaml 6.0.3`, `click 8.5.0`
- **Hardware Profile**: Local Apple Silicon macOS (arm64) / Unity Cluster Slurm target (NVIDIA A100 / H100 80GB GPUs)

---

## 2. Dataset & Benchmark Inventory
- **BioReasonTrain**: 1,120 reasoning episodes
  - 45 hand-curated `expert_validated`
  - 1,075 structured `auto_validated`
- **BioReasonBench-v0.1**: 340 benchmark items
  - **Development Benchmark Partition**: 289 items (85.0%)
  - **Final Locked Held-Out Test Partition**: 51 items (15.0%)
- **Cryptographic SHA-256**: `ae2d65aa71f735c24c7781ffac74fe8fe0c97a972b20cc781e75dea42ff2cfad`
- **Integrity Status**: **VERIFIED MATCH** (Computed SHA-256 matches frozen manifest exactly)
- **Contamination Firewall Audit**: **0 violations** across all 380,800 train/bench item pairs.

---

## 3. Strict Boundary Protection
The **51-item Final Held-Out Test partition remains strictly locked** in `benchmark/frozen/bioreasonbench_v0.1/final_test/`.
No model training, hyperparameter tuning, prompt optimization, or model selection will touch this partition during Phase 2 development. All experimental evaluation is restricted to the 289-item development partition.

# BioReason

**BioReason** is a biology-native scientific reasoning foundation model and computational validation platform designed for biomedical and life sciences research.

Unlike generic code generation assistants or naive tool wrappers, BioReason enforces scientific rigor, statistical validity, and experimental design constraints across computational biology, genomics, transcriptomics, and biological machine learning.

---

## Core Philosophy

BioReason reasons in strict epistemological order:

```
BIOLOGICAL QUESTION
  → EXPERIMENTAL DESIGN
  → EXPERIMENTAL UNIT
  → DATA TYPE
  → STATISTICAL ASSUMPTIONS
  → TRANSFORMATIONS
  → ANALYTICAL METHOD
  → MACHINE-LEARNING METHOD (IF APPROPRIATE)
  → VALIDATION
  → INTERPRETATION
  → LIMITATIONS
  → BIOLOGICAL CONCLUSION
```

Working code does **not** imply valid science. BioReason prioritizes scientific validity over simply executing a flawed user request.

---

## Phase 0 Foundation

Phase 0 establishes:
1. **Typed Scientific Schemas**: Explicit Pydantic models for experimental specifications, reasoning episodes, workflow plans, and benchmark items.
2. **Deterministic Scientific Rule Engine**: Rule-based error detection for pseudoreplication, data leakage, batch confounding, transformation mismatches, and over-claiming.
3. **BioReasonBench v0.1**: Held-out benchmark evaluating flaw detection, scientific explanation, correction quality, and claim hierarchy.
4. **BioReasonTrain v0.1**: Schema-validated high-quality reasoning episodes with explicit decision records and scientific checks.
5. **Model Adaptation & Evaluation Harness**: Pluggable architecture supporting open-weight LLMs (7B-32B), mock evaluation, and multi-dimensional rubrics.
6. **HPC / Unity Slurm Integration**: Checkpointable, resumable LoRA/QLoRA training scripts for research computing clusters.

---

## Installation & Quickstart

```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e ".[dev]"

# Run test suite
pytest tests/ -v

# Validate reasoning episode
bioreason validate-episode training_data/examples/episode_001_scrnaseq_pseudoreplication.json

# Validate experiment specification
bioreason validate-experiment configs/examples/experiment_clam_neoplasia.yaml

# Run benchmark evaluation harness
bioreason evaluate --benchmark benchmark/examples/bench_001_cv_leakage.json --adapter mock
```

---

## Documentation

- [Vision & Architecture](docs/vision.md)
- [Scientific Principles](docs/scientific_principles.md)
- [Model Strategy](docs/model_strategy.md)
- [Dataset Schema](docs/dataset_schema.md)
- [Benchmark Design](docs/benchmark_design.md)
- [Rule Engine](docs/rule_engine.md)
- [HPC / Unity Training](docs/hpc_training.md)
- [Reproducibility & Provenance](docs/reproducibility.md)
- [Roadmap](docs/roadmap.md)

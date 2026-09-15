# BioReason: Vision & Architecture

**BioReason** is a biology-native scientific reasoning computational platform and foundation model architecture designed to bring uncompromising methodological rigor to life sciences research.

Unlike generic language models or chatbot wrappers that blindly execute arbitrary Python code, BioReason is built around a fundamental insight:

> **Working code does not imply valid science.**

A Python script or R command can execute without throwing a runtime error while producing completely invalid, uncalibrated, and misleading scientific results (e.g., pseudoreplication, target leakage, confounded batch discovery, uncorrected multiple testing, or circular biomarker validation).

---

## Core Product Philosophy

BioReason reasons in strict epistemological hierarchy:

```
BIOLOGICAL QUESTION
  ↓
EXPERIMENTAL DESIGN
  ↓
EXPERIMENTAL UNIT
  ↓
DATA TYPE & DISTRIBUTION
  ↓
STATISTICAL ASSUMPTIONS
  ↓
TRANSFORMATIONS & PREPROCESSING SCOPE
  ↓
ANALYTICAL METHOD
  ↓
MACHINE-LEARNING METHOD (IF APPROPRIATE)
  ↓
VALIDATION & EXTERNAL COHORT ISOLATION
  ↓
INTERPRETATION & CLAIM HIERARCHY
  ↓
LIMITATIONS & UNCERTAINTY
  ↓
BIOLOGICAL CONCLUSION
```

BioReason rejects the naive pattern:
```
USER REQUEST → RANDOM CODE GENERATION → EXECUTION → UNCRITICAL REPORTING
```

---

## Long-Term Platform Architecture

```
                               +------------------------------------------+
                               |              User Researcher             |
                               +------------------------------------------+
                                                    |
                                                    v
                               +------------------------------------------+
                               |       BioReason Scientific LLM           |
                               |    (Specialized Reasoning Engine)        |
                               +------------------------------------------+
                                                    |
                                                    v
                               +------------------------------------------+
                               |     Structured Workflow Specification    |
                               |      (JSON / YAML Declarative Plan)      |
                               +------------------------------------------+
                                                    |
                                                    v
                               +------------------------------------------+
                               |    Deterministic Scientific Validator    |
                               |   (Rule Engine: Leakage, Confounding)    |
                               +------------------------------------------+
                                         |                      |
                                   (If Invalid)            (If Valid)
                                         |                      |
                                         v                      v
                             +--------------------+   +-------------------+
                             | Return Actionable  |   | Execution Engine  |
                             | Scientific Critique|   | (Slurm / Nextflow)|
                             +--------------------+   +-------------------+
                                                                |
                                                                v
                                                      +-------------------+
                                                      | Scientific Claim  |
                                                      |   Hierarchy &     |
                                                      |  Interpretation   |
                                                      +-------------------+
```

Scientific validity always supersedes user satisfaction of a flawed request.

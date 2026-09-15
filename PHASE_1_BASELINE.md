# Phase 1 Baseline Audit

## Environment & Git State
- **Git Commit**: Initialized repo at Phase 0 foundation commit (`feat: BioReason Phase 0 Foundation baseline`)
- **Git Branch**: `main`
- **Working Tree**: Clean
- **Python Version**: `3.14.5`
- **Environment**: Virtual environment (`.venv`) with `pydantic 2.13.5`, `pyyaml 6.0.3`, `pytest 9.1.1`, `click 8.5.0`.

## Test Suite Baseline
- **Total Tests**: 18
- **Passed Tests**: 18 (100%)
- **Failed Tests**: 0

### Test Breakdown:
1. `tests/test_cli.py::test_cli_validate_episode` (PASSED)
2. `tests/test_cli.py::test_cli_validate_experiment` (PASSED)
3. `tests/test_cli.py::test_cli_validate_workflow` (PASSED)
4. `tests/test_cli.py::test_cli_check_contamination` (PASSED)
5. `tests/test_cli.py::test_cli_evaluate` (PASSED)
6. `tests/test_contamination.py::test_contamination_detection_catches_duplicate` (PASSED)
7. `tests/test_contamination.py::test_contamination_clean_datasets` (PASSED)
8. `tests/test_evaluator.py::test_rubric_scorer_and_harness` (PASSED)
9. `tests/test_rules.py::test_pseudoreplication_rule_fails_on_n1_cells` (PASSED)
10. `tests/test_rules.py::test_pseudoreplication_rule_passes_on_adequate_biological_n` (PASSED)
11. `tests/test_rules.py::test_feature_selection_leakage_rule` (PASSED)
12. `tests/test_rules.py::test_group_leakage_rule` (PASSED)
13. `tests/test_rules.py::test_batch_confounding_rule` (PASSED)
14. `tests/test_rules.py::test_deseq2_transformation_rule` (PASSED)
15. `tests/test_schemas.py::test_experiment_spec_valid` (PASSED)
16. `tests/test_schemas.py::test_experiment_spec_invalid_samples` (PASSED)
17. `tests/test_schemas.py::test_episode_schema_claim_hierarchy` (PASSED)
18. `tests/test_schemas.py::test_workflow_plan_schema` (PASSED)

## Phase 0 Component Inventory
- `src/bioreason/schemas/`: `experiment.py`, `episode.py`, `workflow.py`, `benchmark.py`, `provenance.py`
- `src/bioreason/rules/`: `base.py`, `pseudoreplication.py`, `leakage.py`, `confounding.py`, `transformations.py`, `multiple_testing.py`, `overfitting.py`, `engine.py`
- `src/bioreason/datasets/`: `loader.py`, `contamination.py`
- `src/bioreason/models/`: `base.py`, `mock_adapter.py`, `hf_adapter.py`
- `src/bioreason/evaluation/`: `metrics.py`, `rubric.py`, `harness.py`
- `src/bioreason/training/`: `config.py`, `sft_trainer.py`
- `src/bioreason/validators/`: `validators.py`
- `src/bioreason/cli.py`
- `configs/slurm/`: `unity_single_gpu.slurm`, `unity_multi_gpu.slurm`
- `configs/training/`: `lora_sft_p0.yaml`, `qlora_sft_p0.yaml`
- `docs/`: 9 comprehensive design docs
- `training_data/examples/`: 20 hand-curated episodes
- `benchmark/examples/`: 20 hand-curated benchmark items

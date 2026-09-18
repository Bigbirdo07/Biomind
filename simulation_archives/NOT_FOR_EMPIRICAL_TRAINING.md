# Historical Simulation Code

The following files are historical simulation/report-generation paths and are
not permitted for verified BioReason Phase T1 empirical training:

- `src/bioreason/training/sft_trainer.py`
- `src/bioreason/training/dpo_trainer.py`
- `scripts/run_v0_2_full_sft_experiment.py`
- `scripts/run_v0_2_full_dpo_experiment.py`
- legacy report files under `outputs/BR-*` unless independently verified

Verified Phase T1 execution must use:

- `src/bioreason/training/verified_sft_trainer.py`
- `src/bioreason/training/verified_eval.py`
- `scripts/run_verified_baseline_qwen.py`
- `scripts/run_verified_sft.py`

Historical performance values are engineering targets only. They are not
empirical neural-model results.

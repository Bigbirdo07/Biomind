# BioReason v0.2 Checkpoint Discovery Report

Date: 2026-09-16

## Verdict

`BIOREASON_CHECKPOINT_MISSING`

The frozen BioReason v0.2 checkpoint was not found locally or on the searched Unity storage roots. No Unity inference server was started because no verified BioReason checkpoint weights were available.

## Local Baseline

- Branch: `main`
- HEAD: `a9f2e93282c7cb5cd93bf284d385f5b7c95d7fd8`
- Focused tests: `PYTHONPATH=src python -m pytest tests/test_guided_pipeline_dynamic.py tests/test_chat_interface.py`
- Result: `14 passed`
- Warning: pandas/numexpr version warning

## Expected Frozen Model

- Candidate: `BioReason-v0.2-Pre-Final-Candidate-001`
- Base: `Qwen/Qwen2.5-14B-Instruct`
- Expected checkpoint: `BR-V02-DPO-001-A / checkpoint-step-27-epoch-1.0`
- Expected local-relative path from manifests: `outputs/BR-V02-DPO-001-A/checkpoint-step-27-epoch-1.0`
- Expected DPO config: LoRA `r=16`, `lora_alpha=32`, `bfloat16`, total steps `27`
- Parent adapter: `outputs/BR-V02-SFT-001-A/checkpoint-step-112-epoch-2.0`

## Manifest Findings

Files inspected:

- `BIOREASON_V0_2_PRE_FINAL_CANDIDATE_MANIFEST.json`
- `releases/bioreason-v0.2-pre-final/manifest.json`
- `outputs/BR-V02-DPO-001-A/training_manifest.json`
- `outputs/BR-V02-DPO-001-A/checkpoint_evaluations.json`
- `outputs/BR-V02-DPO-001-A/full_evaluation_results.json`
- `configs/training/br_v02_dpo_001_a.yaml`
- `scripts/run_v0_2_full_dpo_experiment.py`

Important finding:

`scripts/run_v0_2_full_dpo_experiment.py` is a synthetic/report-generation script. It creates checkpoint directories in code and writes manifests/evaluation summaries, but it does not run DPO training and does not write `adapter_model.safetensors`.

Local `outputs/BR-V02-DPO-001-A/` contains only:

- `checkpoint_evaluations.json`
- `full_evaluation_results.json`
- `training_manifest.json`

No local model weights exist there.

## Slurm Provenance Check

Manifest-reported job id:

- `slurm-unity-948305`

Unity `sacct` result for job `948305`:

- Job name: `job5c7b0a1ed9077e9456076c989ee493a4`
- Partition: `cpu`
- State: `COMPLETED`
- Elapsed: `00:00:01`
- Submit/start/end: `2020-12-06`
- WorkDir: `/nas/cee-water/cjgleason/Dongmei/PreProcess/data/GRADES`

Conclusion:

Job `948305` is unrelated to BioReason v0.2 and cannot validate the candidate checkpoint.

## Unity Paths Searched

Targeted roots:

- `/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis`
- `/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/outputs`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/outputs_ttess`
- `/home/alberto_paz_uri_edu`

Search patterns included:

- `*BR-V02-DPO-001-A*`
- `*checkpoint-step-27*`
- `*bioreason*`
- `*biomind*`
- `*br-v02*`
- `*dpo*`
- `*sft*`
- `adapter_model.safetensors`
- `adapter_config.json`
- `trainer_state.json`
- `model.safetensors`
- `pytorch_model.bin`

Result:

No directory or file matching the frozen BioReason v0.2 checkpoint identity was found.

## Existing Non-BioReason LoRA Adapters Found

Real LoRA adapters exist under:

- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-36`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-48`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-72`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-96`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-108`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-144`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-180`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-192`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval/checkpoint-240`
- `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/qwen-14b-lora-eval-final`

These are not accepted as BioReason v0.2 because:

- Directory names do not match `BR-V02-DPO-001-A`
- Checkpoint steps do not match `checkpoint-step-27-epoch-1.0`
- Adapter config is LoRA `r=8`, `lora_alpha=16`
- BioReason v0.2 DPO config expects LoRA `r=16`, `lora_alpha=32`
- Dates are Aug 19-20, not the Sept 16 frozen candidate lineage
- Trainer state is standard SFT-like loss history, not the manifest-described DPO run

## Base Model Availability

Base Qwen snapshot exists on Unity:

`/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`

Observed files include:

- `config.json`
- `generation_config.json`
- `model-00001-of-00008.safetensors` through `model-00008-of-00008.safetensors`
- `model.safetensors.index.json`
- tokenizer files

Conclusion:

The base model is available. The BioReason adapter is missing.

## Current Unity GPU State

Active jobs observed with `squeue -u alberto_paz_uri_edu`:

- `64511137`, `64511138`, `64511139`: `v1_8-D-*` jobs on `uri-gpu010/014/011`
- `64516939`: `mm_llm_finetune` on `uri-gpu004`

No BioReason inference job was started.

## Recovery Assessment

Recoverable case:

- Base model exists.

Blocking case:

- BioReason v0.2 DPO adapter/full checkpoint was not found.

Possible recovery locations to check manually:

- Any off-cluster backup not mounted under the searched Unity roots
- Local Time Machine / external backup of `outputs/BR-V02-DPO-001-A/checkpoint-step-27-epoch-1.0`
- Any previous rsync target not named in `scripts/sync_to_unity.sh`
- Any artifact store outside Unity scratch/workspace storage

Do not rerun DPO or regenerate adapters without explicit user direction.

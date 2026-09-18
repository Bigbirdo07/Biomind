# BioReason Chat Inference Audit

Date: 2026-09-16

## Request Path

Browser input is submitted from `chat/app.js` with:

`POST /api/chat`

The server handler is:

`src/bioreason/server.py::BioReasonRequestHandler._handle_chat`

The backend routing path is:

`BioReasonRequestHandler._handle_chat`
-> `BioReasonPipelineEngine.process_turn`
-> dynamic intent/state routing
-> `BioReasonInferenceRouter.generate` for normal general conversation.

Guided pipeline rendering is backend-derived structured output, not model inference.

## Model Routing

Expected model:

- Candidate: `BioReason-v0.2-Pre-Final-Candidate-001`
- Base: `Qwen/Qwen2.5-14B-Instruct`
- Checkpoint: `BR-V02-DPO-001-A / checkpoint-step-27-epoch-1.0`

Local expected checkpoint path:

`outputs/BR-V02-DPO-001-A/checkpoint-step-27-epoch-1.0`

Current local status:

`UNAVAILABLE`

Reason:

`outputs/BR-V02-DPO-001-A/` contains evaluation/manifest JSON files only. No local adapter/model weights were found at the expected checkpoint path.

Required files checked:

- `adapter_config.json`: missing
- `adapter_model.safetensors`: missing

Result:

BioReason cannot honestly report local model readiness in this workspace.

## Unity Mode

Supported environment configuration:

- `BIOREASON_BACKEND=local`
- `BIOREASON_BACKEND=unity`
- `BIOREASON_UNITY_URL=<private SSH-tunneled FastAPI URL>`

When `BIOREASON_BACKEND=unity`, the local app posts to:

`$BIOREASON_UNITY_URL/generate`

This endpoint must stay private, preferably behind SSH tunneling.

## Canned Response Origin

The repeated generic methodology text originated in:

`chat/app.js`

Removed frontend artifacts:

- `DOMAIN_KNOWLEDGE`
- `GUIDED_RNASEQ_PIPELINE`
- `generateGeneralBiologicalResponse`
- The canned fallback beginning `Thank you for sharing this scientific methodology`
- Demo-only values such as `N=12 Tumor`, `20,000 genes x 24 samples`, and `14,827 genes`

The backend no longer labels deterministic pipeline scaffolding as model-generated. It uses:

`ResponseSource.BACKEND_DERIVED`

Normal conversational model output must use:

`ResponseSource.MODEL_GENERATED`

Inference failures use:

`ResponseSource.ERROR`

## Conversation History

General model turns now receive:

- system instruction
- active serialized `PipelineContext`
- recent prior user messages
- recent prior assistant messages
- latest user message

The app no longer sends only the latest user message to the model path.

## PipelineContext Behavior

Backend state now persists:

- input type
- counts path
- group counts
- total sample count
- paired/independent design
- experimental unit
- batch columns
- PCA component count
- last pipeline change

Validated scenario:

User-provided:

- 18 Tumor
- 17 Normal
- independent patients
- batch column `sequencing_batch`
- counts file `/scratch/project/cancer/counts.csv`

Persisted context:

- `input_type = count_matrix`
- `sample_count = 35`
- `group_counts = {"Tumor": 18, "Normal": 17}`
- `paired_design = false`
- `experimental_unit = Patient`
- `batch_columns = ["sequencing_batch"]`
- `file_paths.counts = /scratch/project/cancer/counts.csv`

## Guided Pipeline Behavior

Pipeline code is generated as structured `Code | Guide` data from backend state.

The generator no longer fabricates gene counts. Unknown dimensions remain unknown until runtime:

- raw genes: `UNKNOWN`
- retained genes after filtering: computed by the script
- sample count: user-provided when known

PCA follow-ups are contextual:

- `Why PCA?`
- `Which genes contribute to PC1?`
- `Change the PCA to 50 PCs.`
- `What did you change?`

## Response Provenance

Developer-mode responses include:

- `conversation_id`
- `turn_id`
- `model`
- `checkpoint`
- `response_source`
- `mode`
- `pipeline_state`
- `pipeline_state_snapshot`
- `generation_parameters`
- `latency_ms`

## Live Real-Model Test

Script added:

`scripts/live_bioreason_chat_integration.py`

Current result:

`BIOREASON_INFERENCE_FAILED`

Reason:

`LOCAL_MODEL_RESOURCE_BLOCKER: BioReason checkpoint weights are unavailable locally.`

This is the correct behavior. Mock inference is not accepted as final validation.

## Test Results

Focused tests:

`PYTHONPATH=src python -m pytest tests/test_guided_pipeline_dynamic.py tests/test_chat_interface.py`

Result:

`14 passed`

Warning:

The local Python environment emitted a NumPy/pyarrow compatibility warning during pandas import.

## Remaining Blocker

The application integration is hardened, but the product is not fully conversational-ready until the actual frozen checkpoint is available locally or through the configured private Unity endpoint.

Final technical blocker:

`BIOREASON_MODEL_ROUTING_BLOCKER`

# BioReason First Verified SFT Report — BR-VERIFIED-SFT-001

**Status**: `FIRST_VERIFIED_BIOREASON_SFT_BASELINE`. Permanent, immutable
reference artifact. Not suitable for DPO.

## 1. Physical Adapter Evidence

- Adapter path (Unity, durable archive):
  `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-001`
- Adapter path (run output, `final_adapter` == `checkpoint-114`):
  `outputs/verified_training/BR-VERIFIED-SFT-001/final_adapter/adapter_model.safetensors`
- File size: `550,593,184` bytes
- SHA-256: `8784888ceb1753ccee956619d2f714a3a5b55656cba5205c6b56c31ca688cd52`
  — independently recomputed via `ssh unity sha256sum` on 2026-09-16 during
  this session, not merely read from a manifest. Matches
  `checkpoint_integrity.json` exactly.
- Reload verification: adapter loads via `PeftModel.from_pretrained` and
  merges cleanly onto base Qwen (used for both the live chat smoke test and
  the Dev/Regression eval run below).
- Response provenance on every recorded generation: `MODEL_GENERATED`.

## 2. Base Model and Training Provenance

- Base model: `Qwen/Qwen2.5-14B-Instruct`
- Base snapshot: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`
- Git commit at training time: `a9f2e93282c7cb5cd93bf284d385f5b7c95d7fd8`
- Training dataset: `BioReasonTrain-v0.2-SFT-v0.1`
  - train: 900 episodes, SHA-256 `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93`
  - val: 100 episodes, SHA-256 `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28`
- LoRA config: `r=32, alpha=64`, target modules `q_proj, k_proj, v_proj,
  o_proj, gate_proj, up_proj, down_proj`
- Trainable parameters: `137,625,600 / 14,907,659,264` (`0.923%`)
- Epochs: 2.0, `train_loss: 0.6247`, `eval_loss: 0.0226`
- Unity Slurm job: `64519217` (`br_verified_sft_001`), `COMPLETED`, exit
  `0:0`, start `2026-09-16T18:55:48`, end `2026-09-16T19:08:23`
  (duration 579.4s)
- Software: transformers `5.14.1`, peft `0.20.0`, trl `1.9.2`,
  accelerate `1.14.0`, torch `2.13.0+cu130`, CUDA `13.0`

## 3. Empirical Dev / Regression Evaluation

Slurm job `64521223` (`br_sft001_eval`), `COMPLETED`, exit `0:0`, same
`BioReasonDev-v0.2` (SHA-256 `6d1bba201ae81b00aff8a269a169a284a6d171b42de4f6db2c503fcbbab61d9d`)
and `BioReasonRegression-v0.1` (SHA-256 `b97e34f457d10996ebc7eeab9e2af88c47f236085b5cadbbb2862bcbddbaa470`)
sets used for the base-Qwen baseline (job `64517721`).

| Metric | Base Qwen | BR-VERIFIED-SFT-001 |
|---|---|---|
| Dev correctness proxy (n=100) | 0.40 | 0.40 |
| Regression correctness proxy (n=100) | 0.37 | **0.31** |
| Regression flaw-detection-keyword rate | 0.139 | **0.042** |
| Regression correction-keyword rate | 0.02 | 0.00 |

Prediction files (real generations, `response_source: MODEL_GENERATED`):
`outputs/verified_training/BR-VERIFIED-SFT-001/eval/dev_predictions.jsonl`,
`.../regression_predictions.jsonl`; manifest:
`.../SFT_VERIFIED_EVAL_MANIFEST.json`.

## 4. Observed Conversational Failures (Live, Real Inference)

`outputs/verified_training/BR-VERIFIED-SFT-001/live_chat_smoke.json`:

| Prompt | Behavior |
|---|---|
| `hello` | Normal conversational prose |
| `what can you do` | Normal conversational prose |
| `what is PCA` | Fixed structured-audit JSON |
| `explain pseudoreplication` | Fixed structured-audit JSON |
| `Build me an RNA-seq pipeline.` | Fixed structured-audit JSON |

## 5. Content-Collapse Example

Dev item 0, expected flaw `longitudinal_patient_leakage`. Model output:

```json
"identified_issues": ["data_leakage"],
"recommended_analysis": "Rigorous methodology enforcing statistical invariants."
```

The generic taxonomy category is present; the scenario-specific mechanism
(repeated observations from the same patient crossing train/test partitions)
is absent. See `BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md` Section 7 for the
full quantitative content-specificity audit (100% of flawed training targets
are generic-label-only — the model reproduces this pattern at inference
time).

## 6. Root Causes (Full Detail in `BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md`)

1. **Format collapse**: 1000/1000 training targets are JSON, 1 distinct
   field order, 100% share 3 identical stock phrases.
2. **Content collapse**: 100% of flawed-episode targets state the issue as a
   generic taxonomy label only, never a scenario-specific mechanism.
3. **No assistant-only label masking**: `DataCollatorForLanguageModeling`
   applies loss across system/user/assistant tokens, reinforcing the fixed
   user-prompt template too.
4. **System prompt is not the cause**: it already instructs conditional,
   conversational behavior; the dataset never demonstrated that behavior.

## 6b. ConversationDev-v0.1 Comparison (Full 120-Turn Set, Real Inference)

Slurm jobs `64521975` (base Qwen, `COMPLETED`) and `64521976` (SFT-001,
`COMPLETED`) ran the full `BioReasonConversationDev-v0.1` set (120 turns,
93 conversations, real multi-turn replay using each model's own prior
generations as context) with identical settings. Format-pathology metrics:

| Metric | Base Qwen | BR-VERIFIED-SFT-001 |
|---|---|---|
| Natural response rate | **100%** | **11.7%** |
| Unwanted JSON rate | 0% | **81.7%** |
| Unwanted rubric-language rate | 2.5% | **81.7%** |
| Stock-phrase rate | 0% | **88.3%** |
| Avg. response length (words) | 173.2 | 50.5 |

Per-mode breakdown for SFT-001 (`n` = turns in that mode; base Qwen was 0%
unwanted-JSON on every mode except 2 teaching turns and 1
insufficient-information turn):

| Expected mode | n | SFT-001 unwanted JSON |
|---|---|---|
| GENERAL_CHAT | 10 | 0 / 10 |
| CAPABILITY | 5 | 2 / 5 |
| TEACHING | 39 | **38 / 39** |
| SCIENTIFIC_REASONING | 16 | **16 / 16** |
| SCIENTIFIC_AUDIT | 8 | 0 / 8 (JSON here is appropriate) |
| PIPELINE_INTAKE | 6 | **6 / 6** |
| PIPELINE_BUILD | 8 | **8 / 8** |
| PIPELINE_FOLLOWUP | 2 | **2 / 2** |
| CODE_EXPLANATION | 8 | **8 / 8** |
| DEBUGGING | 4 | **4 / 4** |
| SHORT_CONTEXTUAL_FOLLOWUP | 8 | **8 / 8** |
| INSUFFICIENT_INFORMATION | 6 | **6 / 6** |

This is the full-scale confirmation of the 5-turn smoke test: SFT-001 stays
natural essentially only on bare greetings (GENERAL_CHAT). Every other mode
— including modes with zero representation in the training data (pipeline,
debugging, code explanation, short follow-ups) — collapses into the fixed
JSON/rubric schema, matching the root cause in
`BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md`. Base Qwen, with no specialization
at all, handles all 12 modes naturally.

## 7. Limitations

- Metrics are keyword-proxy correctness measures, not a calibrated scientific
  rubric grader — real but coarse.
- Live conversational smoke test is 5 turns; a full 120-item
  `BioReasonConversationDev-v0.1` comparison (base Qwen vs. SFT-001) is the
  next deliverable and will provide statistically broader evidence.
- Base-vs-SFT-001 comparison uses only Dev/Regression (scientific-audit
  style items); it does not yet include conversational/teaching/pipeline
  prompts, which is exactly the gap `BioReasonConversationDev-v0.1` closes.

## 8. Conclusion

**BR-VERIFIED-SFT-001 is a genuine, physically verified neural model** — not
a simulation, not a fabricated claim. Its training ran on real Unity GPU
hardware, produced non-zero learned weights with a verified hash, and its
outputs are confirmed `MODEL_GENERATED` at inference time. **It is not
conversationally or scientifically acceptable for DPO.** Formal decision:
`SFT_001_SCIENTIFIC_REGRESSION` (see diagnosis doc Section 10 for why this is
not downgraded to a pure formatting issue). It is retained permanently as
`FIRST_VERIFIED_BIOREASON_SFT_BASELINE` and will not be overwritten. Repair
path: `BIOREASON_SFT_V2_DATA_MIX_PLAN.md` → `BR-VERIFIED-SFT-002`.

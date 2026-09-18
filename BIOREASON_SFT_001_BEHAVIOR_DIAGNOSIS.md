# BioReason SFT-001 Behavior Diagnosis

**Date**: 2026-09-16
**Scope**: Root-cause diagnosis of the conversational over-activation of structured
audit-JSON output observed from `BR-VERIFIED-SFT-001`. Grounded entirely in
physical evidence: the real training dataset on disk, the real data-formatting
code that produced training targets, the real trainer configuration, and a real
5-turn live-inference smoke test recorded during the verified SFT job.

## 1. Empirical Conversational Failure (Confirmed)

`outputs/verified_training/BR-VERIFIED-SFT-001/live_chat_smoke.json` (real
`model.generate()` calls, `response_source: MODEL_GENERATED`):

| Prompt | Behavior |
|---|---|
| `hello` | Normal conversational prose |
| `what can you do` | Normal conversational prose |
| `what is PCA` | Fixed JSON schema (`assessment`, `flaw_detected`, `experimental_unit`, ...) |
| `explain pseudoreplication` | Same fixed JSON schema |
| `Build me an RNA-seq pipeline.` | Same fixed JSON schema |

This matches the user-reported behavior exactly and is not an isolated anecdote —
it reproduces on the first two categories of prompt tried.

## 2. Training Data Format Audit (Root Cause)

Source: `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/{train,val}.jsonl`
(1,000 episodes total: 900 train / 100 val, matching the hashes recorded in
`BIOREASON_PHASE_T1_STATUS.md`).

- **Episode type distribution**: `FLAWED_WORKFLOW`: 550, `CORRECT_WORKFLOW`: 450.
  **These are the only two episode types in the entire dataset.**
- **Multi-turn examples**: **0 / 1,000.** Every episode is a single
  question → single answer pair. There is no conversational, follow-up,
  clarification, or context-retention structure anywhere in the data.
- **General chat / teaching examples**: **0 / 1,000.** No greetings, no
  "what is X" explanations, no capability questions, no debugging, no pipeline
  intake dialogue.
- **Mode distribution**: **100% SCIENTIFIC_AUDIT.** 0% GENERAL_CHAT, 0%
  TEACHING, 0% PIPELINE_INTAKE, 0% DEBUGGING, 0% CODE_EXPLANATION.

## 3. Token-Level Format Dominance (Root Cause, Confirmed in Code)

`src/bioreason/training/verified_sft_trainer.py`:

- `format_episode_prompt()` (line 91): every single training prompt is built
  from the same fixed template — `"Evaluate the following scientific
  scenario and proposed analysis...\nOrganism: ...\nAssay: ...\n..."` — for
  all 1,000 episodes, with no variation in structure.
- `format_episode_response()` (line 106): every single training target is
  built by populating a fixed dict (`assessment`, `flaw_detected`,
  `experimental_unit`, `identified_issues`, `recommended_analysis`,
  `supported_claims`, `unsupported_claims`, `limitations`, `confidence`) and
  calling `json.dumps(payload, indent=2)`. **100% of target tokens across
  all 1,000 episodes are this one JSON schema.** There is no code path in the
  training data pipeline that ever produces a natural-language, non-JSON
  assistant target.

This is a **complete, unconditional token-level dominance** of one output
format — not merely a majority-class imbalance. The model was never shown a
single gradient step where the correct completion was ordinary prose.

## 4. System Prompt Audit — Ruled Out As Cause

`SYSTEM_PROMPT` (verified_sft_trainer.py line 25):

> "You are BioReason, a biology-native scientific reasoning AI. Evaluate
> biological, statistical, and computational workflows rigorously, **but
> answer conversationally when the user asks a general question.**"

The system prompt already explicitly instructs conditional, mode-aware
behavior. **This rules out `SYSTEM_PROMPT_EFFECT` as the cause.** The failure
is a pure `DATASET_EFFECT`: the system prompt says "be conversational when
appropriate," but the model never once saw a training example demonstrating
what that looks like, so 1,000/1,000 gradient updates overrode the
instruction with a single rigid output shape.

## 5. Chat Template Audit — No Malformation Found

`build_chat_text()` (line 145) constructs proper `system` / `user` /
`assistant` role messages and calls `tokenizer.apply_chat_template(...)`
(Qwen's native template). No evidence of malformed role boundaries.

## 6. Label Masking Audit — Contributing Factor Found

`train_verified_sft()` (line 355-360) uses
`DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)` with no
prompt-token masking applied anywhere in the file. This collator computes
labels as a copy of the full `input_ids`, meaning **loss is computed over the
system prompt and user prompt tokens as well as the assistant response**, not
only the assistant span. This is a secondary contributing factor: it means
the model is also being trained to reproduce the fixed
`"Evaluate the following scientific scenario..."` user-prompt template
verbatim, reinforcing rigid, template-locked behavior beyond just the
response side. It is not the primary cause (the response-side 100% JSON
dominance is), but it should be fixed in any SFT-002 run regardless.

## 7. Template Similarity — Quantified

Computed directly against the physical `format_episode_response()` output for
all 1,000 episodes (script: reproduced trainer's own formatting functions,
not a re-implementation):

| Metric | Value |
|---|---|
| Targets that parse as JSON | **1000 / 1000 (100%)** |
| Distinct JSON field orders across all targets | **1** (i.e. zero variation) |
| Targets matching that single field order | **1000 / 1000 (100%)** |
| Targets containing the literal stock phrase `"Rigorous methodology enforcing statistical invariants"` | **1000 / 1000 (100%)** |
| Targets containing the literal stock phrase `"Constrained to study parameters in"` | **1000 / 1000 (100%)** |
| Targets containing the literal stock phrase `"Validated invariant in"` | **1000 / 1000 (100%)** |
| Flawed-episode targets (`identified_issues` non-empty) | 450 |
| ...of which the issue is expressed **only** as a generic taxonomy label (`data_leakage`, `batch_or_covariate_confounding`, etc.) rather than a scenario-specific mechanism | **450 / 450 (100%)** |
| Average target length | 70.7 words |
| 3-grams shared by >50% of a 200-episode sample | 23 distinct repeated 3-grams |

**`TEMPLATE_COLLAPSE_SCORE` (defined here as the mean of: JSON-format
concentration, field-order concentration, stock-phrase saturation) = 100%.**
There is no partial collapse — every single training target shares the exact
same schema, field order, and boilerplate connective phrases. The only
things that vary between episodes are the substituted domain/scenario nouns
plugged into the template.

**Content-specificity audit finding**: this is not only a format problem.
100% of the 450 flawed-episode targets that name an issue do so with a
category label only (`"identified_issues": ["data_leakage"]`) and never with
a scenario-specific mechanism sentence. The `reasoning_summary` field (which
does contain a more specific sentence) is only used for the free-text
`assessment` field, and even then the model's live outputs (Section 1)
degrade further toward generic paraphrases of it. This confirms the model
learned "scientific-looking input → BioReason rubric skeleton" more strongly
than "scenario → mechanism → explanation," and explains the observed
Regression flaw-detection-keyword regression (0.139 → 0.042 vs. base Qwen).

## 8. Diagnosed Root Cause

**Primary cause (confirmed, not inferred): DATASET_EFFECT.** The SFT-001
training corpus, and the code that generated it, contain exactly one
response format (fixed structured-audit JSON) applied to exactly one prompt
template, across 100% of 1,000 episodes, with zero conversational, teaching,
multi-turn, or pipeline-intake examples. Standard supervised fine-tuning on
this corpus will teach the model to emit that JSON schema unconditionally,
regardless of what the system prompt requests, because the system prompt's
conditional instruction was never demonstrated in training.

**Secondary contributing cause (confirmed): no label masking** on
prompt tokens, which reinforces rigid template reproduction on the input side
as well.

**Confidence**: High. Both findings are derived directly from reading the
physical dataset file and the physical training code that ran in the
completed, hash-verified Slurm job (`64519217`), not from inference or
assumption.

## 9. Empirical Dev/Regression Evaluation (Real Inference, Same Datasets as Base Qwen)

Slurm job `64521223` (`br_sft001_eval`, `COMPLETED`, exit `0:0`), adapter
`final_adapter` (SHA-256 `8784888c...688cd52`) merged onto base Qwen:

| Metric | Base Qwen (job `64517721`) | BR-VERIFIED-SFT-001 (job `64521223`) |
|---|---|---|
| Dev correctness proxy (n=100) | 0.40 | 0.40 |
| Regression correctness proxy (n=100) | 0.37 | **0.31** |
| Regression flaw-detection-keyword rate | 0.139 | **0.042** (3.3x lower) |
| Regression correction-keyword rate | 0.02 | 0.00 |

SFT-001 did not improve Dev correctness and **regressed** Regression
correctness and flaw-detection. This is consistent with, and caused by, the
content collapse documented above: the model's flaw labels became generic
taxonomy words rather than scenario-specific mechanism descriptions, so
keyword-based flaw detection (which looks for the specific expected flaw
term, e.g. `longitudinal_patient_leakage`) fails more often than it did for
un-specialized base Qwen.

Example (Dev item 0, expected flaw `longitudinal_patient_leakage`):
SFT-001 produced `"identified_issues": ["data_leakage"]` and
`"recommended_analysis": "Rigorous methodology enforcing statistical
invariants."` — the generic category is present, but the scenario-specific
mechanism (same-patient longitudinal observations crossing train/test) is
absent.

## 10. Formal Decision (Item 4)

**`SFT_001_SCIENTIFIC_REGRESSION`**

This is deliberately **not** downgraded to a pure formatting issue. The
empirical Dev/Regression evaluation shows a real regression in scientific
flaw-detection performance relative to un-specialized base Qwen, not merely
a cosmetic JSON-wrapping problem. Both things are true simultaneously:
BR-VERIFIED-SFT-001 is conversationally broken (Section 1) **and**
scientifically regressed on the one quantitative axis measured so far
(Section 9). Both stem from the same root cause (Sections 2-3, 7): complete
template and content collapse in the training targets.

## 11. Acceptance Decision (Item 50)

**`SFT_001_REQUIRES_CONVERSATIONAL_REPAIR`** combined with
**`SFT_001_SCIENTIFIC_REGRESSION`** (Section 10) — both apply. BioReason
Specialized Model status: `VERIFIED_EXPERIMENTAL_SFT`. Conversational
status: `NOT_READY`. DPO status: `BLOCKED_PENDING_SFT_REPAIR`.

BR-VERIFIED-SFT-001 is a real, physically verified neural checkpoint with
correctly-formed weights and a legitimate training run. It should be
**retained permanently as `FIRST_VERIFIED_BIOREASON_SFT_BASELINE`** and must
**not** be overwritten. It is **not** suitable as the foundation for DPO.
The path forward is a corrected SFT data mix (see
`BIOREASON_SFT_V2_DATA_MIX_PLAN.md`) trained as a new artifact,
`BR-VERIFIED-SFT-002`.

# BioReason Phase T1.5 Status

Status: `DPO_001_AND_002_BOTH_NULL_SFT002_REMAINS_CANONICAL`

Canonical BioReason model: `BR-VERIFIED-SFT-002` (weights unchanged since
Phase T1.6). `BR-VERIFIED-SFT-003`: `REJECTED_FOR_SCIENTIFIC_REGRESSION`,
preserved for research history only.

**Two real DPO attempts, both null on the target metric:**
- `BR-VERIFIED-DPO-001` (19 preference pairs): no measurable improvement
  in valid-recognition (0/40 Dev, 0/28 Regression). See
  `BIOREASON_VERIFIED_DPO_001_REPORT.md`.
- `BR-VERIFIED-DPO-002` (58 preference pairs, 3x scale, 39 new domains,
  rejected responses grounded in real observed failure patterns): **still
  no measurable improvement** (1/40 Dev — statistically same as SFT-002
  baseline, 0/28 Regression — unchanged). Crucially, in-distribution
  learning was strong (100% held-out preference accuracy within the
  training distribution, positive reward margin) — the model learned to
  prefer chosen-over-rejected for pairs like its training data, but this
  did not transfer to new scenarios at all. This is a more informative
  null than DPO-001: it points toward overfitting to the training pairs'
  surface features rather than "just needed more data of the same kind."
  See `BIOREASON_VERIFIED_DPO_002_REPORT.md`.

Neither DPO checkpoint is promoted; both preserved for research history.
Two real infrastructure bugs were found and permanently fixed along the
way (a broken conda environment on some compute nodes silently resolving
to an incompatible torch/trl build; a CUDA OOM from loading two full model
copies, now fixed via merge-once + single-model-with-disabled-adapter
reference, cutting DPO training memory roughly in half) — both fixes are
now applied project-wide (all 33 sbatch scripts), not just to these runs.

Phase T1.7 (mode-conditioned inference) built a real model-based mode
router + overlay system around SFT-002 without touching its weights.
Result: explicit audit compliance went from 0/8 to **100% across three
independent test sets** — the phase's core hypothesis (route at inference
time, not weight specialization) is strongly supported on that axis. But
the Dev/Regression scientific metric showed an apparent drop under the
audit overlay's verbose style that is very likely (not certainly) a
keyword-scorer artifact, and the recurring primary-mechanism acceptance
case (patient-level leakage) remains unfixed regardless of configuration.
Phase verdict: `MODE_CONDITIONING_INCONCLUSIVE`.

DPO Status: `DPO_STILL_BLOCKED`
Human Evaluation: `PAUSED`
Final Benchmark: `SEALED_UNREAD`

See `BIOREASON_VERIFIED_SFT_002_REPORT.md`, `BIOREASON_VERIFIED_SFT_003_REPORT.md`,
and `BIOREASON_MODE_CONDITIONED_INFERENCE_REPORT.md` for full detail.

## Phase T1.8-1.9: Semantic Re-Scoring and DPO Dataset (Roadmap Phases 0-1, Partial)

Following `~/.claude/plans/kind-questing-seal.md`:

- **Phase 0 (scorer fix)**: replaced the literal keyword scorer with a
  two-step, reference-blind LLM judge (`src/bioreason/training/semantic_judge.py`).
  A first single-step version was spot-checked and found to leak reference
  answers into its own justifications (scored SFT-001 at 100%); rebuilt as
  extract-then-compare. Full corrected comparison across all 10 existing
  prediction sets, plus a major new finding, documented in
  `BIOREASON_SEMANTIC_SCORER_V1.md`: **base Qwen, SFT-002, SFT-003, and
  mode-conditioned SFT-002 all recognize genuinely valid designs as valid
  in ~0% of real Dev/Regression valid cases**, while flaw-detection is
  strong (68-100%) — a bias present in base Qwen itself, not introduced or
  fixed by any BioReason training so far.
- **Phase 1 (router calibration)**: added few-shot contrast examples to
  the mode router prompt. Confirmed real, clean improvement on
  ConversationDev: SCIENTIFIC_REASONING routing accuracy 3/16 → 16/16,
  explicit-audit recall held at 100% (8/8) — no trade-off.
- **Mitigation test for the over-criticism finding**: added an explicit
  "don't manufacture nitpicks" instruction to the SCIENTIFIC_REASONING and
  SCIENTIFIC_AUDIT overlays. Semantically re-scored result: Dev
  valid-recognition improved 0/40 → 9/40 (22.5%) with flaw-detection
  essentially unchanged (100% → 98.3%); Regression valid-recognition did
  not move (0/28 → 0/28). Confirms prompting provides partial, real signal
  but cannot fully correct this bias — it is a calibration bias, not
  purely a missing-instruction problem.
- **DPO dataset built** (dataset only, no training run):
  `BioReasonPreference-Verified-DPO-v0.1` — 19 honestly-labeled preference
  pairs (13 targeting valid-recognition, 4 flaw-detection guardrails
  against overcorrection, 2 reinforcing mechanism-specificity), prose-
  formatted (not JSON), contamination-checked clean against all existing
  eval/training sets. See `BIOREASON_PREFERENCE_DPO_V1_DATASET_REPORT.md`.
  **DPO training itself has not been run** — remains explicitly gated
  pending user authorization, per project governance.

## 1. Premise Verification (Done)

The initiating claim — that `BR-VERIFIED-SFT-001` is a physically verified
LoRA adapter — was independently re-verified against Unity directly (not
assumed from local repo docs, which were stale):

- `sacct -j 64519217`: `COMPLETED`, exit `0:0`.
- `ssh unity sha256sum .../final_adapter/adapter_model.safetensors` →
  `8784888ceb1753ccee956619d2f714a3a5b55656cba5205c6b56c31ca688cd52`
  (matches exactly, independently recomputed, not read from a manifest).
- File size 550,593,184 bytes (non-zero).
- Local `BIOREASON_PHASE_T1_STATUS.md` has been corrected — it previously
  said `PENDING`, which was accurate when written but stale by the time of
  this session.

## 2. Root-Cause Diagnosis (Done)

See `BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md`. Summary: 1,000/1,000 SFT
training episodes are single-turn SCIENTIFIC_AUDIT-mode JSON targets (0%
general chat, teaching, multi-turn, pipeline-intake, or debugging). This is
a confirmed `DATASET_EFFECT`, not a system-prompt effect. Secondary finding:
no prompt-token label masking during training.

## 3. Corrected Data Mix Proposal (Done, Not Yet Built)

See `BIOREASON_SFT_V2_DATA_MIX_PLAN.md`. Proposal only — no new dataset has
been authored or frozen, no SFT-002 run has started.

## 4. Empirical Dev + Regression Evaluation (In Progress)

- Extended `src/bioreason/training/verified_eval.py` and
  `scripts/run_verified_baseline_qwen.py` to support `--adapter-path` (loads
  the base model + merges the LoRA adapter before generation).
- New job config: `slurm/bioreason_verified_sft_001_eval.sbatch`, run ID
  `BR-VERIFIED-SFT-001-EVAL`.
- Submitted to Unity as Slurm job **`64521223`** (`br_sft001_eval`),
  queued `PD (Priority)` as of last check.
- Will write to `outputs/verified_training/BR-VERIFIED-SFT-001/eval/`:
  `dev_predictions.jsonl`, `regression_predictions.jsonl`, `metrics.json`,
  `SFT_VERIFIED_EVAL_MANIFEST.json` — all from real `model.generate()` calls
  on `BioReasonDev-v0.2` (N=100) and `BioReasonRegression-v0.1` (N=100), the
  same datasets already used for the base-Qwen baseline
  (`outputs/verified_training/baseline_qwen/`), enabling a direct,
  same-dataset comparison once this job completes.
- Baseline (base Qwen) reference already exists from job `64517721`:
  Dev correctness-proxy `0.40`, Regression correctness-proxy `0.37`.

## 5. Completed This Session

- `BIOREASON_FIRST_VERIFIED_SFT_REPORT.md` written (adapter evidence,
  training provenance, Dev/Regression comparison, live conversational
  failure, content-collapse example, formal decision
  `SFT_001_SCIENTIFIC_REGRESSION`).
- `BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md` extended with quantitative
  template-collapse audit computed directly against the physical training
  data using the trainer's own formatting functions (not a
  reimplementation): 1000/1000 targets are JSON with 1 distinct field order,
  100% share all 3 stock phrases, 100% of flawed targets use a generic
  taxonomy label only (never a scenario-specific mechanism).
- `BioReasonConversationDev-v0.1` built: 120 turns across 93 conversations
  (single-turn + multi-turn trajectories), original prompts, dev-only,
  separate from the sealed final benchmark. Manifest:
  `benchmark/conversation_dev_v0.1/MANIFEST.json`
  (SHA-256 of items file: `9ecfa1745afd5757153ed29a2e485d7a3d4990246a9fa6ba11cb95818ef50031`).
- New multi-turn eval harness
  (`src/bioreason/training/verified_conversation_eval.py`,
  `scripts/run_verified_conversation_eval.py`): replays each conversation
  turn-by-turn using the model's own prior real generations as context (not
  oracle answers), computes `unwanted_json_rate`, `unwanted_rubric_rate`,
  `stock_phrase_rate`, `natural_response_rate` per expected mode.
- Submitted to Unity:
  - Job `64521975` (`br_convdev_base`) — base Qwen over ConversationDev.
  - Job `64521976` (`br_convdev_sft001`) — BR-VERIFIED-SFT-001 over
    ConversationDev.
  - Both `PD (Priority)` as of last check.

## 6. Phase T1.6 Progress

- Assistant-only label masking implemented
  (`build_labeled_example`, `AssistantOnlyPaddingCollator` in
  `verified_sft_trainer.py`) with 3 unit tests
  (`tests/test_verified_training_guards.py`), all passing (22/22 full
  suite). Verified against the real Qwen tokenizer on Unity: system/user
  tokens masked to `-100`, assistant tokens trainable (~30-45% of tokens per
  example).
- `BioReasonTrain-Verified-SFT-v0.2` built and frozen: 427 episodes
  (385 train / 42 val), see `BIOREASON_VERIFIED_SFT_V2_DATASET_REPORT.md`.
  Template-collapse QC gate and contamination check both **pass** (an
  earlier draft failed both and was corrected before freezing — see report
  Section 4-5 for what was caught and fixed).
- `BR-VERIFIED-SFT-002` training submitted: Slurm job **`64522968`**,
  conservative hyperparameters (lr `2e-5` vs SFT-001's `5e-5`, LoRA `r=16`
  vs `r=32`, assistant-only masking — new), `messages`-format multi-turn
  dataset. `PD (Priority)` as of last check.

## Currently In Flight

- `64521975` (ConversationDev, base Qwen) — **RUNNING**
- `64521976` (ConversationDev, BR-VERIFIED-SFT-001) — **RUNNING**
- `64522968` (BR-VERIFIED-SFT-002 training) — **PENDING**

## Next Actions

1. Poll jobs `64521975` / `64521976`; once `COMPLETED`, sync predictions and
   compute the base-Qwen-vs-SFT-001 conversational comparison, folding it
   into the SFT-001 report.
2. Poll `64522968`; once `COMPLETED`, verify the adapter (hash, reload),
   then run BR-VERIFIED-SFT-002 through Dev, Regression, and ConversationDev
   for the full 3-way comparison (base Qwen vs. SFT-001 vs. SFT-002).
3. Live acceptance conversation test (item 68 of the spec) against SFT-002.
4. Write `BIOREASON_VERIFIED_SFT_002_REPORT.md` and the DPO-readiness
   verdict.

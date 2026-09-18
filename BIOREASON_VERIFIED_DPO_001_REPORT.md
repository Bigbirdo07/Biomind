# BioReason Verified DPO-001 Report

**Status**: `VERIFIED_EXPERIMENTAL_DPO`. Real, physically verified adapter,
trained via TRL's `DPOTrainer` on `BR-VERIFIED-SFT-002`. **Result: null —
no measurable improvement on the targeted bias, no regression either.**

## 1. Lineage and Training Provenance

- Base model: `Qwen/Qwen2.5-14B-Instruct`
- **Parent: `BR-VERIFIED-SFT-002`** (canonical model, unchanged)
- Dataset: `BioReasonPreference-Verified-DPO-v0.1` (19 pairs: 17 train / 2
  val — 13 valid-recognition + 4 flaw-detection guardrails + 2 specificity)
- New training module: `src/bioreason/training/verified_dpo_trainer.py`
  (separate from the historical simulation-only `dpo_trainer.py`, mirroring
  `verified_sft_trainer.py`'s pattern: real TRL `DPOTrainer`, physical
  checkpoint verification, hash-checked archiving)
- LoRA: inherited from the resumed SFT-002 adapter, r=16/alpha=32
- Learning rate: `5e-6`, beta: `0.1`, epochs: `3.0`,
  `gradient_accumulation_steps: 2` (tuned down from the default 8 for this
  small 17-pair train set, to get ~27 optimizer steps instead of ~2)
- Slurm job: **`64545047`** (`br_verified_dpo_001`), `COMPLETED`, exit
  `0:0`, duration 53.7s
- `train_loss: 0.585`, `eval_loss: 0.664` (2 val examples — not
  statistically meaningful on its own; `eval_rewards/accuracies: 0.5`,
  i.e. chance level on n=2)

## 2. Physical Adapter Evidence

- Adapter: `outputs/verified_training/BR-VERIFIED-DPO-001/final_adapter/adapter_model.safetensors`
- SHA-256: `7f3ad6faabb3fdd7a07e237c7b2a2c60ae0db11529e850929675fbc87ecaef13`
  — independently recomputed via `ssh unity sha256sum` on both the run
  output and the durable archive copy; both match exactly
- Durable archive:
  `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-DPO-001`
- A benign discrepancy was investigated and resolved: `final_adapter`
  (137.7MB) is exactly half the size of the intermediate
  `checkpoint-9`/`checkpoint-27` (275.3MB each). Verified via direct tensor
  inspection: both have identical tensor counts (672) and shapes; the
  intermediate checkpoints were saved in fp32 (HF Trainer's automatic
  checkpoint default) while `final_adapter` was saved in bf16 (the
  explicit final `save_pretrained()` call). No data loss — confirmed by
  direct dtype/shape inspection, not assumed.

## 3. Dev / Regression Results (Semantic Scorer) — The Real Verdict

Using the two-step, reference-blind semantic judge from
`BIOREASON_SEMANTIC_SCORER_V1.md` (not the unreliable keyword scorer),
scored on the exact same held-out Dev/Regression items used throughout
this project — **none of which were in the 19-pair training set**:

| Metric | SFT-002 (before) | DPO-001 (after) |
|---|---|---|
| Dev valid-recognition | 1/40 (2.5%) | 0/40 (0%) |
| Dev flaw-detection | 100% | 100% |
| Regression valid-recognition | 0/28 (0%) | 0/28 (0%) |
| Regression flaw-detection | 72.2% | 72.2% |

**No measurable movement in either direction on the primary target
(valid-recognition).** Flaw-detection is exactly unchanged, which is a
genuinely useful negative result: it confirms the 4 guardrail pairs
successfully prevented any drift toward "just say everything is fine"
(the failure mode this dataset was explicitly designed to avoid), but it
also means the 13 valid-recognition pairs produced no detectable
generalization to new, unseen scenarios.

## 4. Spot Check — Consistent With the Null Result

Reading actual DPO-001 responses on Dev valid items (e.g.
`DEV_V02_004_MICROB`, the SparCC/microbiome scenario) shows the same
"hedge then invent a nitpick" pattern as before, in one case with a
factually backwards framing (arguing SparCC has "limitations with
compositional data" when SparCC's specific design purpose is correctly
handling compositional data — the opposite of a genuine flaw). This
confirms the semantic scorer's `0/40` is not a scoring artifact; the
underlying behavior genuinely did not change.

## 5. ConversationDev Format Check — No Regression

| Metric | SFT-002 unconditioned | DPO-001 |
|---|---|---|
| Natural response rate | 100% | 100% |
| Unwanted JSON rate | 0% | 0% |
| Unwanted rubric rate | 1.7% | 2.5% |
| Avg. response length | 140.6 words | 158.0 words |

DPO training did not disturb the conversational format gains from earlier
phases — this is a clean, isolated null result on the one axis it
targeted, not a broader regression.

## 6. Why This Happened (Assessed, Not Guessed)

19 preference pairs (17 used for training) is a very small dataset for
shifting a calibration bias in a 14.8B-parameter model, even with LoRA.
The `BioReasonPreference-Verified-DPO-v0.1` report explicitly flagged this
going in: *"19 pairs is intentionally small — a first, disciplined
increment... not a claim that this alone is enough training signal to run
DPO on."* This result confirms that caveat empirically rather than leaving
it as a hypothesis: at this scale, DPO produced a real, measurable
training signal (loss decreased, reward margins were computed correctly)
but not enough generalizable signal to move behavior on genuinely new
scenarios.

## 7. Conclusion and Recommendation

**BR-VERIFIED-DPO-001 is a real, physically verified DPO checkpoint — the
training pipeline itself worked correctly end-to-end (real TRL DPOTrainer,
real gradient updates, real hash-verified checkpoint).** It does not
improve on `BR-VERIFIED-SFT-002` and is not being promoted to canonical
status. `BR-VERIFIED-SFT-002` remains canonical.

This is not a dead end — it is the expected outcome of a deliberately
small first increment, and it validates the DPO training infrastructure
(`verified_dpo_trainer.py`) for future use. Per the original roadmap
(`~/.claude/plans/kind-questing-seal.md`, Phase 3), the next step for this
specific bias is scaling the preference dataset substantially (the
roadmap's own target for other datasets was one to two orders of
magnitude larger than a 19-pair first pass) before attempting DPO again,
now that the actual training path is proven to work.

## 8. Not Performed

- `BR-VERIFIED-SFT-002` was not overwritten or superseded.
- `BR-VERIFIED-DPO-001` is not being promoted or used as a new canonical
  model.
- No further DPO run was started automatically.
- The sealed final benchmark was not opened.

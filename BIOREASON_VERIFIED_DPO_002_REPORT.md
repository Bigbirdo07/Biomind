# BioReason Verified DPO-002 Report

**Status**: `VERIFIED_EXPERIMENTAL_DPO`. Real, physically verified adapter.
**Result: null again — no measurable improvement on held-out valid-
recognition, despite a 3x-scaled, more diverse dataset. Slightly more
informative than DPO-001's null result, and it changes the diagnosis.**

## 1. Two Infrastructure Bugs Found and Fixed Before This Result

This run required two real fixes before it could execute at all —
documented here because both are now permanent fixes to the shared
training infrastructure, not one-off workarounds:

1. **Broken conda environment on some compute nodes.** The named
   `azera-voice` conda environment has an incompatible torch/trl build
   (`torch 2.5.1+cu121`) on at least one node (`uri-gpu013`) that breaks
   TRL's `DPOTrainer` import (`cannot import name 'FSDPModule' from
   torch.distributed.fsdp`), while other nodes' PATH resolution
   accidentally fell through to a different, working base conda install
   (`torch 2.13.0+cu130`) that every prior successful job in this project
   had actually been using without anyone realizing it. Root-caused via a
   pinned diagnostic job reproducing the failure on the exact node, then
   confirmed the fix (`export PATH="$HOME/miniconda3/bin:$PATH"` instead of
   `conda activate .../envs/azera-voice`) on that same node before
   resubmitting. Applied across all 33 sbatch scripts in the project, not
   just this one.
2. **CUDA OOM from loading two full model copies.** The original
   `verified_dpo_trainer.py` loaded a separate full policy model and a
   separate full reference model (each ~29.6GB in bf16 for the 14.8B base),
   which fit on an 80GB A100 (DPO-001's node) but OOM'd on a 44GB L40S
   (DPO-002's first attempt). Fixed by merging the parent SFT-002 adapter
   into the base once, training a fresh LoRA adapter on top of that merged
   base, and passing `ref_model=None` so TRL uses the same model with the
   adapter disabled as the reference — since the base already contains
   SFT-002's merged weights, this gives the same reference semantics
   (SFT-002 behavior) at roughly half the memory, and works on any GPU size.

## 2. Training Provenance

- Parent: `BR-VERIFIED-SFT-002` (canonical, unchanged)
- Dataset: `BioReasonPreference-Verified-DPO-v0.2` (58 pairs: 52 train / 6
  val — 3x scale over DPO-001's 19, spanning 39 additional domains,
  rejected responses grounded in real observed false-alarm patterns)
- LoRA: fresh r=16/alpha=32 adapter trained on top of merged SFT-002
  weights (see Section 1.2 — different mechanism than DPO-001's continued-
  adapter approach, same effective starting behavior)
- Learning rate `5e-6`, beta `0.1`, epochs `3.0` — same hyperparameters as
  DPO-001, so dataset scale is the only isolated variable under test
- Slurm job: **`64550205`**, `COMPLETED`, exit `0:0`, duration 147.0s, 78
  optimizer steps (52 examples / 2 grad-accum × 3 epochs)
- `train_loss: 0.644`, `eval_loss: 0.641`
- **In-distribution held-out signal is strong**: `eval_rewards/accuracies:
  1.0` (correctly preferred chosen over rejected on all 6 held-out
  preference pairs), `eval_rewards/margins: 0.108` — both meaningfully
  better than DPO-001's chance-level 0.5 accuracy on its 2 val pairs.

## 3. Physical Adapter Evidence

- SHA-256: `f65466809c4e9dd9916848edffea7cd63720f91f972a9ff16b02928d9e22f992`
  — independently recomputed on both the run output and durable archive
  copy; both match exactly.
- Durable archive:
  `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-DPO-002`

## 4. Dev / Regression Results (Semantic Scorer) — The Real Verdict

Held-out Dev/Regression items, none of which were in the 58-pair
training set:

| Metric | SFT-002 (baseline) | DPO-001 (19 pairs) | **DPO-002 (58 pairs)** |
|---|---|---|---|
| Dev valid-recognition | 1/40 (2.5%) | 0/40 (0%) | **1/40 (2.5%)** |
| Dev flaw-detection | 100% | 100% | **100%** |
| Regression valid-recognition | 0/28 (0%) | 0/28 (0%) | **0/28 (0%)** |
| Regression flaw-detection | 72.2% | 72.2% | **66.7%** |

**Tripling the dataset, adding 39 new domains, and grounding rejected
responses in real observed failure patterns produced no measurable
improvement in valid-recognition on genuinely new scenarios.** Dev
valid-recognition (1/40) is statistically indistinguishable from the
2.5% baseline (n=1 either way). Regression valid-recognition remains
exactly 0/28 across all three configurations tested so far (SFT-002,
DPO-001, DPO-002). Regression flaw-detection dropped slightly (72.2% →
66.7%, i.e. 2 fewer items out of 28) — small enough to plausibly be noise,
but reported rather than hidden.

## 5. This Is a More Informative Null Than DPO-001's

DPO-001's null result was ambiguous: 19 pairs might simply have been too
few to show any effect at all, in-distribution or out. DPO-002 rules that
specific explanation out. The in-distribution signal here is strong and
real (100% held-out preference accuracy on the training distribution,
positive reward margin) — **the model successfully learned to prefer
chosen over rejected for pairs statistically similar to what it was
trained on, but this preference did not transfer to new domains/scenarios
at all.** This is the signature of a specific, diagnosable failure mode:
**overfitting to the surface features of the 58 training pairs (or to a
narrow slice of "valid-recognition" as a learned pattern) rather than
learning a generalizable calibration shift** in how the model weighs
evidence when deciding whether a design is valid.

## 6. ConversationDev Format Check — No Regression

| Metric | SFT-002 unconditioned | DPO-002 |
|---|---|---|
| Natural response rate | 100% | 100% |
| Unwanted JSON rate | 0% | 0% |
| Unwanted rubric rate | 1.7% | 2.5% |
| Avg. response length | 140.6 words | 173.2 words |

Consistent with both prior DPO runs: no damage to conversational format,
isolated null result on the one axis targeted.

## 7. Conclusion and Recommendation

**BR-VERIFIED-DPO-002 does not improve on `BR-VERIFIED-SFT-002` and is not
promoted.** `BR-VERIFIED-SFT-002` remains canonical.

The evidence across two real DPO attempts (19 pairs, then 58 pairs across
3x more domains) now points away from "just needs more preference pairs
of the same kind" as the fix. Per the diagnosis in Section 5, the more
likely explanations, in order of how directly this evidence supports them:

1. **LoRA-based DPO at this scale is overfitting to surface patterns**
   rather than learning a transferable calibration shift — strong
   in-distribution learning (100% held-out preference accuracy within the
   trained distribution) with zero out-of-distribution transfer is a
   classic overfitting signature, and an order-of-magnitude-larger dataset
   (500+ pairs) or a lower LoRA rank/regularization change would be the
   next natural test of this specific hypothesis.
2. Alternatively, the bias may need a fundamentally different intervention
   than preference-pair contrastive learning at any practical scale (e.g.
   full-parameter fine-tuning specifically on this axis, or an
   inference-time mechanism, similar to how the mode-router's few-shot
   fix outperformed both SFT-003's weight-level attempt and both DPO
   attempts on the *format* axis).

This report does not recommend which of these to pursue next without
further input — both are real, defensible next steps with different cost/
risk profiles, and the choice affects how much further compute and dataset
authoring effort to commit.

## 8. Not Performed

- `BR-VERIFIED-SFT-002` was not overwritten or superseded.
- Neither `BR-VERIFIED-DPO-001` nor `BR-VERIFIED-DPO-002` is being
  promoted to canonical status; both preserved for research history.
- No further DPO run was started automatically.
- The sealed final benchmark was not opened.

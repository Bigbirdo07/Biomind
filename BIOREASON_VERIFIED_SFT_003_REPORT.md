# BioReason Verified SFT-003 Report

**Status**: `VERIFIED_EXPERIMENTAL_SFT`. Real, physically verified adapter,
continued-trained from BR-VERIFIED-SFT-002. **DPO readiness verdict: NOT
READY — see Section 7.**

## 1. Lineage and Training Provenance

- Base model: `Qwen/Qwen2.5-14B-Instruct`
- **Parent: `BR-VERIFIED-SFT-002`** (continued SFT, not a fresh LoRA — per
  phase spec item 40, chosen to preserve SFT-002's learned behavior while
  applying a small calibrated repair). Lineage: base Qwen → SFT-002 →
  SFT-003.
- Dataset: `BioReasonTrain-Verified-SFT-v0.3` (467 episodes: 421 train / 46
  val — 427 carried forward from v0.2 unchanged, 40 new targeted additions).
  Template-collapse and contamination gates both pass; a contamination fix
  was required during construction (see `BIOREASON_VERIFIED_SFT_V3_DATASET_REPORT.md`
  Section 4 — an early draft accidentally trained on the exact sentence used
  in the SFT-002 acceptance test, which would have made any improvement on
  that case circular; it was replaced with a distinct but structurally
  analogous scenario before freezing).
- LoRA: inherited from the resumed SFT-002 adapter, **r=16, alpha=32**
  (independently confirmed by reading `adapter_config.json` on Unity — the
  auto-generated `trainable_parameters.json` initially mislabeled this as
  r=32/alpha=64 due to a manifest bug that was found and fixed this session;
  the actual trained weights were correct throughout, only the label was
  wrong)
- Learning rate: `1.5e-5` (lower than SFT-002's `2e-5`)
- Epochs: 1.5 (fewer than SFT-002's 2.0)
- Trainable parameters: `68,812,800 / 14,838,846,464` (`0.464%`, same as
  SFT-002 since rank is inherited)
- Slurm job: **`64525515`** (`br_verified_sft_003`), `COMPLETED`, exit
  `0:0`, duration 424.4s
- `train_loss: 1.605`, `eval_loss: 1.556` (epoch 1.53)

## 2. Physical Adapter Evidence

- Adapter: `outputs/verified_training/BR-VERIFIED-SFT-003/final_adapter/adapter_model.safetensors`
- Size: `275,341,720` bytes (matches SFT-002's size exactly, consistent
  with the same LoRA rank)
- SHA-256: `a00b895e44f73589b090a42a7e66ecfe1d71c4864253ad0eac59f9efa8c5de46`
  — independently recomputed via `ssh unity sha256sum`, matches manifest
- Durable archive:
  `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-003`
- Reload verified via `PeftModel.from_pretrained` + `merge_and_unload`,
  used for all evaluations below

## 3. Dev / Regression Results — 4-Way Comparison

| Metric | Base Qwen | SFT-001 | SFT-002 | **SFT-003** |
|---|---|---|---|---|
| Dev correctness proxy | 0.40 | 0.40 | 0.40 | **0.40** |
| Regression correctness proxy | 0.37 | 0.31 | 0.38 | **0.34** |
| Regression flaw-detection-keyword rate | 0.139 | 0.042 | 0.139 | **0.083** |
| Regression correction-keyword rate | 0.02 | 0.00 | 0.03 | **0.03** |

**This is a real, measurable regression relative to SFT-002** on the two
metrics that matter most: Regression correctness dropped 4 points
(0.38 → 0.34) and flaw-detection-keyword rate dropped by 40% relative
(0.139 → 0.083). Both cross the explicit regression guardrails set out
before this run (phase spec item 58: "SFT-003 should NOT be accepted if
Regression correctness falls meaningfully / flaw detection degrades").
Dev stayed flat at 0.40 across all four models — not informative here.

## 4. ConversationDev-v0.1 Results — 4-Way Comparison

| Metric | Base Qwen | SFT-001 | SFT-002 | **SFT-003** |
|---|---|---|---|---|
| Natural response rate | 100% | 11.7% | 100% | **97.5%** |
| Unwanted JSON rate | 0% | 81.7% | 0% | **0%** |
| Unwanted rubric-language rate | 2.5% | 81.7% | 1.7% | **3.3%** |
| Explicit audit compliance rate (n=8) | not measured | not measured | **0%** | **37.5%** |
| Avg. response length (words) | 173.2 | 50.5 | 140.6 | **46.7** |

Explicit audit compliance genuinely improved (0% → 37.5% on the 8
ConversationDev audit turns; 27.3% on a separate, freshly-authored 11-item
audit acceptance set, up from SFT-002's 0/8). This is the one dimension
SFT-003 was specifically built to repair, and it did move in the right
direction, though "substantially improved" (item 59's target) is a stretch
for a jump to ~30%.

**However, average response length collapsed to roughly a third of SFT-002's**
(140.6 → 46.7 words) across the same 120-turn set. Spot-checking confirms
this isn't just terser phrasing — see Section 6.

## 5. Audit-Mode Behavior (Detailed)

Spot-checking the new 11-prompt audit acceptance set: responses are now a
mix of raw JSON (e.g. `AUD_000`, `AUD_004`) and unstructured single-paragraph
prose with no headings at all (e.g. `AUD_001`, `AUD_002`, `AUD_003`) — the
model did **not** reliably converge on the "readable structured prose with
headings" behavior the v0.3 training data was specifically designed to
teach (10 of the 12 new audit episodes used that format; the model still
defaults to either raw JSON or plain prose). Content quality on the prose
responses remains genuinely mechanism-specific and correct (e.g. *"This
pipeline leaks information from the test set into the training set. SMOTE
should be applied only to the training data after the train/test split"*),
just not structurally distinguishable from a SCIENTIFIC_REASONING-mode
answer.

## 6. Live Acceptance Test — Primary-Mechanism Case Got WORSE, Not Better

This is the most important negative finding. `outputs/verified_training/BR-VERIFIED-SFT-003/acceptance/conversation_predictions.jsonl`,
item `ACC_005` (the exact acceptance case used for both SFT-002 and
SFT-003, unchanged):

> *"I have 12 patients measured monthly for six months and randomly put
> visits into train and test."*

| Model | Response |
|---|---|
| SFT-002 | *"...randomly splitting the data into training and test sets can be problematic for time series data because it doesn't respect the temporal order... This can lead to data leakage... Instead, you should use a time-based split..."* |
| **SFT-003** | *"That's a small sample size for time series, and random splitting can break temporal order. Consider a time-based split instead, like training on early months and testing on later ones."* |

SFT-003's answer is **shorter, less specific, and does not mention data
leakage, patient dependency, or subject-level structure at all** — it
regressed to a purely temporal framing, dropping even the partial
leakage-mechanism language SFT-002 had. This is the exact case the v0.3
dataset's 3 new primary-vs-secondary mechanism examples were meant to fix
(Section 2 of `BIOREASON_VERIFIED_SFT_V3_DATASET_REPORT.md`), and it did
not work — if anything, the targeted repair failed and general answer
quality/specificity on this case declined.

Other acceptance cases held up:
- **Valid hard negative** (`ACC_006`): still correctly recognized as valid,
  no invented flaw — matches SFT-002. **Passes.**
- **Debugging with path context** (`ACC_007`): correctly referenced the
  exact prior path when explaining `FileNotFoundError`. **Passes.**
- General chat, capability, teaching, pipeline-build turns: still natural,
  no JSON, retained pipeline context — consistent with SFT-002.

## 7. DPO Readiness Verdict

Per the explicit regression guardrails set before this run (item 58) and
the instruction not to protect BioReason from unfavorable results:

**Verdict: `SFT_003_SCIENTIFIC_REGRESSION`**

SFT-003 achieved a real, partial improvement on explicit audit-mode
activation (0% → ~30%) — the dimension it targeted — but at the cost of a
genuine regression on both quantitative scientific metrics (Regression
correctness and flaw-detection-keyword rate both fell relative to SFT-002)
and, more concerningly, on the *specific* primary-mechanism acceptance case
it was built to fix, where its answer became less specific rather than more.
Average response length collapsing to ~1/3 of SFT-002's across
ConversationDev is consistent with a broader "say less, more generic"
shift that likely explains both the audit-format gain (shorter answers are
more likely to default to a compact JSON/label pattern) and the scientific
regression (shorter answers have less room for mechanism-specific
reasoning).

**Do not promote SFT-003 over SFT-002.** `BR-VERIFIED-SFT-002` remains the
better-performing checkpoint on the scientific axis and is not superseded.
Both adapters are preserved, distinct, hash-verified.

## 8. Likely Cause (Assessed, Not Certain)

The most plausible explanation is that continued SFT from an
already-conservative checkpoint, even at a lower LR and fewer epochs,
still shifted the model's general answer style (toward brevity/genericness)
more than it taught the intended narrow calibration — the 3 primary-
mechanism examples and 10 diverse audit examples were too small a signal
relative to the disruption from a second training pass on top of the first.
This is consistent with, though not proof of, an accumulating-drift risk in
chained continued-SFT that wasn't fully mitigated by the conservative
hyperparameters chosen.

## 9. Not Performed (Per Governance)

- No DPO was run.
- `BioReasonBench-v0.2-Final` (sealed) was not opened.
- Human evaluation remains paused.
- Neither `BR-VERIFIED-SFT-001` nor `BR-VERIFIED-SFT-002` was overwritten;
  all three adapters exist independently with distinct, verified hashes.
- No SFT-004 was started — stopping here per the phase's stop condition to
  report findings and let this regression be reviewed before any further
  training.

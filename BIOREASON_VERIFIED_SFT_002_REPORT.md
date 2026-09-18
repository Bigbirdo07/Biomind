# BioReason Verified SFT-002 Report

**Status**: `VERIFIED_EXPERIMENTAL_SFT`. Real, physically verified LoRA
adapter, trained on the corrected `BioReasonTrain-Verified-SFT-v0.2` dataset
with assistant-only label masking. **DPO readiness verdict: see Section 8 —
not an unqualified yes.**

## 1. Training Provenance

- Base model: `Qwen/Qwen2.5-14B-Instruct`
  (`/scratch4/.../models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`)
- Dataset: `BioReasonTrain-Verified-SFT-v0.2` (427 episodes: 385 train / 42
  val), `messages` format, contamination-checked clean against Dev/
  Regression/ConversationDev (see `BIOREASON_VERIFIED_SFT_V2_DATASET_REPORT.md`)
- Training format: `messages` with **assistant-only label masking**
  (new — SFT-001 masked nothing; verified against the real Qwen tokenizer:
  system/user tokens `-100`, ~30-45% of tokens trainable per example)
- LoRA config: `r=16, alpha=32` (**conservative**: half of SFT-001's `r=32,
  alpha=64`, to reduce risk of overwriting Qwen's general conversational
  ability)
- Learning rate: `2e-5` (**conservative**: 2.5x lower than SFT-001's `5e-5`)
- Epochs: 2.0
- Trainable parameters: `68,812,800 / 14,838,846,464` (`0.464%` — down from
  SFT-001's `0.923%`, consistent with the halved LoRA rank)
- Slurm job: **`64522968`** (`br_verified_sft_002`), `COMPLETED`, exit
  `0:0`, duration 231.0s, node on Unity `uri-gpu` partition
- `train_loss: 2.457`, `eval_loss: 2.272` (epoch 2.0) — **not directly
  comparable to SFT-001's `train_loss: 0.625`**: SFT-001's loss was computed
  over the *entire* sequence including the fixed prompt template (easy to
  fit, inflated the loss downward), while SFT-002's loss is computed only
  over assistant tokens on a much more diverse target distribution (harder
  to fit uniformly, as expected and desired).

## 2. Physical Adapter Evidence

- Adapter path (durable archive):
  `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-002`
- File: `outputs/verified_training/BR-VERIFIED-SFT-002/final_adapter/adapter_model.safetensors`
- Size: `275,341,720` bytes (non-zero)
- SHA-256: `018e5f34ddf9bec820fb545a4ab2d54f837c035f59046e192455a3b5562318f2`
  — independently recomputed via `ssh unity sha256sum`, matches
  `checkpoint_integrity.json` exactly
- Reload verification: loads via `PeftModel.from_pretrained` + `merge_and_unload`,
  used for all evaluation runs below
- Response provenance on every recorded generation: `MODEL_GENERATED`

## 3. Dev / Regression Results — 3-Way Comparison

Slurm job `64523330` (`br_sft002_eval`), `COMPLETED`, exit `0:0`, same
`BioReasonDev-v0.2` / `BioReasonRegression-v0.1` sets as base Qwen and
SFT-001.

| Metric | Base Qwen | SFT-001 | **SFT-002** |
|---|---|---|---|
| Dev correctness proxy (n=100) | 0.40 | 0.40 | **0.40** |
| Regression correctness proxy (n=100) | 0.37 | 0.31 | **0.38** |
| Regression flaw-detection-keyword rate | 0.139 | 0.042 | **0.139** |
| Regression correction-keyword rate | 0.02 | 0.00 | **0.03** |

**SFT-002 fully recovers SFT-001's scientific regression** — Regression
correctness proxy and flaw-detection-keyword rate are statistically
indistinguishable from (in fact marginally better than) base Qwen. Spot
check of Dev item 0 confirms mechanism-specific reasoning, not generic
labels: *"the random splitting of scans into folds disregards the temporal
and patient-specific dependencies inherent in longitudinal data... each
patient's scans are not independent observations"* — this is the kind of
scenario-specific mechanism explanation that was completely absent from
SFT-001's outputs.

## 4. ConversationDev-v0.1 Results — 3-Way Comparison

Slurm job `64523331` (`br_convdev_sft002`), `COMPLETED`, exit `0:0`, full
120-turn set, real multi-turn replay using SFT-002's own prior generations
as context.

| Metric | Base Qwen | SFT-001 | **SFT-002** |
|---|---|---|---|
| Natural response rate | 100% | 11.7% | **100%** |
| Unwanted JSON rate | 0% | 81.7% | **0%** |
| Unwanted rubric-language rate | 2.5% | 81.7% | **1.7%** |
| Stock-phrase rate | 0% | 88.3% | **0%** |
| Avg. response length (words) | 173.2 | 50.5 | 140.6 |

Per-mode unwanted-JSON rate, SFT-002: **0/120 across every mode**,
including the modes that were 100% collapsed in SFT-001 (teaching 0/39,
scientific reasoning 0/16, pipeline 0/17, debugging 0/4, code explanation
0/8, short follow-ups 0/8, insufficient-information 0/6).

**SFT-002 conversational behavior is statistically indistinguishable from
base Qwen on these metrics** — the catastrophic format/content collapse
from SFT-001 is resolved.

## 5. Known Weakness: Audit-Format Conditionality Overcorrected

Inspecting the 8 `SCIENTIFIC_AUDIT` turns in ConversationDev (explicit
requests like *"Audit this experimental design..."*), SFT-002 answered
**all 8 in natural prose, none in structured JSON** — e.g.:

> *"This experimental design has a significant flaw: batch effects are
> confounded with the group of interest (tumor vs. normal). This
> confounding can lead to false positives or false negatives..."*

The content is scientifically correct and mechanism-specific (this example
correctly identifies batch/group confounding), but the model no longer
reliably switches to structured output even when the user explicitly asks
for a formal audit. SFT-001 over-triggered JSON on everything (100%);
SFT-002 has swung to under-triggering it even when appropriate (0/8 on
audit requests) — likely because the v2 dataset's audit slice is only 120/427
(28%) episodes split across 3 rotating JSON schemas, combined with the
conservative LoRA rank/learning rate, which was not enough to reliably teach
the *conditional* "structured format when requested" behavior. This is a
real, unresolved gap — see Section 8.

## 6. Live Acceptance Conversation (Item 68) — Real Inference

Slurm job `64523332` (`br_sft002_accept`), `COMPLETED`, exit `0:0`. Full
transcript: `outputs/verified_training/BR-VERIFIED-SFT-002/acceptance/conversation_predictions.jsonl`.

- `hello` → natural greeting. `what can you do?` → natural capability
  description. `what is PCA?` → natural teaching. `How does PC1 relate back
  to my genes?` → contextual loadings explanation. **All as expected.**
- New pipeline conversation (*"Build me an RNA-seq differential expression
  pipeline with PCA"*): asked for experimental design, sample count,
  sequencing depth, reference genome — **did not invent sample counts**.
  Correctly retained `18 tumor / 17 normal` and `sequencing_batch` across
  subsequent turns. Retained the exact path
  `/scratch/project/cancer/counts.csv` when asked for code (used it
  verbatim in the generated R script, did not invent a path). Explained why
  PCA was used, explained PC1 loadings, updated the pipeline when asked to
  change to 50 PCs, and explained the specific change made
  (`ntop` parameter in `plotPCA`, a real DESeq2 parameter — not a
  hallucinated explanation). **All as expected.**

## 7. Scientific and Hard-Negative Acceptance Cases (Items 69-71)

- **Item 69 (longitudinal leakage)**: *"12 patients measured monthly for six
  months, randomly put visits into train and test."* SFT-002 correctly
  identified this as a leakage problem and explained a real mechanism
  (temporal ordering: *"randomly splitting... doesn't respect the temporal
  order... can lead to data leakage"*) and recommended a time-based split.
  **Partial match to the intended answer**: the expected mechanism was
  specifically *patient-level* dependency (visits from the same patient
  crossing partitions, recommend patient-level grouped splitting); SFT-002
  named a real, defensible leakage mechanism (temporal) but not the
  specific patient/subject-level framing the acceptance case was designed
  to test. Not a generic "data leakage" label — genuinely mechanism-specific
  — but not the exact intended mechanism either.
- **Item 70 (valid hard negative)**: *"split all repeated patient
  measurements at the patient level, fit feature selection only on training
  folds, evaluate on untouched patients."* SFT-002 correctly recognized
  this as valid and did **not** invent a flaw: *"That's a good approach to
  avoid data leakage... Splitting the data at the patient level is a common
  practice... to prevent information from one patient's measurements from
  influencing the model's performance on another patient's data."*
  **Passes.**
- **Item 71 (debugging with path context)**: given prior context
  establishing `/scratch/project/cancer/counts.csv`, then `FileNotFoundError`,
  SFT-002 correctly referenced the exact path from the earlier turn rather
  than giving a generic answer. **Passes.**

## 8. DPO Readiness Verdict

Per the governance requirement that DPO readiness needs **both** scientific
quality **and** conversational quality (strong performance on only one is
insufficient):

- **Scientific quality**: no regression vs. base Qwen (Regression
  correctness and flaw-detection fully recovered from SFT-001's collapse,
  marginally exceeding base Qwen). **Meets the bar.**
- **Conversational quality**: Natural Response Rate, Unwanted JSON Rate,
  Unwanted Rubric Rate, Context Retention, and Pipeline State Retention are
  all at or near base-Qwen parity — a dramatic improvement over SFT-001.
  **However, Appropriate Mode Rate is not yet met**: the model no longer
  reliably produces structured output when a user explicitly requests a
  formal audit (Section 5), and the one scientific acceptance case with a
  specific intended mechanism (Section 7, item 69) was only partially
  matched.

**Verdict: `SFT_002_NEEDS_MORE_SFT_REPAIR`**

This is a **much narrower** repair than SFT-001's: the catastrophic,
unconditional format/content collapse is resolved, and scientific
correctness is fully recovered. The residual gap is specifically
under-representation of the "produce structured output when explicitly
requested" behavior (too few audit examples, or too conservative a LoRA
rank/LR to learn a conditional switch reliably) and some scenario-specific
mechanism precision on harder multi-factor cases (patient-level vs.
temporal leakage). Per the dataset report's own limitations section, the
v2 dataset also under-represents pipeline/debugging/multi-turn relative to
the mix plan's targets, which should be scaled up alongside the audit slice
in the next iteration. DPO remains **not authorized** on SFT-002 pending
this repair.

## 9. Not Performed (Per Governance)

- No DPO was run or attempted.
- `BioReasonBench-v0.2-Final` (sealed) was not opened.
- Human evaluation remains paused.
- `BR-VERIFIED-SFT-001` was not overwritten; both adapters exist
  independently with distinct hashes.

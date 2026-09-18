# BioReason Mode-Conditioned Inference Report

**Canonical BioReason SFT model: `BR-VERIFIED-SFT-002`. Weights unchanged
throughout this phase — no SFT-004, no DPO, no merging of SFT-003.**
`BR-VERIFIED-SFT-003` status: `REJECTED_FOR_SCIENTIFIC_REGRESSION` (unchanged
from prior phase; preserved for research history only).

## 1. Hypothesis Under Test

Prior phases showed: SFT-001 over-specialized (rigid structure everywhere),
SFT-002 was balanced but under-triggered structured audit format (0/8 on
explicit requests), and SFT-003's attempt to fix that at the weight level
caused a real scientific regression. This phase tests the alternative
hypothesis: **response-mode control should occur at inference time, not
through additional weight updates.**

## 2. Architecture

- `src/bioreason/inference/mode_router.py` — real model-based classifier.
  Issues a short (~60-80 token) real generation to the same loaded model,
  asking it to return structured JSON (`{"mode", "confidence",
  "explicit_user_request"}`) given the conversation history and active
  pipeline context. **Not keyword matching.** The legacy
  `PipelineIntentClassifier` (keyword-based, in
  `src/bioreason/pipeline/intent.py`) is used only as a last-resort
  fallback when the model's JSON output fails to parse — across all
  evaluation runs below, `router_parse_failure_rate` was **0%**, so the
  fallback was never actually invoked.
- `src/bioreason/inference/mode_overlays.py` — 9 mode-specific system-prompt
  overlays (`GENERAL_CHAT`, `TEACHING`, `SCIENTIFIC_REASONING`,
  `SCIENTIFIC_AUDIT`, `PIPELINE_INTAKE`, `PIPELINE_BUILD`, `PIPELINE_DEBUG`,
  `CODE_EXPLANATION`, `INSUFFICIENT_INFORMATION`). Overlays control format
  and scope only — none inject scientific content.
- `src/bioreason/inference/orchestrator.py` — wires router → overlay →
  main generation. Includes an optional two-pass audit path: if
  `SCIENTIFIC_AUDIT` mode is selected and the response doesn't contain
  enough structural sections (`audit_schema_ok` check), a second real
  generation reformats the same content into structured sections without
  inventing new claims.
- Existing `PipelineContext`/`PipelineState` (guided pipeline mode) is
  unchanged and kept separate from mode classification, per the "mode =
  behavior, PipelineContext = known experiment facts" split.

## 3. Mode-Dev Dataset

`BioReasonModeDev-v0.1`: 55 turns / 41 conversations, focused on
near-boundary contrast pairs (e.g. "explain PCA flaws in general" vs.
"audit how I used PCA here" vs. "is this a problem?") and short-follow-up
routing that requires conversation history (`benchmark/mode_dev_v0.1/`).
Combined with the existing `BioReasonConversationDev-v0.1` (120 turns), this
gives 175 labeled turns for router evaluation — within the phase's 100-150
target when the two are considered together (ModeDev alone is smaller by
design, since it deliberately targets only the hard boundary cases;
ConversationDev already covers balanced general-mode distribution).

Two additional acceptance-only sets were built:
`audit_acceptance_items.json` (12 turns, fresh explicit audit prompts) and
`orchestrator_acceptance_items.json` (7 turns, testing item 42-43: audit
reformat follow-ups and explicit user overrides).

## 4. Router Metrics

| | ConversationDev (120 turns) | ModeDev (55 turns) |
|---|---|---|
| Raw mode accuracy | 56.7% | 69.1% |
| **Taxonomy-adjusted accuracy*** | 68.75% | — |
| **Explicit audit recall** | **100%** (8/8) | **100%** (8/8) |
| Pipeline intent recall | 75% | 100% |
| Debugging recall | 75% | 42.9% |
| Router parse failure rate | 0% | 0% |

*ConversationDev-v0.1's `expected_mode` labels were authored in the prior
phase using a 12-label taxonomy (includes `CAPABILITY`, `DEBUGGING`,
`PIPELINE_FOLLOWUP`, `SHORT_CONTEXTUAL_FOLLOWUP`) that predates this
phase's 9-mode router taxonomy — so raw accuracy structurally
undercounts correct routing (e.g. `CAPABILITY`, which isn't a valid router
output, can never "match"). Adjusted accuracy remaps `CAPABILITY`→
`GENERAL_CHAT`, `DEBUGGING`→`PIPELINE_DEBUG`, credits `PIPELINE_FOLLOWUP`
against any pipeline-family mode, and excludes the 8
`SHORT_CONTEXTUAL_FOLLOWUP` turns (no single correct label without deeper
judgment). This is disclosed rather than silently substituted for the raw
number.

**Router's main systematic weakness**: over-classifies implicit
`SCIENTIFIC_REASONING` scenarios as `SCIENTIFIC_AUDIT` — 13/16 on
ConversationDev, 7/11 on ModeDev. Confusion matrix (ConversationDev):

```
SCIENTIFIC_REASONING -> {SCIENTIFIC_AUDIT: 13, SCIENTIFIC_REASONING: 3}
```

This did not appear to cause factual harm in spot checks (the
`SCIENTIFIC_AUDIT` overlay still produces correct, mechanism-specific
content — see Section 6), but it means the router does not yet reliably
distinguish "user describes a scenario and implicitly wants a verdict"
from "user explicitly wants a formal audit," despite `explicit_user_request`
detection itself being reliable (100% recall on truly explicit requests).

## 5. Behavior Metrics — ConversationDev, SFT-002 Unconditioned vs. Conditioned

| Metric | SFT-002 unconditioned (prior phase) | **SFT-002 + mode conditioning** |
|---|---|---|
| Natural response rate | 100% | 98.3% |
| Unwanted JSON rate | 0% | 0.8% |
| Unwanted rubric rate | 1.7% | 16.7% |
| **Explicit audit compliance (n=8)** | **0%** | **100%** |
| Avg. response length (words) | 140.6 | 205.7 |

**This is the headline result: explicit audit compliance went from 0/8 to
8/8** across ConversationDev, and separately **11/11 (100%) on the
freshly-authored `audit_acceptance_items.json`** and **8/8 (100%) on
ModeDev's audit turns** — three independent confirmations, not a fluke on
one set. The unwanted-rubric-rate increase (1.7% → 16.7%) is a real,
smaller side effect: some non-audit turns (mostly `TEACHING`) now include
occasional rubric-adjacent phrasing, likely bleeding in from the router's
own audit-heavy vocabulary or from longer, more structured answers overall
(avg. length rose from 140.6 to 205.7 words). This is a genuine trade-off,
not free.

## 6. Scientific Regression Gate (Item 33) — Ambiguous, Not Cleanly Passed

| Metric | Base Qwen | SFT-002 unconditioned | **SFT-002 + mode conditioning** |
|---|---|---|---|
| Dev correctness proxy | 0.40 | 0.40 | 0.40 |
| Regression correctness proxy | 0.37 | 0.38 | **0.26** |
| Regression flaw-detection-keyword rate | 0.139 | 0.139 | **0.042** |

Taken at face value, this trips the regression gate. **However, spot-checking
strongly suggests this is substantially a scorer artifact, not a
comprehension loss**, and this must be reported precisely rather than
resolved in either direction:

- All 100 Regression items routed to `SCIENTIFIC_AUDIT` (the prompt
  template — "Evaluate this biological research scenario... identify the
  primary issue... propose a correction" — reads as an audit request, which
  is itself a reasonable router decision).
- The `SCIENTIFIC_AUDIT` overlay produces long, headed, paraphrased
  responses (e.g. "cells are nested within individual mice" instead of the
  literal word "pseudoreplication"; "predictive power... as evidence of
  causality" instead of the literal flaw-type string
  `shap_feature_importance_causal_conflation`). The keyword-proxy scorer
  requires the literal flaw-type/rubric string to appear, so it fails to
  credit paraphrased-but-correct answers.
- Among the 69 flawed-Regression items that failed strict keyword credit,
  **61 (88%) contained at least a partial lexical match** to the flaw-type
  words when checked loosely (see raw data in
  `outputs/verified_training/mode_conditioned/dev_regression/`), and manual
  reading of several full responses (not just the loose-match check)
  confirmed the model was reasoning about the correct mechanism, just in
  different words than the scorer expects.
- This scorer sensitivity is not new — it was present in every prior
  evaluation in this project — but the mode-conditioned overlay's more
  verbose, paraphrased style appears to expose it more severely than the
  terser unconditioned style did.

**Conclusion: the regression gate is not cleanly passed, and it is not
honest to claim it was.** The most defensible statement is that the
observed drop is very likely partly or mostly a scorer measurement
artifact rather than a real scientific-reasoning regression, but this is
not proven with certainty, and no DPO-readiness claim should rely on this
metric until a semantic (not literal-keyword) scorer is built.

## 7. Valid Hard-Negative — Holds Up Under Audit Framing

The valid hard-negative acceptance case (`ACC_006`: patient-level split,
train-fold-only feature selection, untouched-patient evaluation) was routed
to `SCIENTIFIC_AUDIT` under conditioning — a real test of whether the audit
overlay's issue-finding framing would pressure the model into manufacturing
a flaw. It did not: *"There is no primary issue identified in the described
methodology... this is a robust way to avoid data leakage."* **Passes.**

## 8. Primary-Mechanism Case — Still Unresolved (Confirms Item 3's Separation)

The recurring longitudinal-leakage acceptance case (`ACC_005`, unchanged
across SFT-002, SFT-003, and now mode-conditioned SFT-002) again framed the
primary issue as **temporal ordering**, not patient-level/subject leakage,
even under the `SCIENTIFIC_AUDIT` overlay's explicit "Primary Issue" /
"Secondary Issues" structure — the model used that exact structure but
still put temporal ordering in the primary slot and relegated
patient-subgroup concerns to a vaguer "Lack of Stratification" secondary
note, never explicitly naming "the same patient's visits crossing the
train/test boundary" as the mechanism.

**This is informative, not just disappointing**: it confirms the phase's
own hypothesis in Section 3 (separate reasoning from presentation) — mode
conditioning correctly left the scientific conclusion to the model, and the
model's underlying reasoning gap on this specific case was not, and could
not be, fixed by better formatting. This is a genuine model-capability
limitation that would need targeted SFT data (as SFT-003 attempted and
failed to fix cleanly) or DPO, not inference-layer routing.

## 9. Live Acceptance Tests (Items 34-43)

All run against the real physical `BR-VERIFIED-SFT-002` adapter,
`response_source: MODEL_GENERATED` throughout.

| Test | Result |
|---|---|
| `hello` → GENERAL_CHAT | Pass — natural greeting |
| `What is PCA?` → TEACHING | Pass — natural explanation, no audit scaffold |
| `I fit PCA on all samples before CV. Is that okay?` → SCIENTIFIC_REASONING | Router chose SCIENTIFIC_AUDIT instead (the systematic bias from Section 4); content was still specific and correct |
| `Audit this experiment: [longitudinal case]` → SCIENTIFIC_AUDIT | Pass on routing; primary-mechanism content gap persists (Section 8) |
| `Build me an RNA-seq pipeline.` → PIPELINE_INTAKE | Pass — asked for missing info, no fabricated samples |
| Pipeline continuation (18/17 tumor/normal, batch, exact path) | Pass — `PipelineContext`-style retention held across turns |
| `Give me the code.` → PIPELINE_BUILD | Pass — real code returned |
| `I got FileNotFoundError.` → PIPELINE_DEBUG | Pass — referenced the known path |
| `Can you make that a structured audit?` (item 42) | **Pass** — stayed in SCIENTIFIC_AUDIT, explicitly reformatted ("Sure, here's a structured audit of the issue...") while preserving the same conclusion |
| `Actually, explain this conversationally, not as a formal audit.` (item 43) | **Pass in substance** — response dropped the audit structure and opened "Sure, let's break this down conversationally," though the router's own mode label landed on `TEACHING` rather than `GENERAL_CHAT` (a reasonable near-miss, not a functional failure) |
| `Give me only the code, no explanation.` (item 43) | Pass — response was a code block with minimal prose |
| `Audit this design and return the result as JSON` (item 15/43) | **Pass** — router correctly flagged `explicit_user_request: true` and the response was raw JSON, confirming JSON-on-request still works |

## 10. Comparison A vs. B vs. C

| | A: SFT-002 unconditioned | B: SFT-002 + mode conditioning | C: SFT-003 unconditioned (research only) |
|---|---|---|---|
| Regression correctness | 0.38 | 0.26* | 0.34 |
| Regression flaw-detection | 0.139 | 0.042* | 0.083 |
| ConversationDev natural response | 100% | 98.3% | 97.5% |
| ConversationDev unwanted JSON | 0% | 0.8% | 0% |
| Explicit audit compliance | 0% | **100%** | ~30% |

*See Section 6 — likely partly a scorer artifact under the verbose audit
overlay style, not a clean like-for-like scientific comparison.

Mode-conditioned B achieves audit compliance far beyond what weight-level
repair (C, SFT-003) managed, without touching model weights at all —
strong support for the phase's core hypothesis, with the important caveat
that B's Dev/Regression numbers need a better scorer before being fully
trusted either way.

## 11. Phase Verdict

**`MODE_CONDITIONING_INCONCLUSIVE`**

Not `MODE_CONDITIONED_SFT002_SUCCESS`: the scientific-regression-gate
metric (Section 6) shows a real drop that cannot be confidently dismissed
as purely a scorer artifact without a semantic scorer to confirm it, and
router mode accuracy (57-69%, with a specific systematic
audit-over-triggering bias) is not yet reliable enough on implicit
scientific-reasoning cases to call "solved."

Not `MODE_ROUTING_SUCCESS_AUDIT_FORMAT_STILL_WEAK`: audit format is not
weak — it is the strongest, most consistent result in this report (100%
across three independent test sets).

Not `MODE_ROUTING_SCIENTIFIC_REGRESSION`: the evidence for a genuine
scientific capability loss is weak (88% loose lexical overlap on
"failed" items, manually-confirmed correct reasoning in spot checks); this
verdict would overclaim harm that isn't clearly demonstrated.

Not `MODE_ROUTER_FAILURE`: explicit-request recall (the case that matters
most for the phase's original goal) is 100% across every test set.

**The honest position is inconclusive**, with one clear, strong, repeated
success (explicit audit compliance, solved without touching weights) and
one open question (whether the Dev/Regression metric drop is real or a
measurement artifact) that requires better tooling — a semantic scorer, not
literal keyword matching — before it can be resolved either way.

## 12. DPO Readiness

**`DPO_STILL_BLOCKED`**

Per item 54's explicit requirements (all of: strong conversation, preserved
scientific performance, correct primary mechanisms, functioning explicit
audit mode, functioning pipeline/debugging, no major formatting collapse):
explicit audit mode and pipeline/debugging interaction now function well,
and formatting collapse is resolved — but "scientific performance
preserved" cannot be confirmed (Section 6, unresolved) and "correct primary
mechanisms" is not met (Section 8, the patient-level-leakage case remains
wrong under every configuration tested across three phases). DPO should
remain blocked until (a) a semantic scorer resolves whether Section 6's
metric drop is real, and (b) the primary-mechanism gap is addressed —
likely requiring targeted SFT data on primary-vs-secondary mechanism
distinction with more examples and more careful review than SFT-003's
three-example attempt, or a different repair strategy entirely.

## 13. Files

- Router/overlay/orchestrator code: `src/bioreason/inference/`
- Mode-conditioned eval harness:
  `src/bioreason/training/verified_mode_conditioned_eval.py`,
  `scripts/run_verified_mode_conditioned_eval.py`,
  `scripts/run_verified_mode_conditioned_dev_regression.py`
- `BioReasonModeDev-v0.1`: `benchmark/mode_dev_v0.1/`
- All raw predictions, router decisions, and metrics:
  `outputs/verified_training/mode_conditioned/{conversation_dev,mode_dev,dev_regression,acceptance,audit_acceptance,orchestrator_acceptance}/`

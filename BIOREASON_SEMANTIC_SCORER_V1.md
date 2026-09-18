# BioReason Semantic Scorer v1 — Corrected Scientific Evaluation

**Status**: Phase 0 of `kind-questing-seal` roadmap. Re-scores every
existing Dev/Regression prediction file (no new model generations) with a
real LLM-judge instead of literal keyword matching. Surfaced a major,
previously-invisible finding (Section 4) that is more important than the
scorer-accuracy fix itself.

## 1. Why the Keyword Scorer Had to Go

`score_prediction()` in `verified_eval.py` required the literal
`flaw_type` string or rubric `key_points` to appear verbatim in a
response. Spot-checks in the mode-conditioning phase found this penalized
correct, paraphrased answers (e.g. "cells are nested within individual
mice" not crediting `pseudoreplication`) and — as this phase found —
also failed to catch the opposite problem: verbose hedging responses that
technically contain the word "valid" while still inventing a nitpick.

## 2. The Judge Itself Needed a Fix First (v1 → v2)

A first single-step judge (given the response and the reference answer in
the same prompt) was spot-checked per the roadmap's own verification step
and found broken: it scored **SFT-001 at 100%** on Dev — the model with
the most severe known content collapse. Reading the raw judgments showed
why: the judge's justifications cited specific mechanism details (e.g.
"correlated scans from the same patients") that existed only in the
*reference* material it was given, not in the model's actual response
(which said only `"identified_issues": ["data_leakage"]`). The judge was
leaking the answer key into its own justification.

**Fix**: split into two model calls per item.
1. **Extract** (blind to the reference): summarize what the response
   itself claims, and explicitly flag if it's a generic category label
   with no specific mechanism.
2. **Compare**: judge the *extracted summary* (not the raw response)
   against the reference. A generic-label-only extraction is scored
   incorrect even if the category happens to be right.

This is implemented in `src/bioreason/training/semantic_judge.py` and
`scripts/run_semantic_rescore.py`. Under v2, SFT-001's Dev score dropped
to a believable 90% overall (see Section 4 for why even that isn't the
full picture), and spot-checking individual items confirmed the fix:
generic answers now correctly fail, specific ones correctly pass.

## 3. Corrected Overall Correctness (All 10 Existing Prediction Sets)

| Model / Dataset | Semantic (v2) | Original keyword |
|---|---|---|
| Base Qwen / Dev | 61.0% | 40.0% |
| Base Qwen / Regression | 49.0% | 37.0% |
| SFT-001 / Dev | 90.0% | 40.0% |
| SFT-001 / Regression | 54.0% | 31.0% |
| SFT-002 / Dev | 61.0% | 40.0% |
| SFT-002 / Regression | 52.0% | 38.0% |
| SFT-003 / Dev | 60.0% | 40.0% |
| SFT-003 / Regression | 48.0% | 34.0% |
| SFT-002 mode-conditioned / Dev | 60.0% | 40.0% |
| SFT-002 mode-conditioned / Regression | 49.0% | 26.0% |

Overall semantic scores are higher than keyword scores across the board
(expected — the keyword scorer was too strict), and the mode-conditioned
Regression gap (49% vs. base Qwen and SFT-002's ~49-52%) that looked like
a real regression under the keyword scorer (26% vs. 37-38%) **mostly
closes** under the semantic scorer — consistent with the mode-conditioning
report's suspicion that the earlier drop was substantially a scorer
artifact from the verbose audit-overlay style, not a real comprehension
loss.

## 4. The Real Finding: Valid-Recognition vs. Flaw-Detection Asymmetry

Overall correctness hides the actual story. Breaking Dev and Regression
into their `valid` (no flaw present) and `flawed` (flaw present) subsets:

| Model | Dev valid-recognition | Dev flaw-detection | Regression valid-recognition | Regression flaw-detection |
|---|---|---|---|---|
| Base Qwen | **2.5%** (1/40) | 100.0% | **0.0%** (0/28) | 68.1% |
| SFT-001 | **100.0%** (40/40) | 83.3% | **100.0%** (28/28) | 36.1% |
| SFT-002 | **2.5%** (1/40) | 100.0% | **0.0%** (0/28) | 72.2% |
| SFT-003 | **0.0%** (0/40) | 100.0% | **0.0%** (0/28) | 66.7% |
| SFT-002 mode-conditioned | **0.0%** (0/40) | 100.0% | **0.0%** (0/28) | 68.1% |

**Every model in the "good" lineage — base Qwen, SFT-002, SFT-003,
mode-conditioned SFT-002 — recognizes a genuinely valid design as valid
in essentially 0 out of 68 combined valid-item cases (0-2.5%), while
being very good (68-100%) at finding real flaws when one is present.**
SFT-001 — the model with the worst known conversational collapse — is
the *only* one that reliably recognizes validity (100%), though at the
cost of weaker flaw-detection specificity on the actually-flawed items
(83.3% / 36.1%).

Spot-checking confirms this is real, not a judge artifact. Example
(SFT-002, a Dev item explicitly labeled valid — a genome-wide CRISPR
screen with high cell representation and multiple biological replicates):

> *"...it has some limitations that need to be considered... there are a
> few points to consider for a more rigorous analysis: [invents an issue
> with CERES correction / MAGeCK-MLE that the scenario doesn't actually
> have]"*

The response opens by conceding the design is reasonable, then manufactures
a technical nitpick anyway. This is exactly the "do not invent a flaw
merely because the prompt is scientific" failure mode that acceptance
tests in every prior phase report claimed had "passed" — but those claims
were based on 1-2 hand-picked, unambiguous acceptance-test items (e.g.
`ACC_006`), not a representative sample. This 68-item combined Dev+Regression
result is far more representative, and it says the opposite for the general
case.

**This is not a BioReason-specific regression** — base Qwen itself shows
the same pattern (2.5% / 0%) before any BioReason-specific training, so
none of the SFT phases caused it, and none of them fixed it either.
SFT-001's rigid, over-templated JSON format — for all its other,
well-documented problems — happens to produce a clean binary
`flaw_detected: true/false` decision that is *better calibrated* on this
one specific axis than any of the more conversationally fluent models.
This is a genuinely new, previously invisible result: the keyword scorer's
`valid_recognized_keyword` check (matching words like "valid",
"reasonable", "defensible" anywhere in the response) was trivially
satisfied by these hedging-then-nitpicking responses, which is why no
prior report caught this.

## 5. Implication for the Roadmap

This changes Phase 2 and Phase 3 of the roadmap
(`~/.claude/plans/kind-questing-seal.md`). The primary-mechanism gap
(patient-level leakage) is still real and still a priority, but this
result surfaces an equally important, previously-unknown gap: **the
model needs dedicated, at-scale training on recognizing valid designs
without inventing a nitpick** — not just the handful of valid-workflow
examples already in `BioReasonTrain-Verified-SFT-v0.2`/`v0.3` (60 + a
handful more), which were clearly not enough signal to overcome
whatever bias Qwen already has toward "always find something to
critique when asked to evaluate."

Recommend folding this into Phase 2's diagnostic work: build a
larger, harder valid-recognition diagnostic set (designs that are
genuinely sound but have a plausible-sounding minor detail to nitpick,
like the CERES/bootstrap-iteration examples found here), and treat
valid-recognition-under-pressure as a first-class metric alongside
primary-mechanism accuracy before any further SFT attempt.

## 6. Files

- `src/bioreason/training/semantic_judge.py` — two-step judge (extract +
  compare)
- `scripts/run_semantic_rescore.py` — re-scoring harness
- `outputs/verified_training/semantic_rescore_v2/` — all raw judge
  outputs (including the rejected v1 leniency-bug evidence in
  `outputs/verified_training/semantic_rescore/` for the record)
- `outputs/verified_training/semantic_rescore_v2/SEMANTIC_RESCORE_SUMMARY.json`
  — machine-readable summary

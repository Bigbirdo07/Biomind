# BioReasonPreference-Verified-DPO-v0.1 — Dataset Report

**Status**: `FROZEN_DATASET_ONLY_NOT_TRAINED`. This is a preference-pair
dataset for DPO. **No DPO training has been run against it.** Per
project governance, DPO does not launch automatically — this document
covers dataset construction only.

## 1. Purpose

Targets a specific, empirically confirmed bias documented in
`BIOREASON_SEMANTIC_SCORER_V1.md`: base Qwen, SFT-002, SFT-003, and
mode-conditioned SFT-002 all recognize a genuinely valid experimental
design as valid in roughly **0% of real Dev/Regression valid-item cases**
(0/40 Dev, 0/28 Regression for most configurations), while flaw-detection
on actually-flawed items is strong (68-100%). A follow-up test (Step 2 of
the mitigation plan) added an explicit "don't manufacture nitpicks"
instruction to the mode-conditioned system prompt and got a partial,
real improvement (Dev valid-recognition 0/40 → 9/40) but no movement on
Regression (0/28 → 0/28) — confirming this is a calibration bias that
prompting alone cannot fully correct, and the natural next lever is
preference optimization on matched pairs.

## 2. Composition

| | Value |
|---|---|
| Total pairs | 19 |
| Train | 17 |
| Val | 2 |

| Category | Count | Purpose |
|---|---|---|
| `VALID_VS_FALSE_ALARM` | 13 | Primary target: chosen correctly recognizes a valid design, rejected invents a plausible-sounding nitpick |
| `PRIMARY_ISSUE_PRIORITIZATION` (used as guardrail) | 4 | Counterweight: chosen correctly identifies a real, serious flaw; rejected misses it and calls the design valid |
| `ACTIONABLE_VS_VAGUE_CORRECTION` | 2 | Reinforces specificity: chosen names the mechanism, rejected gives only a generic category label |

19 pairs is intentionally small — a first, disciplined increment (matching
this project's established pattern of starting small, QC-gating, and
scaling only once the approach is validated), not a claim that this alone
is enough training signal to run DPO on. Scaling this dataset is explicit
future work, not done here.

## 3. Why the Guardrail Category Exists

Training exclusively on "say valid more often" pairs risks teaching the
model to say valid to *everything* — recreating SFT-001's rigid-format
problem in reverse (rigid over-criticism → rigid under-criticism). The 4
`PRIMARY_ISSUE_PRIORITIZATION` pairs are real, unambiguous flaws
(patient-level leakage, batch/group confounding, feature-selection
leakage, pseudoreplication) where the *rejected* response is the one that
claims the design is valid. Any DPO run on this dataset should monitor
flaw-detection rate on held-out Regression items as a regression gate,
exactly as every SFT phase in this project has done.

## 4. Format — Deliberately Not JSON

`preferred_response`/`rejected_response` are stored as a single
`{"text": "..."}` dict (plain prose), not a JSON schema. This required a
fix to `bioreason.schemas.preference.format_dpo_pair()`, which previously
always called `json.dumps()` on the response dict — that would have
trained DPO targets to prefer JSON-formatted output over other
JSON-formatted output, silently re-introducing the exact format-collapse
problem `BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md` diagnosed. The function
now renders a `{"text": ...}` dict as plain text and only falls back to
`json.dumps()` for older-style pairs that don't use this shape (backward
compatible with the historical `bioreason_preference_v0.2` dataset).
`json_formatted_pair_count: 0` confirms all 19 pairs in this dataset
render as prose.

## 5. Provenance — Honest Labeling

All 19 pairs are labeled `review_status: developer_scientist_reviewed`
(a new value added to `PreferenceReviewStatus` this phase) and
`source_type: EXPERT_SCIENTIFIC_CONTRAST` with an explicit `source`
string naming this phase. **None are labeled `PREF_A` ("human expert
reviewed") or `expert_validated`.**

This distinction matters because of a real problem found in the existing
`training_data/preferences/bioreason_preference_v0.2/` dataset (245 pairs,
including 44 in the same `VALID_VS_FALSE_ALARM` category): those pairs
carry `source: "bioreason_expert_review"` and `review_status: "PREF_A"`
("Human expert reviewed"), but the project's own
`BIOREASON_MODEL_PROVENANCE_LEDGER.md` documents that the entire DPO
lineage those pairs were built for (`BR-DPO-002-A` and related) has
**`NO_EVIDENCE_OF_TRAINING`** — no real Slurm job, simulated logs, no
physical checkpoint weights. Relabeling that content as freshly reviewed
would repeat the exact provenance-integrity failure this project has
caught and corrected multiple times (see item 43/51 in the phase specs
governing this session: "Do not label automated generation as human
expert review"). This dataset was authored fresh instead, rather than
relabeling the old content.

## 6. Contamination Check

| Against | Overlap | Clean |
|---|---|---|
| Dev / Regression / ConversationDev / all acceptance sets / ModeDev | 0 | Yes |
| `BioReasonTrain-Verified-SFT-v0.3` (existing SFT training data) | 0 | Yes |
| `benchmark/final_v0.2` (sealed) | not checked | `NOT_CHECKED_SEALED_REMAINS_UNREAD_PER_GOVERNANCE` |

All 19 prompts were newly authored for this phase — none reused from any
existing eval set or training corpus.

## 7. Split Integrity

Split by preference-family prefix (85/15 train/val target). Verified:
zero `preference_id` overlap between train (17) and val (2).

## 8. Files

- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.1/train.jsonl`
  (17 pairs, flat `prompt`/`chosen`/`rejected` shape ready for a DPO
  trainer)
- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.1/val.jsonl`
  (2 pairs)
- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.1/pairs_with_full_schema.jsonl`
  (full `BioReasonPreferencePair` schema, including `preference_reason`
  and `error_taxonomy`, for audit trail)
- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.1/DATASET_REPORT.json`
  (machine-readable, with exact hashes)

## 9. What This Does Not Do

- Does not run DPO training. That is a separate, larger, explicitly
  gated step (per every phase spec in this project's history: "Do NOT
  run DPO automatically").
- Does not scale the dataset to production size — 19 pairs is a first
  increment to validate the category structure and format, not a
  claim of sufficiency.
- Does not touch the sealed final benchmark.
- Does not modify `BR-VERIFIED-SFT-002` (still canonical, weights
  unchanged) or any existing checkpoint.

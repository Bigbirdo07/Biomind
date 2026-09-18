# BioReasonPreference-Verified-DPO-v0.2 — Dataset Report

**Status**: `FROZEN`. Scaled ~3x from `BioReasonPreference-Verified-DPO-v0.1`
(19 → 58 pairs), built directly in response to `BR-VERIFIED-DPO-001`'s null
result.

## 1. Why This Exists

`BIOREASON_VERIFIED_DPO_001_REPORT.md` found that DPO training on 19
preference pairs produced **zero measurable change** in valid-recognition
on held-out Dev/Regression items (0/40 → 0/40 Dev-adjacent, 0/28 → 0/28
Regression, measured with the reference-blind semantic judge), while
correctly preserving flaw-detection (unchanged, no overcorrection). The
diagnosis: 19 pairs is not enough training signal to shift a 14.8B-parameter
model's calibration bias, even with LoRA. This dataset directly tests that
diagnosis by scaling up.

## 2. What Changed From v0.1

- All 19 v0.1 pairs carried forward unchanged (same pattern used for SFT
  v0.2 → v0.3: preserve what exists, add on top).
- **39 new pairs added**: 30 valid-recognition, 6 flaw-detection guardrails,
  2 specificity pairs.
- **39 new domains** not covered in v0.1 (metabolomics, epigenetics, flow
  cytometry, pharmacokinetics, digital histopathology, wastewater
  surveillance, multi-omics integration, causal inference, meta-analysis,
  network biology, single-cell perturbation screens, clinical trial design,
  copy-number variation, differential splicing, cfDNA liquid biopsy, and
  more) — breadth was a deliberate goal, since v0.1's zero-generalization
  result could partly reflect narrow domain coverage, not just raw count.

## 3. Rejected Responses Are Grounded in Real Observed Failures

**Critical methodological point**: new rejected responses were not
invented from scratch. Before authoring them, actual failure predictions
from `BR-VERIFIED-SFT-002` and mode-conditioned SFT-002 on real Dev/
Regression valid items were read and categorized into concrete, recurring
false-alarm archetypes:

| Archetype | Real example observed |
|---|---|
| A. Hedge-then-invent | *"a common approach, but it has some limitations"* → invents an unstated limitation |
| B. Concede-then-manufacture-secondary | *"generally a robust experimental design... a few points to consider"* → introduces an unfounded secondary concern |
| C. Second-guess a stated parameter | *"generally valid, but the number of bootstrap iterations may be insufficient"* |
| D. Outright false flaw claim | *"contains a critical flaw"* on a genuinely valid design |
| E. Request unnecessary detail | asks for confirmation of something not needed to judge validity |
| F. Treat comparison as flawed | frames an explicitly justified methodological choice as an unexplained inconsistency |

Every new rejected response in this dataset is one of these six real,
observed archetypes, applied to a fresh scenario. **The scenario text
itself was never reused from Dev/Regression** — doing so would train
directly on the evaluation benchmark's content, invalidating future
measurement on those exact items. Only the *style* of failure was reused;
the *content* is entirely new.

## 4. Composition

| | Value |
|---|---|
| Total pairs | 58 (19 carried forward + 39 new) |
| Train | 52 |
| Val | 6 |

| Category | Count | % |
|---|---|---|
| `VALID_VS_FALSE_ALARM` | 43 | 74% |
| `PRIMARY_ISSUE_PRIORITIZATION` (guardrail) | 11 | 19% |
| `ACTIONABLE_VS_VAGUE_CORRECTION` (specificity) | 4 | 7% |

Guardrail proportion was deliberately kept close to v0.1's ~21% (now 19%)
despite the large increase in valid-recognition pairs, so the
flaw-detection safety net scales roughly with the primary-target signal
rather than being diluted.

## 5. QC Gates — All Pass

| Gate | Result |
|---|---|
| Contamination vs. Dev/Regression/ConversationDev/acceptance/ModeDev | 0 overlaps |
| Contamination vs. `BioReasonTrain-Verified-SFT-v0.3` | 0 overlaps |
| Internal duplicate prompts (v0.1 + new combined) | 0 |
| JSON-formatted chosen/rejected pairs | 0 (all prose, per `format_dpo_pair`'s `{"text": ...}` rendering) |
| Sealed final benchmark | Not checked, per governance |

## 6. Provenance

All 58 pairs labeled `review_status: developer_scientist_reviewed`,
consistent with v0.1 — no claim of independent external expert review.

## 7. Files

- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.2/train.jsonl` (52 pairs)
- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.2/val.jsonl` (6 pairs)
- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.2/pairs_with_full_schema.jsonl`
- `training_data/preferences/BioReasonPreference-Verified-DPO-v0.2/DATASET_REPORT.json`

## 8. Honest Caveat

58 pairs is still small by the standards of published DPO work (typically
thousands to tens of thousands of pairs). This is a meaningful, evidence-
driven increase over v0.1 (3x scale, informed directly by why v0.1 failed),
not a claim that 58 is definitively "enough." If `BR-VERIFIED-DPO-002`
(trained on this dataset) also shows no movement, the honest conclusion
would be that either (a) another order-of-magnitude scale-up is needed, or
(b) DPO with LoRA at this rank is not the right lever for this specific
bias and a different approach (e.g. full-parameter fine-tuning on this
axis, or a much larger SFT-style corpus of valid-recognition examples)
should be considered instead.

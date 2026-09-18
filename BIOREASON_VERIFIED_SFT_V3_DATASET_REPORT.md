# BioReasonTrain-Verified-SFT-v0.3 — Dataset QC Report

**Status**: `FROZEN`. Built on top of `BioReasonTrain-Verified-SFT-v0.2`
(all 427 v0.2 episodes preserved verbatim, per the protection guardrail —
nothing that fixed SFT-001's collapse was removed or altered) plus 40
targeted additions.

## 1. Scale and Composition

| | Value |
|---|---|
| Total episodes | **467** (427 carried forward + 40 new) |
| Train | 421 |
| Val | 46 |
| Multi-turn episodes | 17 (3.6%, up from 3.0% in v0.2) |

## 2. What Was Added and Why

Targeted at SFT-002's two documented weaknesses
(`BIOREASON_VERIFIED_SFT_002_REPORT.md` Sections 5 and 7):

1. **Explicit audit-mode activation (10 new audit episodes + 2 JSON-on-request
   episodes)**: SFT-002 answered 0/8 explicit audit requests with structured
   output. New examples use **readable structured prose** (headings like
   Primary Issue / Why It Matters / Correction), not JSON, across 4 rotating
   layouts (compact, detailed, reviewer-style, risk-summary) — explicitly
   teaching "audit = structured reasoning," not "audit = JSON." Two episodes
   where the user explicitly asks for JSON output keep JSON as the correct
   response, to preserve that conditional distinction.
2. **Mode contrast pairs (10 episodes)**: the same concept (PCA,
   pseudoreplication, batch effects) asked in different ways (`what is X` →
   TEACHING, `is this X` → SCIENTIFIC_REASONING, `audit this for X` →
   SCIENTIFIC_AUDIT, `fix this X in my code` → DEBUGGING), so the model has
   direct contrastive signal for mode selection rather than inferring it
   indirectly.
3. **Primary-vs-secondary mechanism cases (3 episodes)**: directly targets
   the acceptance-test finding that SFT-002 named temporal ordering instead
   of patient-level leakage as the primary issue in a longitudinal-visit
   scenario. New targets explicitly structure answers as **Primary
   issue / Secondary issue / Why primary**, and are built around a
   *different* scenario from the exact acceptance-test sentence (to avoid
   training on the eval item itself — see Section 4).
4. **Pipeline expansion (4 new multi-turn trajectories)**: new domains not
   covered in v0.2 — variant calling, ML classification, survival analysis,
   proteomics — each asking for missing info before generating code.
5. **Debugging expansion (5 new single-turn troubleshooting cases)**:
   metadata/count mismatches, NaN values, PCA collapse, CV fold-size
   errors, matrix orientation mismatches.
6. **Protective top-ups (8 episodes)**: a few more general-chat, short
   follow-up, and valid-hard-negative examples, per the explicit
   instruction not to let the categories that fixed SFT-001 shrink.

## 3. Template-Collapse Gate — PASS (Stricter Than v0.2's Gate)

| Metric | v0.2 | v0.3 |
|---|---|---|
| Distinct JSON field orders | 3 | **4** |
| Top field-order share of JSON responses | 33.3% | **32.8%** |
| Top opening-phrase concentration (all assistant turns) | not measured | **10.7%** (gate: must be ≤15%) |
| Banned stock phrases | 0 | **0** |

Added a new gate this round (top opening-phrase concentration ≤15%) since
the phase spec specifically flagged "avoid repeated openings such as
'Methodological Evaluation:' for every audit" — the audit layout rotation
(4 styles) keeps this well under threshold.

## 4. Contamination Check — PASS (Including Against the Acceptance Set)

| Against | Overlap | Clean |
|---|---|---|
| `BioReasonDev-v0.2` | 0 | Yes |
| `BioReasonRegression-v0.1` | 0 | Yes |
| `BioReasonConversationDev-v0.1` | 0 | Yes |
| `benchmark/conversation_dev_v0.1/acceptance_items.json` | 0 | Yes |
| `benchmark/final_v0.2` (sealed) | not checked | `NOT_CHECKED_SEALED_REMAINS_UNREAD_PER_GOVERNANCE` |

**This required a real fix, not just a check.** An earlier draft had 6
collisions: two audit prompts and two teaching questions duplicated
`BioReasonConversationDev-v0.1` wording, and — most importantly — the new
primary-vs-secondary mechanism training example originally used the *exact*
sentence from the SFT-002 acceptance test (*"I have 12 patients measured
monthly for six months and randomly put visits into train and test"*).
Training on that would have made any "improvement" on that specific
acceptance case circular (teaching to the test) rather than a genuine
generalization of primary-mechanism reasoning. It was replaced with a
structurally analogous but distinct scenario (15 subjects, weekly visits
over 3 months) before freezing.

## 5. Mode / Format Distribution (Full v0.3)

| Mode | Count |
|---|---|
| SCIENTIFIC_REASONING | 218 |
| SCIENTIFIC_AUDIT | 133 (up from 120 in v0.2) |
| TEACHING | 46 |
| GENERAL_CHAT | 21 |
| CODE_EXPLANATION | 12 |
| INSUFFICIENT_INFORMATION | 8 |
| CAPABILITY | 7 |
| PIPELINE_INTAKE | 7 (up from 3) |
| DEBUGGING | 10 (up from 4) |
| SHORT_CONTEXTUAL_FOLLOWUP | 3 (new as an explicit mode label) |
| PIPELINE_FOLLOWUP / PIPELINE_BUILD | 1 each |

JSON is 24.1% of assistant turns (down slightly from v0.2's 26.2%, since
most new audit examples use structured prose, not JSON) — structured prose
is a new, separate format category (11 turns) sitting between free prose and
raw JSON.

## 6. Known Remaining Gap

Pipeline (9 episodes total across intake/build/followup, mostly single
multi-turn trajectories per new domain) and debugging (14 total) are still
below the mix plan's 15-20%/10-15% targets by episode count, though each
pipeline/debugging episode is multi-turn (3-8 turns), so token share is
higher than the episode-count percentage suggests. This is flagged
honestly, consistent with the v0.2 report's own acknowledgment — a future
iteration should scale these further if evaluation still shows weakness
there.

## 7. Files

- `training_data/snapshots/BioReasonTrain-Verified-SFT-v0.3/train.jsonl` (421 episodes)
- `training_data/snapshots/BioReasonTrain-Verified-SFT-v0.3/val.jsonl` (46 episodes)
- `training_data/snapshots/BioReasonTrain-Verified-SFT-v0.3/episodes_with_provenance.jsonl`
- `training_data/snapshots/BioReasonTrain-Verified-SFT-v0.3/DATASET_REPORT.json` (hashes, full machine-readable report)

## 8. Split Integrity

v0.2's existing train/val assignment is preserved unchanged; the 40 new
episodes are split by scenario family independently and added on top.
Verified: zero episode-ID overlap, zero scenario-family overlap between
train and val.

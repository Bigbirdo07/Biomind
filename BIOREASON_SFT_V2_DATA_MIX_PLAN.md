# BioReason SFT-v2 Corrected Data Mix Plan

**Status**: Proposal only. **No training has occurred against this plan.**
Do not begin SFT-002 until this plan is reviewed and a corrected, hashed
dataset (`BioReasonTrain-Verified-SFT-v0.2`) is frozen.

## 1. Why This Plan Exists

`BIOREASON_SFT_001_BEHAVIOR_DIAGNOSIS.md` found that `BR-VERIFIED-SFT-001`'s
1,000-episode training corpus is 100% single-turn `SCIENTIFIC_AUDIT`-mode
JSON targets, with 0% general chat, teaching, multi-turn, pipeline-intake, or
debugging examples. This plan proposes the corrected mixture needed to teach
mode-conditional behavior instead of unconditional structured output.

## 2. Target Mode Distribution

| Mode | Target % | Rationale |
|---|---|---|
| SCIENTIFIC_AUDIT / reasoning | 25–30% | Retain BioReason's core differentiator; reduce from 100% but keep it the largest single category since it's the specialization goal |
| TEACHING / scientific explanation | 20% | Directly addresses the observed "what is PCA" / "explain X" failures |
| PIPELINE_INTAKE / PIPELINE_GENERATION | 15–20% | Directly addresses the "build me a pipeline" failure; must be multi-turn |
| DEBUGGING / CODE_EXPLANATION | 10–15% | Currently 0% represented |
| GENERAL_CHAT / general biology conversation | 10–15% | Currently 0% represented; preserves base Qwen conversational ability |
| Multi-turn follow-up (cross-cutting) | 10–15% of total episodes, distributed across the above modes, not a separate silo | Currently 0% represented; required for context retention |

Existing hard scientific-failure cases (pseudoreplication, leakage,
confounding, experimental-unit errors, causal overclaiming, longitudinal
dependence, multiple testing, hard negatives) must be **retained**, not
discarded — see Section 4.

## 3. Response-Format Variation (Applies Within Every Mode)

The single biggest defect in v0.1 was that `format_episode_response()` always
emitted the same 9-key JSON object. For v2, every mode should mix formats:

- Direct natural-language explanation (no JSON, no headings)
- Structured audit JSON (retained, but **only** for SCIENTIFIC_AUDIT-mode
  episodes and episodes that explicitly request an audit)
- Reviewer-style critique prose
- Conversational Q&A turns
- Pipeline-correction dialogue
- Debugging dialogue

Concretely: `format_episode_response()` (or its v2 successor) must branch on
an explicit `target_mode` / `response_format` field per episode instead of
unconditionally calling `json.dumps(payload)`.

## 4. Reusing the Existing 1,000 Audit Episodes

Do not discard `BioReasonTrain-v0.2-SFT-v0.1`. Instead:

- Keep a representative ~250–300 of the 1,000 as the SCIENTIFIC_AUDIT slice
  (still JSON, since that's the appropriate format when an audit is
  requested), covering the current flaw-type diversity (replication,
  confounding, leakage, transformation, multiple testing, sample size).
- Re-author a subset of the *same* underlying scenarios (same flaw
  reasoning, e.g. pseudoreplication) into 2–3 alternate response styles each
  (direct explanation, reviewer critique, conversational teaching) rather
  than writing entirely new scientific content. This reduces cost and keeps
  the scientific reasoning quality already validated, while breaking the
  1:1 scenario→JSON-template lock.

## 5. New Data To Author

- **Multi-turn pipeline intake** (per item 36 of the phase spec): "Build an
  RNA-seq pipeline" → clarifying questions → retained sample counts → retained
  batch info → retained file path, ending in a generation step.
- **Multi-turn teaching**: concept explained → "explain more simply" →
  "how does this relate to my genes" — testing context retention, not just
  first-turn correctness.
- **Short contextual follow-ups**: "why?", "show me", "what does that mean?",
  requiring resolution against prior turns.
- **Debugging**: real error message → path/context-aware diagnosis → exact
  fix location, not a generic answer.
- **General biology/bioinformatics conversation**: preserve base-Qwen-level
  fluency on "what is a VCF", "what does FDR mean", etc., answered as prose.

## 6. Provenance and Governance Constraints (Carried Forward From Phase Spec)

- Every new episode must record: source, generation method, review status,
  mode, domain, scenario signature, response format.
- `DEVELOPER_SCIENTIST_REVIEWED` (Alberto's manual review) must never be
  mislabeled `INDEPENDENT_EXTERNAL_REVIEW`.
- No item from `benchmark/final_v0.2` (sealed) may enter the corrected SFT
  set. Run the existing contamination tooling between any v2 candidate and
  Dev/Regression/Bench/Challenge before freezing.
- Before any SFT-002 run: freeze train/val splits, generate SHA-256 hashes,
  record mode distribution, and record it as `BioReasonTrain-Verified-SFT-v0.2`
  — a new dataset artifact, not an overwrite of v0.1.

## 7. Training Fix (Independent of Data)

Fix the label-masking gap identified in the diagnosis report: mask loss on
system/user prompt tokens so only assistant-response tokens receive gradient
signal. Use `DataCollatorForCompletionOnlyLM` (or equivalent explicit
assistant-span masking) instead of the current whole-sequence
`DataCollatorForLanguageModeling`.

## 8. What This Plan Does Not Do

This plan does not train SFT-002, does not touch the sealed final benchmark,
and does not authorize DPO. Per the governing phase constraints, SFT-002 may
only begin after the corrected dataset is authored, reviewed, hashed, and
contamination-checked.

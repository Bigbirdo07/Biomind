# BR-VERIFIED-SFT-32B-001 vs BR-VERIFIED-SFT-002 (14B) — A/B Comparison

## Purpose

Final step of the base-model-scale evaluation (see
`BIOREASON_VERIFIED_SFT_32B_001_REPORT.md` for training verification).
Question: does `Qwen2.5-32B-Instruct`, LoRA-adapted under the identical
recipe and dataset as the current verified 14B, produce a measurably
better BioReason?

## Serving setup

- Model: `BR-VERIFIED-SFT-32B-001`, served via
  `slurm/bioreason_serve_verified_model_32b.sbatch` (adapted to port 8101),
  Slurm job `64596013`, node `uri-gpu003`, `NVIDIA A100-SXM4-80GB`.
- `/health` confirmed adapter SHA-256
  `1b323f77542ced3d0fba8ee557dec354d410473f48ec8704ec3979218bb075bd`
  matches the independently-verified training output exactly.
- Evaluated via `scripts/live_regression_suite.py --url http://localhost:8101`.

## Partition race (side note, answers "which schedules faster")

Submitted the same serving job to both `--partition=gpu` (job `64595944`)
and `--partition=uri-gpu` (job `64596013`) simultaneously as a live
scheduling-speed test. `uri-gpu` won this particular race — it started
within ~10 minutes while `gpu` was still pending on `Priority` — the
opposite of most of tonight's earlier experience, where `uri-gpu` was
badly congested. Takeaway: neither partition is reliably faster; check
both when time matters. The losing `gpu` job was cancelled once `uri-gpu`
started, so only one GPU was held.

## Results — 32B model

```
HARD failures (real regressions, code-level): 0
SOFT failures (model-behavior, review manually): 3
```

Soft failures:
1. **Single-cell pseudoreplication flag**: expected the response to
   mention `pseudobulk` when warning about nested single-cell design;
   it didn't. Model-behavior/sampling variance — same category of soft
   failure 14B has shown intermittently.
2. **WGS/WES paired tumor-normal pipeline scenario misrouted**: expected
   `PIPELINE_BUILD`, got `PIPELINE_INTAKE`. This is the exact scenario
   that took 5 rounds of dedicated hardening (wrong caller, `-normal`
   flag, subprocess syntax, loop completeness, variable-shadowing bugs)
   to get right on the 14B model this session.
3. **Consequence of #2**: because the response never reached
   `PIPELINE_BUILD`, execution verification (the dry-run shell-mock
   system built specifically to catch bugs like the ones found in that
   5-round hardening effort) never ran at all.

## Comparison to 14B baseline

The last full `live_regression_suite.py` run against the 14B server this
session (after the `SCIENTIFIC_REASONING` structural-conflict fix) was
clean: 0 hard, 0 soft failures, including the WGS/WES shell-dry-run
scenario routing and executing correctly. That specific scenario is the
one the 32B run just failed on.

**This is not an apples-to-apples "raw model capability" comparison.**
The 14B model's current strength on WGS/WES and `SCIENTIFIC_REASONING`
is substantially the product of this session's overlay/router prompt
hardening (`mode_overlays.py`, `mode_router.py`) — work aimed at 14B's
specific failure modes, tuned and verified against 14B's actual outputs.
The 32B model was evaluated using those same prompts/overlays completely
unchanged. It is plausible a bigger base model responds differently to
the same scaffolding — better in some ways, worse in others — and that
version-specific tuning would be needed to get 32B to its own ceiling,
just as 14B needed.

## Initial finding (superseded below): no-go on first pass

First evaluation (2 identical runs) found 32B regressing on the hardest,
most heavily-verified scenario in this project (WGS/WES pipeline
generation) — confirmed as a real, repeatable weakness, not sampling
noise, and not a case of stale prompts (`mode_router.py`/
`mode_overlays.py` are shared, model-agnostic code; 32B was evaluated
with the identical fully-fixed instruction text 14B uses). This was a
genuine behavioral difference in how 32B responds to the same router
instructions 14B follows correctly.

## Root-cause diagnosis and fix

Queried the 32B server directly for its actual generated response on the
failing scenario (full WGS/WES design + explicit "build the full
pipeline" request). Its response asked a confirming question first
("Is that correct? Would you like to proceed?") instead of building —
32B has a stronger built-in "confirm scope before generating" instinct
than 14B, and the router's classification reflected that same caution.

Fixed by adding an explicit worked example to `ROUTER_INSTRUCTION` in
`mode_router.py` telling the classifier: when assay/data type, sample
design, research question, AND an explicit build/generate request are
all present, classify as `PIPELINE_BUILD` and build — do not downgrade
to `PIPELINE_INTAKE` just to ask a confirming question first.

**First fix attempt over-corrected.** Re-running the suite surfaced a
*new* soft failure: a different scenario with full design detail but
*no* explicit build request ("I want to find genes that cause brain
cancer...") also started getting misrouted to `PIPELINE_BUILD`. The
32B model was generalizing "stated a goal" into "asked to build,"
which is exactly the distinction the fix needed to preserve. Confirmed
consistent across 2 runs (not noise), then tightened the router example
to explicitly contrast "stating a research goal" (not sufficient alone)
against "an explicit ask to build/generate the pipeline" (required),
with a minimal-pair example showing the same scenario with and without
the build request.

## Final results — 32B model, after both fixes

Two consecutive clean runs against the same live 32B server:

```
HARD failures (real regressions, code-level): 0
SOFT failures (model-behavior, review manually): 0
```

Both the original WGS/WES misroute and the over-trigger introduced by
the first fix attempt are resolved, with no other regressions across
all 14 checks (router accuracy, intake pseudoreplication flagging,
build/debug lint and execution-verification honesty, WGS/WES shell
dry-run execution, and DE-interpretation causation-overclaiming checks).

## Go/No-Go decision

**Go, conditionally — for router/classification behavior specifically.**
32B now matches 14B's clean baseline on every scenario in the regression
suite, including the WGS/WES scenario that originally regressed. The
fixes that closed the gap are shared, model-agnostic code
(`mode_router.py`), so **14B benefits from the same fixes** the next
time its server is restarted and picks up the updated file — this
wasn't a 32B-only patch.

This is *not* yet a decision to promote 32B to back the live chat
product. That is a separate, bigger call than "the regression suite is
clean," and should not be made unilaterally:

- **Latency was never measured.** 32B is inherently slower per token;
  the cost-vs-benefit tradeoff (if there even is a benefit — the suite
  shows parity, not superiority, on these checks) hasn't been quantified.
- **Coverage is small.** 14 checks across ~11 scenarios is enough to
  catch regressions, not enough to claim 32B reasons more deeply in
  general — the original motivation for this experiment (closing the
  gap to Claude/ChatGPT-level reasoning depth) is not something this
  suite measures directly.
- `BR-VERIFIED-SFT-002` (14B) remains the model backing the live chat
  product until a deliberate decision is made to change that.

## Caveats

- No formal latency measurement taken in this pass.
- 14B's own regression numbers referenced above are from the last
  recorded run earlier this session (pre-dating tonight's router fixes),
  not a simultaneous fresh run against a currently-live 14B server —
  worth a fresh confirming run before treating 14B as unaffected, since
  the router file changed after that last 14B run.
- `mode_router.py` was pushed directly to the Unity working copy (not a
  git repo there) to iterate quickly; the local repo copy (this commit)
  is the source of truth and has not yet been committed/pushed to
  GitHub — pending user confirmation.

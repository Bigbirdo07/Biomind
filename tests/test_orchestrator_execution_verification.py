"""
tests/test_orchestrator_execution_verification.py

Offline tests for the execution-in-the-loop verification stage wired into
run_orchestrated_turn (src/bioreason/inference/orchestrator.py). Uses a
fake generate_fn closure (no GPU/model needed) that returns canned
responses by call order, so these test the ORCHESTRATOR'S wiring (field
population, one-retry cap, fallback caveat text) deterministically,
independent of any live model's actual behavior.

Bug patterns used here are deliberately chosen to NOT match any
code_lint.py regex (no AnnData/.groupby(), no QC-column, no "pseudobulk"
keyword, no missing sc.tl.umap pattern) -- this isolates testing to the
NEW execution-verification stage specifically, since code_lint already has
its own dedicated test suite (tests/test_code_lint.py).
"""

from bioreason.inference.orchestrator import run_orchestrated_turn

ROUTER_PIPELINE_BUILD = '{"mode": "PIPELINE_BUILD", "confidence": 1.0, "explicit_user_request": true}'
ROUTER_PIPELINE_DEBUG = '{"mode": "PIPELINE_DEBUG", "confidence": 1.0, "explicit_user_request": true}'
ROUTER_GENERAL_CHAT = '{"mode": "GENERAL_CHAT", "confidence": 1.0, "explicit_user_request": false}'

BROKEN_CODE_RESPONSE = (
    "Here is the code:\n\n```python\nimport pandas as pd\n"
    "counts = pd.read_csv('counts.csv')\n"
    "print(counts.hea())\n```\n"  # typo: .hea() instead of .head() -> AttributeError
)

FIXED_CODE_RESPONSE = (
    "Here is the corrected code:\n\n```python\nimport pandas as pd\n"
    "counts = pd.read_csv('counts.csv')\n"
    "print(counts.head())\n```\n"
)

WORKING_CODE_RESPONSE = (
    "Here is the code:\n\n```python\nimport pandas as pd\n"
    "counts = pd.read_csv('counts.csv')\n"
    "print(counts.shape)\n```\n"
)

UNSUPPORTED_IO_RESPONSE = (
    "Here is the code:\n\n```python\nimport pysam\n"
    "bam = pysam.AlignmentFile('reads.bam')\n```\n"
)


def make_fake_generate_fn(*canned_responses):
    calls = {"count": 0}

    def generate_fn(messages, max_new_tokens):
        idx = calls["count"]
        calls["count"] += 1
        return canned_responses[min(idx, len(canned_responses) - 1)]

    generate_fn.call_count = lambda: calls["count"]
    return generate_fn


def test_broken_code_never_fixed_gets_honest_caveat():
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_BUILD,   # router call
        BROKEN_CODE_RESPONSE,    # main response
        BROKEN_CODE_RESPONSE,    # corrective regen attempt (still broken)
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="I have a bulk RNA-seq count matrix in counts.csv, give me code to load it.",
    )
    assert result.execution_verified is False
    assert result.execution_error is not None
    assert "AttributeError" in result.execution_error
    assert "Execution in a controlled test environment" in result.response
    assert result.execution_regeneration_used is False


def test_broken_code_fixed_on_regeneration():
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_BUILD,
        BROKEN_CODE_RESPONSE,
        FIXED_CODE_RESPONSE,     # corrective regen produces working code
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="I have a bulk RNA-seq count matrix in counts.csv, give me code to load it.",
    )
    assert result.execution_verified is True
    assert result.execution_regeneration_used is True
    assert result.response == FIXED_CODE_RESPONSE
    assert "Execution in a controlled test environment" not in result.response


def test_working_code_verified_without_regeneration():
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_BUILD,
        WORKING_CODE_RESPONSE,
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="I have a bulk RNA-seq count matrix in counts.csv, give me code to load it.",
    )
    assert result.execution_verified is True
    assert result.execution_regeneration_used is False
    # Only 2 calls should have happened: router + main response, no fix attempt.
    assert generate_fn.call_count() == 2


def test_pipeline_debug_mode_also_gets_execution_verification():
    # PIPELINE_DEBUG proposes a fix for a reported bug -- still generated
    # code that can be wrong in a new way, so it needs the same real-
    # execution check as PIPELINE_BUILD, not just the static linter.
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_DEBUG,
        BROKEN_CODE_RESPONSE,
        BROKEN_CODE_RESPONSE,
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="I got an AttributeError running this fix, what's wrong?",
    )
    assert result.execution_verified is False
    assert result.execution_error is not None
    assert "AttributeError" in result.execution_error
    assert "Execution in a controlled test environment" in result.response


def test_pipeline_debug_fix_verified_when_correct():
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_DEBUG,
        WORKING_CODE_RESPONSE,
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="Here's my error, can you fix it?",
    )
    assert result.execution_verified is True
    assert result.execution_regeneration_used is False


def test_non_pipeline_build_mode_skips_execution_verification():
    generate_fn = make_fake_generate_fn(
        ROUTER_GENERAL_CHAT,
        "Hello! I can help with a variety of bioinformatics topics.",
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="hi, what can you do?",
    )
    assert result.execution_verified is None
    assert result.execution_error is None


def test_unsupported_io_skips_execution_verification_without_flagging():
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_BUILD,
        UNSUPPORTED_IO_RESPONSE,
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="I have a BAM file, give me code to inspect it.",
    )
    # Fixture can't safely be synthesized for a .bam read -> skipped, not
    # flagged as a failure.
    assert result.execution_verified is None
    assert "Execution in a controlled test environment" not in result.response


def test_execution_verification_can_be_disabled():
    generate_fn = make_fake_generate_fn(
        ROUTER_PIPELINE_BUILD,
        BROKEN_CODE_RESPONSE,
    )
    result = run_orchestrated_turn(
        generate_fn=generate_fn,
        history=[],
        user_message="I have a bulk RNA-seq count matrix in counts.csv, give me code to load it.",
        enable_execution_verification=False,
    )
    assert result.execution_verified is None
    assert generate_fn.call_count() == 2  # router + main response only, no fix attempt

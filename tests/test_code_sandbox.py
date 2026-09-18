"""
tests/test_code_sandbox.py

Unit tests for bioreason.inference.code_sandbox -- offline, no GPU/model
needed. Runs real Python subprocesses against deliberately broken and
deliberately correct toy code.
"""

import sys
import tempfile
from pathlib import Path

import pytest

from bioreason.inference.code_sandbox import run_in_sandbox


def _run(source: str, **kwargs):
    with tempfile.TemporaryDirectory() as workdir:
        return run_in_sandbox(source, Path(workdir), **kwargs)


def test_correct_code_returns_ok():
    result = _run("x = 1 + 1\nassert x == 2\n")
    assert result.status == "OK"


def test_undefined_variable_returns_exception_with_traceback():
    result = _run("print(undefined_variable)\n")
    assert result.status == "EXCEPTION"
    assert "NameError" in result.traceback_text


def test_attribute_error_returns_exception_with_traceback():
    result = _run("x = 5\nx.groupby('a')\n")
    assert result.status == "EXCEPTION"
    assert "AttributeError" in result.traceback_text


def test_infinite_loop_returns_timeout():
    result = _run("while True:\n    pass\n", timeout_seconds=2)
    assert result.status == "TIMEOUT"


@pytest.mark.skipif(
    sys.platform != "linux",
    reason=(
        "RLIMIT_AS enforcement is unreliable on macOS (virtual memory can be "
        "reserved without being committed, so the cap is often a no-op); "
        "this behaves correctly on Linux, which is the actual Unity HPC "
        "deployment target this sandbox runs on."
    ),
)
def test_huge_allocation_returns_resource_limit_or_exception():
    # Actually touch every page (not just reserve address space) so the
    # allocation is real and the memory cap has something to catch.
    result = _run(
        "data = bytearray(b'\\x01' * (2 * 1024 * 1024 * 1024))\n",  # 2GB, fully written
        memory_limit_mb=256,
        timeout_seconds=10,
    )
    assert result.status in ("RESOURCE_LIMIT", "EXCEPTION")


def test_missing_dependency_returns_environment_error_not_exception():
    # A broken/missing import should never be attributed to the generated
    # code's logic -- the model can't fix a dependency conflict by
    # rewriting its code, and presenting it as a code bug would mislead
    # the user about what's actually wrong.
    result = _run("import this_module_does_not_exist_anywhere\n")
    assert result.status == "ENVIRONMENT_ERROR"
    assert "ImportError" in result.traceback_text or "ModuleNotFoundError" in result.traceback_text


def test_shared_object_load_failure_returns_environment_error():
    # Seen live: numba/llvmlite failing to locate its native shared
    # library raises OSError, not ImportError -- must still be classified
    # as an environment problem, not a code bug.
    result = _run(
        "raise OSError('Could not find/load shared object file')\n"
    )
    assert result.status == "ENVIRONMENT_ERROR"


def test_inherits_ld_library_path_from_parent_environment():
    # Regression test: an earlier version of this sandbox stripped the
    # subprocess environment down to an allowlist of just PATH/HOME/
    # PYTHONDONTWRITEBYTECODE, which broke native-extension packages
    # (numba/llvmlite) that need LD_LIBRARY_PATH or similar to locate their
    # shared libraries -- found live on Unity. The env must now be
    # inherited by denylist (drop credential-looking vars only), not
    # rebuilt from a narrow allowlist.
    import os
    os.environ["_FX_TEST_SENTINEL_VAR"] = "sentinel_value_12345"
    try:
        result = _run("import os\nassert os.environ.get('_FX_TEST_SENTINEL_VAR') == 'sentinel_value_12345'\n")
    finally:
        del os.environ["_FX_TEST_SENTINEL_VAR"]
    assert result.status == "OK", result.stderr


def test_strips_credential_looking_env_vars():
    import os
    os.environ["MY_SECRET_API_KEY"] = "should-not-leak"
    try:
        result = _run("import os\nassert 'MY_SECRET_API_KEY' not in os.environ\n")
    finally:
        del os.environ["MY_SECRET_API_KEY"]
    assert result.status == "OK", result.stderr


def test_default_memory_limit_permits_scanpy_import():
    # Regression test: scanpy's dependency chain (numba/llvmlite) reserves
    # several GB of VIRTUAL address space just to import, well before any
    # data is touched -- RLIMIT_AS (which caps virtual, not physical,
    # memory) at the old 1024MB default denied that reservation and
    # llvmlite reported a misleading "could not find/load shared object
    # file" error instead of a clear out-of-memory message. Found live on
    # Unity; the default must stay generous enough for a plain scanpy
    # import to succeed.
    pytest.importorskip("scanpy")
    result = _run("import scanpy\nprint('ok')\n", timeout_seconds=30)
    assert result.status == "OK", (result.status, result.stderr[-500:] if result.stderr else None)


def test_writes_script_into_workdir():
    with tempfile.TemporaryDirectory() as workdir:
        run_in_sandbox("pass\n", Path(workdir))
        assert (Path(workdir) / "_generated.py").exists()

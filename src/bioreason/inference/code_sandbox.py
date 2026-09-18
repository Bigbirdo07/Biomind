"""
src/bioreason/inference/code_sandbox.py

Runs a block of generated Python source in a resource-limited subprocess
and reports back a structured result -- real execution, not a heuristic
pattern match. Complements code_lint.py: the linter catches known failure
shapes cheaply; this catches anything, at the cost of actually running it.

No container tooling (Docker/Singularity/Apptainer) is confirmed available
on the Unity HPC node this runs on, so isolation is stdlib subprocess +
resource.setrlimit + a wall-clock timeout -- proportionate to the actual
threat model here: this is BioReason's OWN generated code for a legitimate
user's request, not arbitrary user-submitted code, so the goal is catching
accidental bugs (infinite loops, huge allocations, real exceptions), not
defending against a deliberate escape attempt.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SandboxResult:
    status: str  # "OK" | "EXCEPTION" | "TIMEOUT" | "RESOURCE_LIMIT" | "ENVIRONMENT_ERROR"
    stdout: str = ""
    stderr: str = ""
    traceback_text: Optional[str] = None
    duration_seconds: float = 0.0


def _make_resource_limiter(memory_limit_mb: int, cpu_seconds: int):
    """Returns a preexec_fn (POSIX only) applying best-effort resource caps
    in the child process before exec. Never raises -- a platform that
    doesn't support a given limit just runs unconstrained on that axis
    rather than failing the whole sandbox call."""
    def _limiter():
        import resource
        mem_bytes = memory_limit_mb * 1024 * 1024
        for limit, value in (
            (resource.RLIMIT_AS, (mem_bytes, mem_bytes)),
            (resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds)),
            (resource.RLIMIT_NOFILE, (64, 64)),
        ):
            try:
                resource.setrlimit(limit, value)
            except (ValueError, OSError):
                pass
    return _limiter


_ENVIRONMENT_ERROR_PREFIXES = (
    "ImportError", "ModuleNotFoundError",
    "OSError: Could not find/load shared object file",  # e.g. numba/llvmlite native lib loading
)


def _is_environment_error(traceback_text: str) -> bool:
    """True if the last raised exception indicates a missing or broken
    dependency/native library in the execution environment itself -- never
    something fixable by rewriting the generated code's logic. Checks the
    final exception line specifically (not the whole traceback body), since
    a genuine code bug could legitimately mention "import" in an earlier
    frame without being an import/environment failure."""
    if not traceback_text:
        return False
    last_line = traceback_text.strip().splitlines()[-1] if traceback_text.strip() else ""
    return any(last_line.startswith(prefix) for prefix in _ENVIRONMENT_ERROR_PREFIXES)


def _extract_traceback(stderr: str) -> Optional[str]:
    if not stderr:
        return None
    marker = "Traceback (most recent call last):"
    idx = stderr.rfind(marker)
    if idx == -1:
        return stderr.strip()[-2000:] or None
    return stderr[idx:].strip()[-2000:]


def run_in_sandbox(
    source: str,
    workdir: Path,
    timeout_seconds: int = 20,
    # RLIMIT_AS caps VIRTUAL address space, not physical memory used --
    # found live that scanpy's dependency chain (numba/llvmlite) reserves
    # several GB of virtual address space just to load, well before any
    # data is touched, and gets a misleading "could not find/load shared
    # object file" error (not a clear out-of-memory message) when that
    # reservation is denied. 1024 was far too tight for any scanpy-based
    # code; 4096 gives real scientific-stack headroom while still catching
    # genuinely runaway growth in a reasonable time.
    memory_limit_mb: int = 4096,
) -> SandboxResult:
    """Writes `source` (full Python source, including any fixture preamble)
    to workdir/_generated.py and runs it as a subprocess with cwd=workdir.
    Uses sys.executable, not a hardcoded interpreter path, so it
    automatically inherits whichever environment has the bio packages
    installed -- the same interpreter the calling server process runs
    under."""
    script_path = workdir / "_generated.py"
    script_path.write_text(source)

    # Inherit the full environment (conda/library paths like LD_LIBRARY_PATH
    # and CONDA_PREFIX are needed for native-extension packages -- e.g.
    # numba/llvmlite fail to locate their shared library without them, found
    # live when an earlier allowlist-only env dropped everything but PATH/
    # HOME/PYTHONDONTWRITEBYTECODE) and strip by denylist instead: drop
    # anything that looks like a credential rather than guessing an
    # allowlist that might be missing something a package legitimately needs.
    # Critically, do NOT override HOME to a fresh directory: also found
    # live, numba builds a compilation cache keyed off HOME, and pointing
    # it at an unfamiliar directory on Unity's networked scratch filesystem
    # made cache creation hang indefinitely (60s+, zero stderr) instead of
    # failing cleanly -- the real HOME lets it reuse its existing cache and
    # complete in ~8s. cwd=workdir (below) already isolates where the code
    # itself reads/writes without needing to touch HOME.
    env = {
        k: v for k, v in os.environ.items()
        if not any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))
    }
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    preexec_fn = _make_resource_limiter(memory_limit_mb, timeout_seconds + 5) if os.name == "posix" else None

    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(workdir),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            preexec_fn=preexec_fn,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        return SandboxResult(
            status="TIMEOUT",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            duration_seconds=time.time() - t0,
        )

    duration = time.time() - t0
    if proc.returncode == 0:
        return SandboxResult(status="OK", stdout=proc.stdout, stderr=proc.stderr, duration_seconds=duration)

    # A resource-limit kill typically shows up as a negative returncode
    # (killed by signal) or a MemoryError with no normal traceback frame,
    # rather than a clean Python exception -- treat those as inconclusive,
    # not a code bug.
    tb = _extract_traceback(proc.stderr) or ""
    if proc.returncode < 0 or "MemoryError" in (proc.stderr or ""):
        status = "RESOURCE_LIMIT"
    elif _is_environment_error(tb):
        # A missing/broken dependency (e.g. a package version conflict in
        # the server's own environment) is never something the MODEL can
        # fix by rewriting its logic -- feeding this back as a "corrective
        # regeneration" request would just reproduce the identical error,
        # and showing it to the user as a code problem would be actively
        # misleading. Treated as inconclusive, same as TIMEOUT/RESOURCE_LIMIT.
        status = "ENVIRONMENT_ERROR"
    else:
        status = "EXCEPTION"

    return SandboxResult(
        status=status,
        stdout=proc.stdout,
        stderr=proc.stderr,
        traceback_text=tb or None,
        duration_seconds=duration,
    )

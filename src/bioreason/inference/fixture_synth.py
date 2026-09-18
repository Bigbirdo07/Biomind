"""
src/bioreason/inference/fixture_synth.py

Synthetic fixture support for execution-in-the-loop verification of
PIPELINE_BUILD-generated code (see code_sandbox.py). BioReason never has
access to a user's real data files -- it's chat-only, no upload -- so
verifying generated code actually RUNS requires standing in synthetic data
that structurally matches what the code expects.

Design choice: rather than writing real fixture files to disk and hoping
the code's hardcoded paths line up with them, this monkeypatches the
file-reading functions themselves (sc.read_10x_h5, sc.read_h5ad,
anndata.read_h5ad, pd.read_csv, pd.read_table) so ANY call to them, with
any path argument, returns a fresh synthetic object. This sidesteps two
problems at once: (1) brittle path/f-string matching against whatever the
model happened to hardcode, and (2) format fidelity -- sc.read_10x_h5
expects Cell Ranger's specific on-disk HDF5 layout, which is NOT the same
as anndata's native .h5ad format, so writing a fake file there would raise
a misleading format error unrelated to any actual bug in the code.

If the code reads data through a mechanism we cannot safely intercept this
way (raw open(), or another language entirely), execution verification is
skipped for that block rather than risking a misleading false-positive
failure -- an execution result that's wrong for the wrong reason is worse
than not attempting execution at all, since "the code was actually run"
reads as more authoritative than a heuristic warning.

A second, complementary strategy handles shell-orchestration pipelines
(bwa/samtools/gatk/bcftools invoked via subprocess -- the norm for WGS/WES
variant calling, not the scanpy/pandas norm above). Live testing found
most of the real bugs in this kind of code are NOT bioinformatics mistakes
at all -- they're ordinary Python control-flow bugs (zip() argument-count
mismatches, a variable reassigned to one of its own elements, a loop
variable from one loop mistaken for a list in the next). None of these
need real reference genomes or real sequencing data to catch; they need
the actual Python loop/function/zip() structure to actually execute. So
instead of faking genomic data, this monkeypatches subprocess.run/Popen/
call/check_call/check_output to no-op stubs and runs the real script --
every loop, every zip(), every function call executes for real. Only the
question "did BWA actually align reads correctly" goes unanswered, which
was never answerable anyway. This does NOT catch bugs that don't raise a
Python exception on their own (e.g. a malformed shell command string that
a permissive stub happily "runs" without complaint, or a tuple that
silently stringifies into an f-string) -- those still need code_lint.py's
static checks, which this complements rather than replaces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

GROUP_KEYWORDS = [
    "tumor", "normal", "treated", "control", "controls", "infected",
    "uninfected", "healthy", "neoplastic", "responder", "nonresponder",
    "case", "cases", "disease", "wildtype", "mutant", "wt", "ko",
]

H5AD_KEYWORDS = [
    "h5ad", "single-cell", "single cell", "scrna", "sc-rna", "10x",
    "filtered_feature_bc_matrix", ".h5",
]
COUNT_MATRIX_KEYWORDS = [
    "count matrix", "bulk rna", "deseq2", "count_matrix", ".csv",
]

# Any of these markers means the code reads data through a mechanism we
# cannot safely fixture even via the shell-dry-run path -- execution
# verification is skipped for the whole block, not flagged as a bug.
UNSUPPORTED_IO_MARKERS = [
    r"\bopen\s*\(",
    r"\bRscript\b",
    r"^\s*library\s*\(",
]

H5AD_READER_CALLS = ("sc.read_10x_h5", "sc.read_h5ad", "anndata.read_h5ad", "ad.read_h5ad")
CSV_READER_CALLS = ("pd.read_csv", "pd.read_table")
SUBPROCESS_CALL_RE = re.compile(r"\bsubprocess\.(run|Popen|call|check_call|check_output)\s*\(")


def infer_dataset_shape(
    user_message: str,
    history: List[Dict[str, str]],
    pipeline_context_summary: Optional[str],
) -> Dict[str, Any]:
    """Lightweight heuristic extraction of dataset shape from conversation
    text -- same regex/keyword style as
    bioreason.pipeline.state_machine.PipelineStateManager.update_from_user_text,
    adapted locally rather than imported so this module stays dependency-free
    and independently testable. v1 only needs to distinguish "single-cell"
    vs "bulk count-matrix" shape plus sample/group counts -- not full
    fidelity, since the fixture's only job is to catch structural code bugs,
    not reproduce the user's real data."""
    parts = [pipeline_context_summary or ""]
    for turn in history:
        parts.append(turn.get("content", ""))
    parts.append(user_message)
    combined = " ".join(parts).lower()

    kind = "unknown"
    if any(k in combined for k in H5AD_KEYWORDS):
        kind = "h5ad"
    elif any(k in combined for k in COUNT_MATRIX_KEYWORDS):
        kind = "count_matrix"

    group_counts: Dict[str, int] = {}
    for m in re.finditer(r"(\d+)\s+([a-zA-Z][a-zA-Z\-]{2,20})", combined):
        n, label = int(m.group(1)), m.group(2)
        if label in GROUP_KEYWORDS and 0 < n <= 1000:
            group_counts[label] = n

    sample_count = sum(group_counts.values()) if group_counts else None

    return {
        "kind": kind,
        "sample_count": sample_count,
        "group_counts": group_counts,
    }


@dataclass
class FixturePlan:
    confidence: str  # "high" | "none"
    reason: str
    kind: str = "python_lib"  # "python_lib" | "shell_dry_run"
    uses_h5ad_readers: bool = False
    uses_csv_readers: bool = False
    shape: Dict[str, Any] = field(default_factory=dict)


def build_fixture_plan(code: str, shape: Dict[str, Any]) -> FixturePlan:
    # Raw open() stays unsupported regardless of path -- can't safely fake
    # arbitrary binary file content generically.
    if re.search(r"\bopen\s*\(", code):
        return FixturePlan(confidence="none", reason="raw open() call present", shape=shape)

    # Shell-orchestration code (WGS/WES-style bwa/samtools/gatk pipelines):
    # .bam/.fastq/.vcf mentions here are just string arguments to external
    # tools, not parsed by a Python library that needs real content, so
    # they're expected and fine -- route to the dry-run mock path instead
    # of bailing out.
    if SUBPROCESS_CALL_RE.search(code):
        return FixturePlan(confidence="high", reason="ok", kind="shell_dry_run", shape=shape)

    for pattern in UNSUPPORTED_IO_MARKERS:
        if pattern == r"\bopen\s*\(":
            continue  # already checked above
        if re.search(pattern, code, re.MULTILINE):
            return FixturePlan(confidence="none", reason=f"unsupported I/O pattern: {pattern}", shape=shape)

    uses_h5ad = any(fn in code for fn in H5AD_READER_CALLS)
    uses_csv = any(fn in code for fn in CSV_READER_CALLS)

    if not uses_h5ad and not uses_csv:
        return FixturePlan(confidence="none", reason="no recognized file I/O found", shape=shape)

    return FixturePlan(
        confidence="high", reason="ok", kind="python_lib",
        uses_h5ad_readers=uses_h5ad, uses_csv_readers=uses_csv, shape=shape,
    )


def build_execution_preamble(plan: FixturePlan) -> str:
    """Python source injected before the generated code block. Monkeypatches
    whichever file-reading functions the code uses so every call to them
    returns a fresh synthetic object instead of touching the real
    filesystem. Exact content fidelity across different calls doesn't
    matter for the purpose here -- what matters is that .X/.obs/.var (or
    the returned DataFrame) have plausible shapes so downstream
    .groupby()/aggregation/indexing logic can be genuinely exercised."""
    if plan.kind == "shell_dry_run":
        return _build_shell_dry_run_preamble()

    if not plan.uses_h5ad_readers and not plan.uses_csv_readers:
        return ""

    group_counts = plan.shape.get("group_counts") or {}
    groups = list(group_counts.keys()) or ["group_a", "group_b"]

    lines = ["import numpy as _fx_np", "import pandas as _fx_pd"]

    if plan.uses_h5ad_readers:
        lines.append(
            "import anndata as _fx_anndata\n"
            "import scanpy as _fx_sc\n"
            "\n"
            "def _fx_make_adata(*_fx_args, **_fx_kwargs):\n"
            "    _rng = _fx_np.random.default_rng(0)\n"
            "    _n_obs, _n_vars = 40, 200\n"
            f"    _groups = {groups!r}\n"
            "    _X = _rng.poisson(2, size=(_n_obs, _n_vars)).astype('float32')\n"
            "    _obs = _fx_pd.DataFrame({\n"
            "        'sample': [f'sample{i % max(len(_groups), 1)}' for i in range(_n_obs)],\n"
            "        'animal': [f'animal{i % max(len(_groups), 1)}' for i in range(_n_obs)],\n"
            "        'condition': [_groups[i % len(_groups)] for i in range(_n_obs)],\n"
            "    })\n"
            "    _obs.index = [f'CELL{i}' for i in range(_n_obs)]\n"
            "    _var = _fx_pd.DataFrame(index=[f'GENE{i}' for i in range(_n_vars)])\n"
            "    return _fx_anndata.AnnData(X=_X, obs=_obs, var=_var)\n"
            "\n"
            "_fx_sc.read_10x_h5 = _fx_make_adata\n"
            "_fx_sc.read_h5ad = _fx_make_adata\n"
            "_fx_anndata.read_h5ad = _fx_make_adata\n"
        )

    if plan.uses_csv_readers:
        lines.append(
            "def _fx_make_df(*_fx_args, **_fx_kwargs):\n"
            "    _rng = _fx_np.random.default_rng(0)\n"
            f"    _group_counts = {group_counts!r}\n"
            "    if _group_counts:\n"
            "        _cols = []\n"
            "        for _label, _n in _group_counts.items():\n"
            "            _cols += [f'{_label}_{i+1}' for i in range(_n)]\n"
            "    else:\n"
            "        _cols = [f'sample{i+1}' for i in range(6)]\n"
            "    _n_genes = 100\n"
            "    _data = _rng.poisson(20, size=(_n_genes, len(_cols)))\n"
            "    return _fx_pd.DataFrame(_data, columns=_cols, index=[f'GENE{i}' for i in range(_n_genes)])\n"
            "\n"
            "_fx_pd.read_csv = _fx_make_df\n"
            "_fx_pd.read_table = _fx_make_df\n"
        )

    return "\n".join(lines)


def _build_shell_dry_run_preamble() -> str:
    """Python source injected before shell-orchestration code. Monkeypatches
    subprocess.run/Popen/call/check_call/check_output to no-op stubs that
    return a dummy success instead of actually invoking bwa/samtools/gatk/
    etc, then lets the real script execute. This exercises every loop,
    zip(), function call, and f-string in the generated code for real --
    exactly where the bugs found via live testing actually were (Python
    control-flow mistakes, not bioinformatics mistakes) -- without needing
    a real reference genome or real sequencing data.

    Best-effort: touches an empty placeholder file at whatever path
    follows -o/-O/--output in a mocked command, so code that checks
    os.path.exists(...) on a tool's output before proceeding doesn't
    false-positive. This is heuristic, not exhaustive -- it won't cover
    every tool's argument convention, and that's an accepted v1 limit."""
    return (
        "import subprocess as _fx_subprocess\n"
        "import os as _fx_os\n"
        "import shlex as _fx_shlex\n"
        "\n"
        "def _fx_touch_outputs(_fx_cmd):\n"
        "    if isinstance(_fx_cmd, (list, tuple)):\n"
        "        _fx_tokens = [str(_t) for _t in _fx_cmd]\n"
        "    else:\n"
        "        try:\n"
        "            _fx_tokens = _fx_shlex.split(str(_fx_cmd))\n"
        "        except Exception:\n"
        "            _fx_tokens = str(_fx_cmd).split()\n"
        "    for _fx_i, _fx_tok in enumerate(_fx_tokens):\n"
        "        if _fx_tok in ('-o', '-O', '--output') and _fx_i + 1 < len(_fx_tokens):\n"
        "            _fx_path = _fx_tokens[_fx_i + 1]\n"
        "            try:\n"
        "                _fx_dirname = _fx_os.path.dirname(_fx_path)\n"
        "                if _fx_dirname:\n"
        "                    _fx_os.makedirs(_fx_dirname, exist_ok=True)\n"
        "                with open(_fx_path, 'a'):\n"
        "                    pass\n"
        "            except Exception:\n"
        "                pass\n"
        "\n"
        "class _FxCompletedProcess:\n"
        "    def __init__(self, args):\n"
        "        self.args = args\n"
        "        self.returncode = 0\n"
        "        self.stdout = ''\n"
        "        self.stderr = ''\n"
        "    def check_returncode(self):\n"
        "        pass\n"
        "\n"
        "class _FxPopen:\n"
        "    def __init__(self, args):\n"
        "        self.args = args\n"
        "        self.returncode = 0\n"
        "        self.stdout = None\n"
        "        self.stderr = None\n"
        "        self.stdin = None\n"
        "    def communicate(self, *_fx_a, **_fx_k):\n"
        "        return (b'', b'')\n"
        "    def wait(self, *_fx_a, **_fx_k):\n"
        "        return 0\n"
        "    def poll(self):\n"
        "        return 0\n"
        "\n"
        "def _fx_mock_run(*_fx_args, **_fx_kwargs):\n"
        "    _fx_cmd = _fx_args[0] if _fx_args else _fx_kwargs.get('args')\n"
        "    _fx_touch_outputs(_fx_cmd)\n"
        "    return _FxCompletedProcess(_fx_cmd)\n"
        "\n"
        "def _fx_mock_check_output(*_fx_args, **_fx_kwargs):\n"
        "    _fx_cmd = _fx_args[0] if _fx_args else _fx_kwargs.get('args')\n"
        "    _fx_touch_outputs(_fx_cmd)\n"
        "    return b''\n"
        "\n"
        "def _fx_mock_popen(*_fx_args, **_fx_kwargs):\n"
        "    _fx_cmd = _fx_args[0] if _fx_args else _fx_kwargs.get('args')\n"
        "    _fx_touch_outputs(_fx_cmd)\n"
        "    return _FxPopen(_fx_cmd)\n"
        "\n"
        "_fx_subprocess.run = _fx_mock_run\n"
        "_fx_subprocess.Popen = _fx_mock_popen\n"
        "_fx_subprocess.call = lambda *_fx_a, **_fx_k: 0\n"
        "_fx_subprocess.check_call = lambda *_fx_a, **_fx_k: 0\n"
        "_fx_subprocess.check_output = _fx_mock_check_output\n"
    )

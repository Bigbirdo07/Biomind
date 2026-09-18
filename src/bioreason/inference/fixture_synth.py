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
way (raw open(), an unsupported format like .bam/.fastq/.vcf, or another
language entirely), execution verification is skipped for that block
rather than risking a misleading false-positive failure -- an execution
result that's wrong for the wrong reason is worse than not attempting
execution at all, since "the code was actually run" reads as more
authoritative than a heuristic warning.
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
# cannot safely fixture -- execution verification is skipped for the whole
# block, not flagged as a bug.
UNSUPPORTED_IO_MARKERS = [
    r"\bopen\s*\(",
    r"\.(bam|fastq|fq|vcf|sam)\b",
    r"\bRscript\b",
    r"^\s*library\s*\(",
]

H5AD_READER_CALLS = ("sc.read_10x_h5", "sc.read_h5ad", "anndata.read_h5ad", "ad.read_h5ad")
CSV_READER_CALLS = ("pd.read_csv", "pd.read_table")


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
    uses_h5ad_readers: bool = False
    uses_csv_readers: bool = False
    shape: Dict[str, Any] = field(default_factory=dict)


def build_fixture_plan(code: str, shape: Dict[str, Any]) -> FixturePlan:
    for pattern in UNSUPPORTED_IO_MARKERS:
        if re.search(pattern, code, re.MULTILINE):
            return FixturePlan(confidence="none", reason=f"unsupported I/O pattern: {pattern}", shape=shape)

    uses_h5ad = any(fn in code for fn in H5AD_READER_CALLS)
    uses_csv = any(fn in code for fn in CSV_READER_CALLS)

    if not uses_h5ad and not uses_csv:
        return FixturePlan(confidence="none", reason="no recognized file I/O found", shape=shape)

    return FixturePlan(
        confidence="high", reason="ok",
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

"""
tests/test_fixture_synth.py

Unit tests for bioreason.inference.fixture_synth -- offline, no GPU/model
needed.
"""

import pytest

from bioreason.inference.fixture_synth import (
    build_execution_preamble,
    build_fixture_plan,
    infer_dataset_shape,
)


def test_infer_shape_detects_h5ad_kind():
    shape = infer_dataset_shape(
        "I have single-cell RNA-seq data, filtered_feature_bc_matrix.h5 per sample.",
        [], None,
    )
    assert shape["kind"] == "h5ad"


def test_infer_shape_detects_count_matrix_kind():
    shape = infer_dataset_shape(
        "I have a bulk RNA-seq count matrix in a CSV file.",
        [], None,
    )
    assert shape["kind"] == "count_matrix"


def test_infer_shape_extracts_group_counts():
    shape = infer_dataset_shape(
        "I have 15 tumor and 15 normal samples, matched pairs.",
        [], None,
    )
    assert shape["group_counts"] == {"tumor": 15, "normal": 15}
    assert shape["sample_count"] == 30


def test_infer_shape_uses_history_and_summary():
    shape = infer_dataset_shape(
        "Please give me the code.",
        [{"role": "user", "content": "I ran single-cell RNA-seq, 6 healthy and 4 neoplastic animals."}],
        "input_type=h5ad",
    )
    assert shape["kind"] == "h5ad"
    assert shape["group_counts"] == {"healthy": 6, "neoplastic": 4}


def test_infer_shape_unknown_kind_when_no_signal():
    shape = infer_dataset_shape("hello, what can you do?", [], None)
    assert shape["kind"] == "unknown"
    assert shape["group_counts"] == {}


CODE_WITH_H5AD_READ = """
import scanpy as sc
adata = sc.read_10x_h5('filtered_feature_bc_matrix.h5')
"""

CODE_WITH_CSV_READ = """
import pandas as pd
counts = pd.read_csv('counts.csv')
"""

CODE_WITH_OPEN = """
with open('data.txt') as f:
    data = f.read()
"""

CODE_WITH_UNSUPPORTED_FORMAT = """
import pysam
bam = pysam.AlignmentFile('reads.bam')
"""

CODE_WITH_NO_IO = """
x = 1 + 1
print(x)
"""


def test_plan_high_confidence_for_h5ad_read():
    plan = build_fixture_plan(CODE_WITH_H5AD_READ, {"kind": "h5ad", "group_counts": {}})
    assert plan.confidence == "high"
    assert plan.uses_h5ad_readers is True
    assert plan.uses_csv_readers is False


def test_plan_high_confidence_for_csv_read():
    plan = build_fixture_plan(CODE_WITH_CSV_READ, {"kind": "count_matrix", "group_counts": {}})
    assert plan.confidence == "high"
    assert plan.uses_csv_readers is True


def test_plan_none_confidence_for_open():
    plan = build_fixture_plan(CODE_WITH_OPEN, {})
    assert plan.confidence == "none"


def test_plan_none_confidence_for_unsupported_format():
    plan = build_fixture_plan(CODE_WITH_UNSUPPORTED_FORMAT, {})
    assert plan.confidence == "none"


def test_plan_none_confidence_for_no_io():
    plan = build_fixture_plan(CODE_WITH_NO_IO, {})
    assert plan.confidence == "none"


anndata = pytest.importorskip("anndata")
pd = pytest.importorskip("pandas")


def _run_preamble_isolated(preamble: str, tail: str, namespace: dict):
    """Executes the preamble+tail in a subprocess, not in-process, so any
    monkeypatching it does (e.g. pandas.read_csv = ...) can never leak into
    this test session's shared sys.modules and corrupt unrelated tests --
    exactly the isolation reason code_sandbox.run_in_sandbox exists for the
    real execution-verification path. Returns the namespace dict populated
    via a small json handoff written to a temp file."""
    import json
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as workdir:
        script = (
            preamble + "\n" + tail + "\n"
            "import json as _fx_json\n"
            f"with open(r'{workdir}/_fx_result.json', 'w') as _fx_f:\n"
            "    _fx_json.dump(_fx_result_hook(), _fx_f)\n"
        )
        script_path = Path(workdir) / "_test_preamble.py"
        script_path.write_text(script)
        result = subprocess.run(
            [sys.executable, str(script_path)], cwd=workdir,
            capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == 0, result.stderr
        with open(Path(workdir) / "_fx_result.json") as f:
            return json.load(f)


def test_preamble_h5ad_monkeypatch_produces_loadable_adata():
    plan = build_fixture_plan(CODE_WITH_H5AD_READ, {"kind": "h5ad", "group_counts": {"healthy": 4, "sick": 6}})
    preamble = build_execution_preamble(plan)
    tail = (
        "adata = _fx_sc.read_10x_h5('anything.h5')\n"
        "def _fx_result_hook():\n"
        "    return {'n_obs': adata.n_obs, 'n_vars': adata.n_vars, 'columns': list(adata.obs.columns)}\n"
    )
    out = _run_preamble_isolated(preamble, tail, {})
    assert out["n_obs"] == 40
    assert out["n_vars"] == 200
    assert "condition" in out["columns"]


def test_preamble_csv_monkeypatch_produces_loadable_dataframe():
    plan = build_fixture_plan(CODE_WITH_CSV_READ, {"kind": "count_matrix", "group_counts": {"tumor": 3, "normal": 2}})
    preamble = build_execution_preamble(plan)
    tail = (
        "df = _fx_pd.read_csv('anything.csv')\n"
        "def _fx_result_hook():\n"
        "    return {'n_cols': df.shape[1], 'columns': list(df.columns)}\n"
    )
    out = _run_preamble_isolated(preamble, tail, {})
    assert out["n_cols"] == 5
    assert any(col.startswith("tumor_") for col in out["columns"])
    assert any(col.startswith("normal_") for col in out["columns"])


def test_preamble_empty_when_no_readers_used():
    plan = build_fixture_plan(CODE_WITH_NO_IO, {})
    # plan.confidence == "none" here, but build_execution_preamble should
    # still degrade gracefully (empty string) if ever called on a plan with
    # no reader flags set.
    assert build_execution_preamble(plan) == ""

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


# ---------------------------------------------------------------------------
# Shell dry-run path (WGS/WES-style subprocess-orchestration pipelines).
# Fixes the earlier "any .bam/.fastq/.vcf mention -> confidence=none" gap:
# these files are just string arguments to external tools in this kind of
# code, not parsed by a Python library that needs real content, so the
# right move is to mock the TOOL CALLS, not the data.
# ---------------------------------------------------------------------------

CODE_WITH_SUBPROCESS_AND_BAM = """
import subprocess
subprocess.run(f'bwa mem ref.fa in.fq | samtools sort -o out.bam', shell=True)
subprocess.run(['gatk', 'HaplotypeCaller', '-I', 'out.bam', '-O', 'out.vcf'])
"""

CODE_WITH_RAW_OPEN = """
with open('data.txt') as f:
    data = f.read()
"""

CODE_WITH_R = """
library(DESeq2)
dds <- DESeqDataSetFromMatrix(countData=countData, colData=colData, design=~condition)
"""


def test_subprocess_code_with_bam_gets_shell_dry_run_not_none():
    # Regression test for the earlier gap: .bam/.fastq/.vcf mentions used
    # to unconditionally bail out to confidence="none" even when the code
    # only references them as command-line arguments to external tools.
    plan = build_fixture_plan(CODE_WITH_SUBPROCESS_AND_BAM, {})
    assert plan.confidence == "high"
    assert plan.kind == "shell_dry_run"


def test_raw_open_still_unsupported_even_with_subprocess_present():
    code = CODE_WITH_SUBPROCESS_AND_BAM + "\nwith open('extra.txt') as f:\n    pass\n"
    plan = build_fixture_plan(code, {})
    assert plan.confidence == "none"


def test_r_code_still_unsupported():
    plan = build_fixture_plan(CODE_WITH_R, {})
    assert plan.confidence == "none"


def test_shell_dry_run_preamble_mocks_subprocess_and_runs_real_script():
    """Integration test: the exact zip() arity-mismatch bug found via live
    WGS/WES testing this session -- the loop unpacks 6 targets from a
    zip() of 3 lists (one of which, fastq_files, holds 4-tuples), which
    Python cannot do and raises ValueError the instant the script runs.
    No real BWA/GATK needed to catch this -- only real Python execution."""
    from pathlib import Path
    import tempfile
    from bioreason.inference.code_sandbox import run_in_sandbox

    code = (
        "import subprocess\n"
        "fastq_files = [\n"
        "    ('t1_R1.fq', 't1_R2.fq', 'n1_R1.fq', 'n1_R2.fq'),\n"
        "    ('t2_R1.fq', 't2_R2.fq', 'n2_R1.fq', 'n2_R2.fq'),\n"
        "]\n"
        "tumor_sample_names = ['tumor1', 'tumor2']\n"
        "normal_sample_names = ['normal1', 'normal2']\n"
        "for tumor_r1, tumor_r2, normal_r1, normal_r2, tumor_sample_name, normal_sample_name in zip(\n"
        "    fastq_files, tumor_sample_names, normal_sample_names\n"
        "):\n"
        "    subprocess.run(f'bwa mem ref.fa {tumor_r1} {tumor_r2} -o out.bam', shell=True)\n"
    )
    plan = build_fixture_plan(code, {})
    assert plan.kind == "shell_dry_run"
    preamble = build_execution_preamble(plan)
    full_source = preamble + "\n\n" + code

    with tempfile.TemporaryDirectory() as workdir:
        result = run_in_sandbox(full_source, Path(workdir))
    assert result.status == "EXCEPTION"
    assert "ValueError" in result.traceback_text


def test_shell_dry_run_preamble_runs_correct_script_cleanly():
    """A correctly-structured per-sample-function pipeline (the pattern
    the overlay now recommends) should run to completion under the mock
    with no real bwa/gatk installed."""
    from pathlib import Path
    import tempfile
    from bioreason.inference.code_sandbox import run_in_sandbox

    code = (
        "import subprocess\n"
        "samples = [\n"
        "    {'tumor_r1': 't1_R1.fq', 'tumor_r2': 't1_R2.fq', 'normal_r1': 'n1_R1.fq', "
        "'normal_r2': 'n1_R2.fq', 'tumor_bam': 't1.bam', 'normal_bam': 'n1.bam', "
        "'normal_sample_name': 'normal1'},\n"
        "    {'tumor_r1': 't2_R1.fq', 'tumor_r2': 't2_R2.fq', 'normal_r1': 'n2_R1.fq', "
        "'normal_r2': 'n2_R2.fq', 'tumor_bam': 't2.bam', 'normal_bam': 'n2.bam', "
        "'normal_sample_name': 'normal2'},\n"
        "]\n"
        "\n"
        "def process_sample(s):\n"
        "    subprocess.run(f\"bwa mem ref.fa {s['tumor_r1']} {s['tumor_r2']} | samtools sort -o {s['tumor_bam']}\", shell=True)\n"
        "    subprocess.run(f\"gatk Mutect2 -I {s['tumor_bam']} -I {s['normal_bam']} -normal {s['normal_sample_name']} -O out.vcf\", shell=True)\n"
        "\n"
        "for sample in samples:\n"
        "    process_sample(sample)\n"
        "print('done')\n"
    )
    plan = build_fixture_plan(code, {})
    preamble = build_execution_preamble(plan)
    full_source = preamble + "\n\n" + code

    with tempfile.TemporaryDirectory() as workdir:
        result = run_in_sandbox(full_source, Path(workdir))
    assert result.status == "OK", result.stderr


def test_shell_dry_run_catches_missing_shell_true_on_plain_string_command():
    """Seen live: subprocess.run(f'gatk BaseRecalibrator -R ... -O ...')
    with no shell=True and no pipe -- easy to miss since it's not the
    pipe-character bug code_lint already catches. Without shell=True, a
    plain multi-word STRING command is run as a single literal executable
    name (no argument splitting), which real Python raises
    FileNotFoundError for -- the mock must replicate this, not silently
    accept it, since it's exactly the class of bug this layer exists for."""
    from pathlib import Path
    import tempfile
    from bioreason.inference.code_sandbox import run_in_sandbox

    code = (
        "import subprocess\n"
        "subprocess.run(f'gatk BaseRecalibrator -R ref.fa -I in.bam -O out.table')\n"
    )
    plan = build_fixture_plan(code, {})
    preamble = build_execution_preamble(plan)
    full_source = preamble + "\n\n" + code

    with tempfile.TemporaryDirectory() as workdir:
        result = run_in_sandbox(full_source, Path(workdir))
    assert result.status == "EXCEPTION"
    assert "FileNotFoundError" in result.traceback_text


def test_shell_dry_run_touches_output_placeholder_for_o_flag():
    """A script that checks os.path.exists() on a tool's -o output before
    proceeding shouldn't false-positive just because no real tool ran."""
    from pathlib import Path
    import tempfile
    from bioreason.inference.code_sandbox import run_in_sandbox

    code = (
        "import subprocess, os\n"
        "subprocess.run(['samtools', 'sort', 'in.bam', '-o', 'sorted.bam'])\n"
        "assert os.path.exists('sorted.bam'), 'expected samtools output to exist'\n"
        "print('ok')\n"
    )
    plan = build_fixture_plan(code, {})
    preamble = build_execution_preamble(plan)
    full_source = preamble + "\n\n" + code

    with tempfile.TemporaryDirectory() as workdir:
        result = run_in_sandbox(full_source, Path(workdir))
    assert result.status == "OK", result.stderr

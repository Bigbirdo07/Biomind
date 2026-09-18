"""
tests/test_code_lint.py

Unit tests for bioreason.inference.code_lint against the exact broken code
patterns observed during live testing of BR-VERIFIED-SFT-002's
PIPELINE_BUILD mode, plus positive controls that must NOT be flagged.
"""

from bioreason.inference.code_lint import lint_generated_code


def wrap(code: str) -> str:
    return f"Here is the code.\n\n```python\n{code}\n```\n\nExplanation follows."


def test_flags_anndata_groupby_misuse():
    code = wrap(
        "pseudobulk_adata = sc.AnnData()\n"
        "pseudobulk_adata = pseudobulk_adata.concatenate(adata)\n"
        "pseudobulk_adata = pseudobulk_adata.groupby('animal').mean()\n"
    )
    warnings = lint_generated_code(code)
    assert any("groupby() directly on what" in w for w in warnings)


def test_does_not_flag_correct_obs_groupby():
    code = wrap(
        "grouped = adata.obs.groupby('animal')['total_counts'].sum()\n"
    )
    warnings = lint_generated_code(code)
    assert not any("groupby() directly on what" in w for w in warnings)


def test_flags_qc_column_used_without_computation():
    code = wrap(
        "sc.pp.regress_out(adata, ['total_counts', 'pct_counts_mt'])\n"
    )
    warnings = lint_generated_code(code)
    assert any("pct_counts_mt" in w and "calculate_qc_metrics" in w for w in warnings)


def test_does_not_flag_qc_column_after_calculate_qc_metrics():
    code = wrap(
        "sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)\n"
        "sc.pp.regress_out(adata, ['total_counts', 'pct_counts_mt'])\n"
    )
    warnings = lint_generated_code(code)
    assert not any("pct_counts_mt" in w for w in warnings)


def test_flags_pseudobulk_with_no_reduction_at_all():
    # Seen live: concatenate-only "pseudobulk" that never actually
    # aggregates cells into subject-level rows.
    code = wrap(
        "# Aggregate cells by animal\n"
        "pseudobulk_adata = sc.AnnData()\n"
        "for animal in metadata['animal'].unique():\n"
        "    animal_adata = adata[adata.obs['sample'] == animal, :]\n"
        "    pseudobulk_adata = pseudobulk_adata.concatenate(animal_adata)\n"
    )
    warnings = lint_generated_code(code)
    assert any("no reduction operation" in w for w in warnings)


def test_flags_pseudobulk_collapsing_across_all_subjects():
    # Seen live: pseudobulk_adata.X.sum(axis=0) collapses the ENTIRE
    # dataset into one row instead of one row per subject.
    code = wrap(
        "# Perform pseudobulk aggregation\n"
        "pseudobulk_adata = adata.copy()\n"
        "pseudobulk_adata.X = pseudobulk_adata.X.sum(axis=0)\n"
        "pseudobulk_adata.obs = pseudobulk_adata.obs.groupby('condition').first()\n"
    )
    warnings = lint_generated_code(code)
    assert any("does not clearly group by a per-subject" in w for w in warnings)


def test_does_not_flag_correct_pseudobulk_pattern():
    code = wrap(
        "# Aggregate raw counts per animal to form pseudobulk profiles\n"
        "rows = []\n"
        "for animal_id, group in adata.obs.groupby('animal'):\n"
        "    cell_idx = group.index\n"
        "    summed = adata[cell_idx].X.sum(axis=0)\n"
        "    rows.append(summed)\n"
    )
    warnings = lint_generated_code(code)
    assert warnings == []


def test_no_warnings_for_code_without_any_flagged_pattern():
    code = wrap(
        "dds <- DESeqDataSetFromMatrix(countData=countData, colData=sampleInfo, design=~condition)\n"
        "dds <- DESeq(dds)\n"
        "res <- results(dds)\n"
    )
    warnings = lint_generated_code(code)
    assert warnings == []


def test_no_code_blocks_returns_no_warnings():
    assert lint_generated_code("Just a plain conversational reply, no code here.") == []


def test_flags_umap_plot_without_umap_computed():
    # Seen live: sc.pl.umap(...) called with no sc.tl.umap(adata) anywhere
    # in the code -- adata.obsm['X_umap'] would not exist, KeyError.
    code = wrap(
        "sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)\n"
        "sc.tl.leiden(adata)\n"
        "sc.pl.umap(adata, color='condition')\n"
    )
    warnings = lint_generated_code(code)
    assert any("sc.pl.umap" in w and "KeyError" in w for w in warnings)


def test_does_not_flag_umap_plot_after_umap_computed():
    code = wrap(
        "sc.tl.umap(adata)\n"
        "sc.pl.umap(adata, color='condition')\n"
    )
    warnings = lint_generated_code(code)
    assert not any("sc.pl.umap" in w for w in warnings)


def test_does_not_flag_decoupler_get_pseudobulk():
    # Seen live: switching to decoupler.get_pseudobulk (a real, tested
    # aggregation function) after the earlier overlay fix -- this performs
    # correct per-subject reduction internally and must not be flagged just
    # because there's no literal .sum(axis=0) or .obs.groupby(...) in this
    # code block.
    code = wrap(
        "from decoupler import get_pseudobulk\n"
        "pseudobulk_adata = get_pseudobulk(\n"
        "    adata_list=[sc.read_h5ad(f'{a}_processed.h5ad') for a in metadata['animal'].unique()],\n"
        "    by=['animal', 'condition', 'stage'],\n"
        "    func='sum'\n"
        ")\n"
    )
    warnings = lint_generated_code(code)
    assert warnings == []


def test_does_not_flag_scanpy_get_aggregate():
    code = wrap(
        "pseudobulk_adata = sc.get.aggregate(adata, by=['animal', 'condition'], func='sum')\n"
    )
    warnings = lint_generated_code(code)
    assert warnings == []


def test_does_not_flag_metadata_groupby():
    # Regression test: metadata.groupby(...) is an extremely common,
    # completely correct pandas operation in this exact domain (grouping a
    # metadata table by sample/animal). A naive substring search for
    # "adata" inside variable names incorrectly matches inside "metadata"
    # -- found live and must never regress.
    code = wrap(
        "metadata = pd.read_csv('metadata.csv')\n"
        "for animal, group in metadata.groupby('animal'):\n"
        "    pass\n"
    )
    warnings = lint_generated_code(code)
    assert warnings == []


def test_does_not_flag_groupby_mean_chain_as_missing_reduction():
    # Seen live: a PIPELINE_DEBUG fix that converts a .X slice to a real
    # pandas DataFrame first, then does `.groupby(idx).mean()` -- this is a
    # genuinely correct reduction pattern (pandas reduces within each
    # group, no axis=0 argument needed) and must not be flagged as "no
    # reduction operation present".
    code = wrap(
        "pseudobulk_data = adata.X[adata.obs['animal'].index].copy()\n"
        "pseudobulk_data = pd.DataFrame(pseudobulk_data, index=adata.obs['animal'])\n"
        "pseudobulk_data = pseudobulk_data.groupby(pseudobulk_data.index).mean()\n"
    )
    warnings = lint_generated_code(code)
    assert not any("no reduction operation" in w for w in warnings)
    assert not any("does not clearly group by a per-subject" in w for w in warnings)


def test_flags_groupby_on_anndata_X_slice():
    # Seen live in a PIPELINE_DEBUG "fix" for the direct .groupby() bug --
    # this disguises the identical mistake by slicing .X first, but a numpy
    # array / scipy sparse matrix slice still has no .groupby() method.
    code = wrap(
        "pseudobulk_data = adata.X[adata.obs['animal'].index].groupby(adata.obs['animal']).mean()\n"
    )
    warnings = lint_generated_code(code)
    assert any("slice of an AnnData object's .X matrix" in w for w in warnings)


def test_flags_subprocess_pipe_without_shell_true():
    # Seen live in a generated WGS variant-calling pipeline: subprocess.run
    # given a list of arguments including '|' between bwa mem and samtools
    # -- subprocess never interprets shell metacharacters when given a
    # list, so '|' is passed as a literal (meaningless) argument.
    code = wrap(
        "subprocess.run([\n"
        "    'bwa', 'mem', '-t', '8', reference_genome, fastq,\n"
        "    '|', 'samtools', 'view', '-bS', '-',\n"
        "    '|', 'samtools', 'sort', '-o', alignment_output\n"
        "], check=True)\n"
    )
    warnings = lint_generated_code(code)
    assert any("literal '|'" in w for w in warnings)


def test_does_not_flag_subprocess_with_shell_true():
    code = wrap(
        "subprocess.run('bwa mem ref.fa in.fq | samtools sort -o out.bam', shell=True)\n"
    )
    warnings = lint_generated_code(code)
    assert not any("literal '|'" in w for w in warnings)


def test_does_not_flag_subprocess_without_pipe():
    code = wrap(
        "subprocess.run(['samtools', 'index', 'aligned.bam'], check=True)\n"
    )
    warnings = lint_generated_code(code)
    assert not any("literal '|'" in w for w in warnings)


def test_flags_subprocess_popen_pipe_too():
    code = wrap(
        "proc = subprocess.Popen(['gatk', 'HaplotypeCaller', '|', 'tee', 'log.txt'])\n"
    )
    warnings = lint_generated_code(code)
    assert any("literal '|'" in w for w in warnings)


def test_flags_shell_true_with_list_argument():
    # Seen live: shell=True added to "fix" the pipe warning, but the
    # command was left as a list -- only args[0] runs as the actual shell
    # command with shell=True; the rest become positional shell params,
    # not part of the command line. Still broken, just differently.
    code = wrap(
        "subprocess.run(['bwa', 'mem', ref, r1, r2, '|', 'samtools', 'sort', "
        "'-o', out_bam], shell=True)\n"
    )
    warnings = lint_generated_code(code)
    assert any("shell=True together with a LIST" in w for w in warnings)


def test_does_not_flag_shell_true_with_string_argument():
    code = wrap(
        "subprocess.run('bwa mem ref.fa in.fq | samtools sort -o out.bam', shell=True)\n"
    )
    warnings = lint_generated_code(code)
    assert not any("shell=True together with a LIST" in w for w in warnings)


def test_flags_self_referential_subscript_reassignment():
    # Seen live in a WGS pipeline: tumor_bai = tumor_bai[i] inside a loop
    # over 12 samples -- silently broke every sample after the first.
    code = wrap(
        "tumor_bai = ['a.bai', 'b.bai', 'c.bai']\n"
        "for i in range(3):\n"
        "    tumor_bai = tumor_bai[i]\n"
        "    print(tumor_bai)\n"
    )
    warnings = lint_generated_code(code)
    assert any("reassigns 'tumor_bai' to one of its own elements" in w for w in warnings)


def test_does_not_flag_normal_indexing_into_different_variable():
    code = wrap(
        "tumor_bai = ['a.bai', 'b.bai', 'c.bai']\n"
        "for i in range(3):\n"
        "    current_bai = tumor_bai[i]\n"
        "    print(current_bai)\n"
    )
    warnings = lint_generated_code(code)
    assert not any("reassigns" in w for w in warnings)

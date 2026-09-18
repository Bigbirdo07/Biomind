"""
Deterministic static checks for generated pipeline code.

These catch structural code-generation failure patterns found via live
testing of BR-VERIFIED-SFT-002's PIPELINE_BUILD mode that prompt-engineering
alone could not reliably prevent: the model writing code that *looks*
correct (right variable names, right library calls, comments that describe
the right operation) but is structurally broken or silently does something
different from what it claims. This is not a substitute for real code
review -- it is a narrow, cheap check for the specific patterns observed to
recur across many live generations, used to trigger one corrective
regeneration pass or an honest caveat rather than silently shipping code
that would crash or silently produce wrong science.
"""

from __future__ import annotations

import re
from typing import List

CODE_FENCE_RE = re.compile(r"```(?:python|r)?\n(.*?)```", re.DOTALL)

# sc.pp.calculate_qc_metrics is what actually computes these .obs columns;
# referencing them without that call raises a KeyError at runtime -- seen
# live in generated code (pct_counts_mt referenced in sc.pp.regress_out
# without ever being computed).
QC_DERIVED_COLUMNS = ["pct_counts_mt", "pct_counts_ribo", "total_counts", "n_genes_by_counts"]

SUBJECT_KEY_HINTS = ["animal", "patient", "subject", "sample", "mouse", "donor"]


def extract_code_blocks(text: str) -> List[str]:
    return CODE_FENCE_RE.findall(text)


def lint_code_block(code: str) -> List[str]:
    warnings: List[str] = []

    # 1. AnnData has no .groupby() method (that's pandas-only) -- calling it
    # directly on an AnnData-named variable (not adata.obs) raises
    # AttributeError. Seen live: `pseudobulk_adata.groupby('animal').mean()`.
    # Match "adata" only as a real token boundary (a bare "adata..." prefix,
    # or an "..._adata..." suffix joined by underscore) -- a naive substring
    # search also matches inside "metadata", which is an extremely common
    # and completely correct pandas variable name in this exact domain
    # (found and fixed as a live false-positive bug during testing).
    ANNDATA_VAR = r"\b(?:adata\w*|\w*_adata\w*)\b"
    for match in re.finditer(ANNDATA_VAR + r"\.groupby\(", code, re.IGNORECASE):
        warnings.append(
            f"'{match.group(0)[:-1]}...)' calls .groupby() directly on what looks "
            "like an AnnData object -- AnnData has no .groupby() method (that's a "
            "pandas DataFrame method). This will raise AttributeError unless it's "
            "actually adata.obs.groupby(...)."
        )

    # 1b. The same underlying mistake, disguised: .groupby() called on a
    # slice/index of an AnnData object's .X matrix. Seen live in a
    # PIPELINE_DEBUG "fix" for the bug above:
    # `adata.X[adata.obs['animal'].index].groupby(adata.obs['animal']).mean()`
    # -- neither a numpy array nor a scipy sparse matrix (what .X slicing
    # returns) has a .groupby() method either; only adata.obs (a real pandas
    # DataFrame) does.
    for match in re.finditer(r"\.groupby\(", code):
        start = match.start()
        immediate = code[max(0, start - 8):start]
        if immediate.endswith(".obs"):
            continue  # the safe, correct pattern
        window = code[max(0, start - 100):start]
        if re.search(ANNDATA_VAR + r"\.X\b", window):
            warnings.append(
                "'.groupby(...)' is called on what looks like a slice of an AnnData "
                "object's .X matrix -- neither a numpy array nor a scipy sparse "
                "matrix has a .groupby() method (that's pandas-only, and only "
                "adata.obs is a real DataFrame here). This will raise AttributeError."
            )

    # 2. QC-derived .obs columns referenced without being computed first.
    # Seen live: pct_counts_mt used in sc.pp.regress_out with no preceding
    # sc.pp.calculate_qc_metrics call.
    has_qc_metrics_call = "calculate_qc_metrics" in code
    for col in QC_DERIVED_COLUMNS:
        if col in code and not has_qc_metrics_call:
            warnings.append(
                f"'{col}' is referenced but sc.pp.calculate_qc_metrics(...) is never "
                "called in this code -- that column would not exist yet, causing a "
                "KeyError at runtime."
            )

    # 3. Pseudobulk aggregation that collapses across ALL rows instead of
    # per-subject. Seen live in two different broken forms: concatenate()
    # with no reduction at all, and .sum(axis=0)/.mean(axis=0) applied to
    # the whole matrix with no per-subject groupby, collapsing every
    # subject into a single row.
    if "pseudobulk" in code.lower():
        # A real aggregation function (decoupler.get_pseudobulk, scanpy's
        # sc.get.aggregate) does the reduction internally and correctly --
        # calling one of these IS the reduction, even without a literal
        # .sum(axis=0)/.mean(axis=0) or .obs.groupby(...) in this code
        # block, so neither check below should fire a false positive on it.
        uses_verified_aggregation_function = re.search(
            r"\b(get_pseudobulk|sc\.get\.aggregate)\s*\(", code
        )
        # A raw-matrix reduction (.sum(axis=0)/.mean(axis=0)) is one valid
        # form of aggregation; a pandas .groupby(...).sum()/.mean() chain
        # (no axis argument needed -- pandas reduces within each group) is
        # an equally valid, and equally common, form. Seen live: converting
        # a .X slice to a DataFrame, then `.groupby(idx).mean()`.
        has_groupby_reduction = re.search(r"\.groupby\([^)]*\)(?:\.\w+\([^)]*\))*\.(sum|mean)\(\)", code)
        has_reduction = (
            uses_verified_aggregation_function
            or has_groupby_reduction
            or re.search(r"\.(sum|mean)\(axis=0\)", code)
        )
        has_subject_groupby = (
            uses_verified_aggregation_function
            or has_groupby_reduction
            or re.search(
                r"\.obs\.groupby\(\s*['\"](" + "|".join(SUBJECT_KEY_HINTS) + r")",
                code, re.IGNORECASE,
            )
        )
        if not has_reduction:
            warnings.append(
                "Code claims to perform pseudobulk aggregation but no reduction "
                "operation (e.g. .sum(axis=0) or .mean(axis=0) per subject) is "
                "present -- concatenation alone does not aggregate cells into "
                "subject-level rows."
            )
        elif not has_subject_groupby:
            warnings.append(
                "Code claims to perform pseudobulk aggregation and does reduce with "
                "sum/mean, but does not clearly group by a per-subject/per-sample "
                "key first -- this risks collapsing all cells (or all subjects) into "
                "far fewer rows than subjects, which would either crash on a shape "
                "mismatch or leave too few replicates for any statistical test."
            )

    # 4. Plotting an embedding that was never computed. sc.pl.umap(...)
    # reads adata.obsm['X_umap'], which only exists after sc.tl.umap(adata)
    # has actually been run; sc.pl.tsne(...) needs sc.tl.tsne(adata)
    # likewise. Seen live: sc.pl.umap(...) called with no preceding
    # sc.tl.umap(...) anywhere in the code -- this raises a KeyError.
    for plot_fn, compute_fn, embedding in (
        ("sc.pl.umap", "sc.tl.umap", "UMAP"),
        ("sc.pl.tsne", "sc.tl.tsne", "t-SNE"),
    ):
        if plot_fn in code and compute_fn not in code:
            warnings.append(
                f"'{plot_fn}(...)' is called but '{compute_fn}(adata)' is never run "
                f"in this code -- the {embedding} embedding would not exist yet "
                "(adata.obsm has no entry for it), causing a KeyError at runtime."
            )

    # 5. subprocess.run/Popen/call/check_call/check_output given a shell
    # pipe character as a literal list argument, without shell=True.
    # subprocess with a list of arguments (the safe, recommended form)
    # NEVER interprets shell metacharacters like '|' -- it passes '|' as a
    # literal argument to the first command, which errors or silently does
    # nothing useful. This is a general Python-mechanics bug, not specific
    # to any one domain -- seen live in a generated WGS variant-calling
    # pipeline chaining `bwa mem | samtools view | samtools sort` this way.
    # The fix is either shell=True with a single command string, or
    # separate Popen calls manually chaining stdout=PIPE between them.
    for match in re.finditer(
        r"\bsubprocess\.(run|Popen|call|check_call|check_output)\s*\(", code
    ):
        call_text = _extract_balanced_parens(code, match.end() - 1)
        has_pipe_literal = re.search(r"""['"]\s*\|\s*['"]""", call_text)
        uses_shell_true = re.search(r"shell\s*=\s*True", call_text)
        # A second, distinct way to get this wrong: shell=True combined
        # with a LIST as the first argument. Python only runs args[0] as
        # the actual shell command in that case -- every other list item
        # becomes a positional shell parameter ($0, $1, ...), never
        # appended to the command line. Seen live: shell=True added to
        # silence the "missing shell=True" case above, but the list wasn't
        # converted to a single command string, so it's still broken.
        starts_with_list = re.match(r"\(\s*\[", call_text)
        if has_pipe_literal and not uses_shell_true:
            warnings.append(
                f"'subprocess.{match.group(1)}(...)' is called with a list of "
                "arguments that includes a literal '|' -- subprocess never "
                "interprets shell metacharacters like pipes when given a list "
                "(only when shell=True is set with a single command string, or "
                "separate calls are chained manually via stdout=subprocess.PIPE). "
                "As written, '|' is passed as a literal argument to the command "
                "and this will error or silently fail."
            )
        elif uses_shell_true and starts_with_list:
            warnings.append(
                f"'subprocess.{match.group(1)}(...)' passes shell=True together "
                "with a LIST as the command argument -- with shell=True, only "
                "the first list item is actually run as the shell command; every "
                "other item becomes a positional parameter to the shell itself, "
                "never appended to the command line. shell=True requires a "
                "single command STRING (e.g. 'bwa mem ref.fa in.fq | samtools "
                "sort -o out.bam'), not a list."
            )

    return warnings


def _extract_balanced_parens(code: str, open_paren_idx: int) -> str:
    """Returns the substring from an opening '(' to its matching ')',
    by simple bracket-depth counting (does not account for parens inside
    string literals -- acceptable for this heuristic-level check)."""
    depth = 0
    for i in range(open_paren_idx, len(code)):
        if code[i] == "(":
            depth += 1
        elif code[i] == ")":
            depth -= 1
            if depth == 0:
                return code[open_paren_idx:i + 1]
    return code[open_paren_idx:]


def lint_generated_code(response_text: str) -> List[str]:
    """Run static checks over every code block in a generated response.
    Returns a flat list of plain-language warnings (empty if nothing found).
    """
    warnings: List[str] = []
    for block in extract_code_blocks(response_text):
        warnings.extend(lint_code_block(block))
    return warnings

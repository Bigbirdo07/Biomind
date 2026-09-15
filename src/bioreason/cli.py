"""
Command-line interface for the BioReason platform (Phase 1).
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import click

from bioreason.schemas.episode import ScientificReasoningEpisode, ValidationStatus, EpisodeType
from bioreason.schemas.experiment import ExperimentSpec
from bioreason.schemas.workflow import WorkflowPlan
from bioreason.schemas.benchmark import BenchmarkItem, DifficultyLevel, BenchmarkCategory
from bioreason.datasets.loader import (
    load_episode,
    load_experiment_spec,
    load_workflow_plan,
    load_benchmark_item,
    load_benchmark_from_dir,
    load_episodes_from_dir,
)
from bioreason.validators.validators import (
    validate_episode_file,
    validate_experiment_file,
    validate_workflow_file,
)
from bioreason.rules.base import RuleSeverity
from bioreason.datasets.contamination import check_contamination
from bioreason.evaluation.harness import BioReasonEvaluationHarness
from bioreason.evaluation.rubric import ScientificRubricScorer
from bioreason.models.mock_adapter import MockModelAdapter
from bioreason.training.config import TrainingConfig
from bioreason.training.sft_trainer import ScientificSFTTrainer


@click.group()
@click.version_option(version="0.1.0", prog_name="bioreason")
def cli():
    """BioReason: Biology-Native Scientific Reasoning Computational Platform."""
    pass


@cli.command("validate-episode")
@click.argument("file_path", type=click.Path(exists=True))
def validate_episode_cmd(file_path):
    """Validate a scientific reasoning episode against schema and deterministic scientific rules."""
    click.echo(f"Validating scientific reasoning episode: {file_path}")
    try:
        is_valid, episode, rule_results = validate_episode_file(file_path)
    except Exception as e:
        click.secho(f"Schema Validation ERROR: {e}", fg="red", err=True)
        sys.exit(1)

    click.secho(f"✓ Schema validation passed: {episode.episode_id} ({episode.domain})", fg="green")
    
    has_errors = False
    for res in rule_results:
        if not res.passed:
            color = "red" if res.severity == RuleSeverity.ERROR else "yellow"
            click.secho(f"[{res.severity.value}] {res.rule_id} ({res.rule_name}): {res.message}", fg=color)
            click.echo(f"  Explanation: {res.explanation}")
            if res.suggested_correction:
                click.echo(f"  Suggested Correction: {res.suggested_correction}")
            if res.severity == RuleSeverity.ERROR:
                has_errors = True
        else:
            click.secho(f"[PASS] {res.rule_id} ({res.rule_name})", fg="green")

    if has_errors:
        click.secho("\nValidation FAILED due to scientific rule errors.", fg="red")
        sys.exit(1)
    else:
        click.secho("\nAll scientific validation checks PASSED.", fg="green")


@cli.command("validate-experiment")
@click.argument("file_path", type=click.Path(exists=True))
def validate_experiment_cmd(file_path):
    """Validate an experiment design specification against schema and rule engine."""
    click.echo(f"Validating experiment specification: {file_path}")
    try:
        is_valid, experiment, rule_results = validate_experiment_file(file_path)
    except Exception as e:
        click.secho(f"Schema Validation ERROR: {e}", fg="red", err=True)
        sys.exit(1)

    click.secho(f"✓ Schema validation passed: {experiment.organism} ({experiment.assay.value})", fg="green")
    
    has_errors = False
    for res in rule_results:
        if not res.passed:
            color = "red" if res.severity == RuleSeverity.ERROR else "yellow"
            click.secho(f"[{res.severity.value}] {res.rule_id} ({res.rule_name}): {res.message}", fg=color)
            click.echo(f"  Explanation: {res.explanation}")
            if res.suggested_correction:
                click.echo(f"  Suggested Correction: {res.suggested_correction}")
            if res.severity == RuleSeverity.ERROR:
                has_errors = True
        else:
            click.secho(f"[PASS] {res.rule_id} ({res.rule_name})", fg="green")

    if has_errors:
        click.secho("\nValidation FAILED due to scientific design errors.", fg="red")
        sys.exit(1)
    else:
        click.secho("\nExperiment design PASSED all scientific checks.", fg="green")


@cli.command("validate-workflow")
@click.argument("file_path", type=click.Path(exists=True))
def validate_workflow_cmd(file_path):
    """Validate a computational workflow plan against schema and leakage/statistical rules."""
    click.echo(f"Validating workflow plan: {file_path}")
    try:
        is_valid, workflow, rule_results = validate_workflow_file(file_path)
    except Exception as e:
        click.secho(f"Schema Validation ERROR: {e}", fg="red", err=True)
        sys.exit(1)

    click.secho(f"✓ Schema validation passed: {workflow.workflow_id} ({workflow.target})", fg="green")
    
    has_errors = False
    for res in rule_results:
        if not res.passed:
            color = "red" if res.severity == RuleSeverity.ERROR else "yellow"
            click.secho(f"[{res.severity.value}] {res.rule_id} ({res.rule_name}): {res.message}", fg=color)
            click.echo(f"  Explanation: {res.explanation}")
            if res.suggested_correction:
                click.echo(f"  Suggested Correction: {res.suggested_correction}")
            if res.severity == RuleSeverity.ERROR:
                has_errors = True
        else:
            click.secho(f"[PASS] {res.rule_id} ({res.rule_name})", fg="green")

    if has_errors:
        click.secho("\nWorkflow validation FAILED due to methodological violations.", fg="red")
        sys.exit(1)
    else:
        click.secho("\nWorkflow plan PASSED all scientific validation rules.", fg="green")


@cli.command("evaluate")
@click.argument("target_path", type=click.Path(exists=True))
@click.option("--adapter", type=click.Choice(["mock", "hf"]), default="mock", help="Model adapter to run.")
@click.option("--model-path", type=str, default="meta-llama/Meta-Llama-3-8B-Instruct", help="HF model name/path.")
@click.option("--output", "-o", type=click.Path(), default="evaluation_results.json", help="Output results file.")
def evaluate_cmd(target_path, adapter, model_path, output):
    """Evaluate benchmark items using scientific rubrics and a model adapter."""
    click.echo(f"Running BioReason Evaluation on: {target_path} (adapter: {adapter})")
    
    path = Path(target_path)
    if path.is_file():
        items = [load_benchmark_item(path)]
    else:
        items = load_benchmark_from_dir(path)

    if not items:
        click.secho(f"No benchmark items found in {target_path}", fg="red")
        sys.exit(1)

    click.echo(f"Loaded {len(items)} benchmark item(s). Initializing adapter...")

    if adapter == "mock":
        model_adapter = MockModelAdapter(mode="oracle")
    else:
        from bioreason.models.hf_adapter import HuggingFaceModelAdapter
        model_adapter = HuggingFaceModelAdapter(model_name_or_path=model_path)

    harness = BioReasonEvaluationHarness(adapter=model_adapter)
    results = harness.evaluate_benchmark(items)

    agg = results["aggregate_metrics"]
    click.echo("\n--- EVALUATION SUMMARY ---")
    click.echo(f"Items Evaluated:         {agg['total_items']}")
    click.echo(f"Flaw Detection Accuracy: {agg['flaw_detection_accuracy'] * 100:.1f}%")
    click.echo(f"Critical Failure Rate:   {agg.get('critical_failure_rate', 0.0) * 100:.1f}%")
    click.echo(f"Mean Composite Score:    {agg['mean_composite_score']:.3f}")
    click.echo(f"Mean Flaw Detection:     {agg['mean_flaw_detection_score']:.3f}")
    click.echo(f"Mean Explanation:        {agg['mean_explanation_score']:.3f}")
    click.echo(f"Mean Correction Quality: {agg['mean_correction_score']:.3f}")
    click.echo(f"Mean Calibration:        {agg['mean_calibration_score']:.3f}")
    click.echo(f"Mean Interpretation:     {agg['mean_interpretation_score']:.3f}")

    if agg.get("by_difficulty"):
        click.echo("\n--- BY DIFFICULTY ---")
        for diff, stats in agg["by_difficulty"].items():
            click.echo(f"  {diff:<14}: N={stats['count']:<3} Composite={stats['mean_composite']:.3f} CritFail={stats['critical_failure_rate']*100:.1f}%")

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    click.secho(f"\nDetailed evaluation results written to: {output}", fg="green")


@cli.command("check-contamination")
@click.argument("train_dir", type=click.Path(exists=True))
@click.argument("benchmark_dir", type=click.Path(exists=True))
@click.option("--threshold", type=float, default=0.65, help="Jaccard token similarity threshold.")
def check_contamination_cmd(train_dir, benchmark_dir, threshold):
    """Check for data contamination / scenario overlap between training episodes and benchmark items."""
    click.echo(f"Checking data contamination between:\n  Train: {train_dir}\n  Benchmark: {benchmark_dir}")
    train_episodes = load_episodes_from_dir(train_dir)
    bench_items = load_benchmark_from_dir(benchmark_dir)

    click.echo(f"Loaded {len(train_episodes)} training episode(s) and {len(bench_items)} benchmark item(s).")
    reports = check_contamination(train_episodes, bench_items, similarity_threshold=threshold)

    if reports:
        click.secho(f"\n[WARNING] Found {len(reports)} potential contamination / overlap issue(s):", fg="red")
        for r in reports:
            click.secho(f"  - [{r['contamination_type']}] {r['message']}", fg="yellow")
        sys.exit(1)
    else:
        click.secho("\n✓ No benchmark contamination or overlap detected. Datasets are strictly separated.", fg="green")


@cli.command("dataset-audit")
@click.argument("train_dir", type=click.Path(exists=True), default="training_data/examples")
@click.argument("bench_dir", type=click.Path(exists=True), default="benchmark/examples")
@click.option("--output", "-o", type=click.Path(), default="BIOREASON_DATASET_AUDIT.md", help="Output audit report file.")
def dataset_audit_cmd(train_dir, bench_dir, output):
    """Generate comprehensive dataset and benchmark audit report."""
    train_episodes = load_episodes_from_dir(train_dir)
    bench_items = load_benchmark_from_dir(bench_dir)
    reports = check_contamination(train_episodes, bench_items)

    # Calculate distributions
    train_domains: Dict[str, int] = {}
    train_types: Dict[str, int] = {}
    train_status: Dict[str, int] = {}
    for ep in train_episodes:
        train_domains[ep.domain] = train_domains.get(ep.domain, 0) + 1
        ep_type = ep.episode_type.value if ep.episode_type else "FLAWED_WORKFLOW"
        train_types[ep_type] = train_types.get(ep_type, 0) + 1
        train_status[ep.validation_status.value] = train_status.get(ep.validation_status.value, 0) + 1

    bench_categories: Dict[str, int] = {}
    bench_diffs: Dict[str, int] = {}
    for item in bench_items:
        bench_categories[item.category.value] = bench_categories.get(item.category.value, 0) + 1
        bench_diffs[item.difficulty.value] = bench_diffs.get(item.difficulty.value, 0) + 1

    report_md = f"""# BioReason Dataset & Benchmark Audit Report

## 1. Executive Summary
- **Total Training Episodes**: {len(train_episodes)}
- **Total Benchmark Items**: {len(bench_items)}
- **Contamination / Collision Violations**: {len(reports)}
- **Contamination Status**: {'PASSED (Zero Overlap)' if len(reports) == 0 else 'FAILED'}

---

## 2. Training Dataset Composition (BioReasonTrain)
### Domain Breakdown:
"""
    for d, c in sorted(train_domains.items()):
        report_md += f"- **{d}**: {c}\n"

    report_md += "\n### Episode Type Breakdown:\n"
    for t, c in sorted(train_types.items()):
        report_md += f"- **{t}**: {c}\n"

    report_md += "\n### Human Review Status:\n"
    for s, c in sorted(train_status.items()):
        report_md += f"- **{s}**: {c}\n"

    report_md += f"""
---

## 3. Benchmark Composition (BioReasonBench)
### Category Breakdown:
"""
    for cat, c in sorted(bench_categories.items()):
        report_md += f"- **{cat}**: {c}\n"

    report_md += "\n### Difficulty Breakdown:\n"
    for diff, c in sorted(bench_diffs.items()):
        report_md += f"- **{diff}**: {c}\n"

    report_md += f"""
---

## 4. Contamination & Firewall Audit
- **Exact Matches**: {sum(1 for r in reports if r['contamination_type'] == 'EXACT_QUESTION_MATCH')}
- **Normalized Matches**: {sum(1 for r in reports if r['contamination_type'] == 'NORMALIZED_QUESTION_MATCH')}
- **Scenario Signature Collisions**: {sum(1 for r in reports if r['contamination_type'] == 'SCENARIO_SIGNATURE_COLLISION')}
- **High Token Overlaps**: {sum(1 for r in reports if r['contamination_type'] == 'HIGH_TOKEN_SIMILARITY')}

### Verdict:
{'✓ Clean separation maintained across training and held-out benchmark partitions.' if len(reports) == 0 else '⚠ Contamination issues detected.'}
"""

    with open(output, "w", encoding="utf-8") as f:
        f.write(report_md)

    click.secho(f"✓ Dataset audit report written to: {output}", fg="green")


if __name__ == "__main__":
    cli()

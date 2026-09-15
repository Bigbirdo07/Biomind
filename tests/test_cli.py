"""
Integration tests for CLI commands.
"""

from click.testing import CliRunner
from bioreason.cli import cli


def test_cli_validate_episode():
    runner = CliRunner()
    result = runner.invoke(cli, ["validate-episode", "training_data/examples/ep_001_scrna_pseudoreplication.json"])
    assert result.exit_code == 0
    assert "✓ Schema validation passed" in result.output
    assert "All scientific validation checks PASSED" in result.output


def test_cli_validate_experiment():
    runner = CliRunner()
    result = runner.invoke(cli, ["validate-experiment", "configs/examples/experiment_clam_neoplasia.yaml"])
    assert result.exit_code == 0
    assert "✓ Schema validation passed" in result.output
    assert "Experiment design PASSED all scientific checks" in result.output


def test_cli_validate_workflow():
    runner = CliRunner()
    result = runner.invoke(cli, ["validate-workflow", "configs/examples/workflow_clam_neoplasia_pipeline.yaml"])
    assert result.exit_code == 0
    assert "✓ Schema validation passed" in result.output
    assert "Workflow plan PASSED all scientific validation rules" in result.output


def test_cli_check_contamination():
    runner = CliRunner()
    result = runner.invoke(cli, ["check-contamination", "training_data/examples", "benchmark/examples"])
    assert result.exit_code == 0
    assert "No benchmark contamination or overlap detected" in result.output


def test_cli_evaluate():
    runner = CliRunner()
    result = runner.invoke(cli, ["evaluate", "benchmark/examples/bench_001_scrna_pseudoreplication.json", "--adapter", "mock"])
    assert result.exit_code == 0
    assert "EVALUATION SUMMARY" in result.output

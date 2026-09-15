"""
Validators for episodes, experiments, and workflow plans combining schema and rule engine checks.
"""

from typing import List, Tuple, Dict, Any
from pathlib import Path
from bioreason.schemas.episode import ScientificReasoningEpisode
from bioreason.schemas.experiment import ExperimentSpec
from bioreason.schemas.workflow import WorkflowPlan
from bioreason.datasets.loader import load_episode, load_experiment_spec, load_workflow_plan
from bioreason.rules.engine import ScientificRuleEngine
from bioreason.rules.base import RuleResult, RuleSeverity


def validate_episode_file(path: str) -> Tuple[bool, Any, List[RuleResult]]:
    rule_engine = ScientificRuleEngine()
    episode = load_episode(path)
    rule_results = rule_engine.validate_episode(episode)
    has_errors = any(not r.passed and r.severity == RuleSeverity.ERROR for r in rule_results)
    return (not has_errors, episode, rule_results)


def validate_experiment_file(path: str) -> Tuple[bool, Any, List[RuleResult]]:
    rule_engine = ScientificRuleEngine()
    experiment = load_experiment_spec(path)
    rule_results = rule_engine.validate_experiment(experiment)
    has_errors = any(not r.passed and r.severity == RuleSeverity.ERROR for r in rule_results)
    return (not has_errors, experiment, rule_results)


def validate_workflow_file(path: str) -> Tuple[bool, Any, List[RuleResult]]:
    rule_engine = ScientificRuleEngine()
    workflow = load_workflow_plan(path)
    rule_results = rule_engine.validate_workflow(workflow)
    has_errors = any(not r.passed and r.severity == RuleSeverity.ERROR for r in rule_results)
    return (not has_errors, workflow, rule_results)

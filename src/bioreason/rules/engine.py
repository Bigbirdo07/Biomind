"""
Central Rule Engine coordinator for BioReason.
"""

from typing import List, Optional, Union
from bioreason.schemas.experiment import ExperimentSpec
from bioreason.schemas.workflow import WorkflowPlan
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity
from .pseudoreplication import PseudoreplicationRule
from .leakage import (
    FeatureSelectionLeakageRule,
    PreprocessingLeakageRule,
    GroupLeakageRule,
)
from .confounding import BatchConfoundingRule
from .transformations import TransformationCompatibilityRule
from .multiple_testing import MultipleTestingRule
from .overfitting import HighDimensionalOverfittingRule


class ScientificRuleEngine:
    def __init__(self, rules: Optional[List[Rule]] = None):
        if rules is not None:
            self.rules = rules
        else:
            self.rules = [
                PseudoreplicationRule(),
                FeatureSelectionLeakageRule(),
                PreprocessingLeakageRule(),
                GroupLeakageRule(),
                BatchConfoundingRule(),
                TransformationCompatibilityRule(),
                MultipleTestingRule(),
                HighDimensionalOverfittingRule(),
            ]

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def validate_experiment(self, experiment: ExperimentSpec) -> List[RuleResult]:
        results = []
        for rule in self.rules:
            res = rule.evaluate_experiment(experiment)
            if res is not None:
                results.append(res)
        return results

    def validate_workflow(self, workflow: WorkflowPlan) -> List[RuleResult]:
        results = []
        for rule in self.rules:
            res = rule.evaluate_workflow(workflow)
            if res is not None:
                results.append(res)
        return results

    def validate_episode(self, episode: ScientificReasoningEpisode) -> List[RuleResult]:
        """
        Validates a scientific reasoning episode:
        Checks whether the episode's scientific_checks, reasoning_summary,
        and interpretation correctly align with the ground-truth methodological assessment.
        """
        results = []
        for rule in self.rules:
            res = rule.evaluate_episode(episode)
            if res is not None:
                results.append(res)
        return results

    @staticmethod
    def filter_failures(results: List[RuleResult]) -> List[RuleResult]:
        return [r for r in results if not r.passed]

    @staticmethod
    def has_errors(results: List[RuleResult]) -> bool:
        return any(not r.passed and r.severity == RuleSeverity.ERROR for r in results)

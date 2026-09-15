"""
Rule engine exports.
"""

from .base import Rule, RuleResult, RuleSeverity
from .pseudoreplication import PseudoreplicationRule
from .statistical_power import StatisticalPowerRule
from .leakage import (
    FeatureSelectionLeakageRule,
    PreprocessingLeakageRule,
    GroupLeakageRule,
)
from .confounding import BatchConfoundingRule
from .transformations import TransformationCompatibilityRule
from .multiple_testing import MultipleTestingRule
from .overfitting import HighDimensionalOverfittingRule
from .engine import ScientificRuleEngine

__all__ = [
    "Rule",
    "RuleResult",
    "RuleSeverity",
    "PseudoreplicationRule",
    "StatisticalPowerRule",
    "FeatureSelectionLeakageRule",
    "PreprocessingLeakageRule",
    "GroupLeakageRule",
    "BatchConfoundingRule",
    "TransformationCompatibilityRule",
    "MultipleTestingRule",
    "HighDimensionalOverfittingRule",
    "ScientificRuleEngine",
]

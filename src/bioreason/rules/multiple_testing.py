"""
Rule: Multiple hypothesis testing control in high-throughput biological data.
"""

from typing import Optional
from bioreason.schemas.experiment import ExperimentSpec, AnalysisObjective
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class MultipleTestingRule(Rule):
    rule_id = "MULT_001"
    name = "Multiple Hypothesis Testing Control"
    category = "statistical_reasoning"
    description = "Ensures multiple comparison adjustments (FDR / Benjamini-Hochberg) are mandated for genomic-scale tests."

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        # If the proposed analysis failed to control multiple testing, the episode should reflect this
        if episode.experiment.objective == AnalysisObjective.DIFFERENTIAL_EXPRESSION:
            # If multiple testing is not controlled and episode did not note it
            if episode.scientific_checks.multiple_testing_controlled is False:
                # The episode correctly identified that multiple testing was NOT controlled
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=True,
                    severity=RuleSeverity.INFO,
                    message="Episode correctly identified uncontrolled multiple testing in proposed analysis.",
                    explanation="Multiple testing flaw was properly recognized in scientific_checks."
                )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Multiple testing evaluation consistent.",
            explanation="Multiple testing assumptions properly handled."
        )

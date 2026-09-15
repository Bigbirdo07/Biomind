"""
Rule POWER_001: Detect low statistical power / insufficient independent biological replication.
"""

from typing import Optional
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AnalysisObjective,
)
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class StatisticalPowerRule(Rule):
    rule_id = "POWER_001"
    name = "Low or Insufficient Independent Biological Replication"
    category = "statistical_reasoning"
    description = (
        "Detects experimental designs with very low biological sample size (e.g. N < 3 per group) "
        "that provide insufficient statistical power for population-level inference."
    )

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        # Triggers when independent biological samples per group < 3 in comparative/differential studies
        if experiment.objective in [
            AnalysisObjective.DIFFERENTIAL_EXPRESSION,
            AnalysisObjective.SUPERVISED_CLASSIFICATION,
            AnalysisObjective.BIOMARKER_DISCOVERY,
        ]:
            low_n_groups = [g for g in experiment.groups if g.sample_count < 3]
            if low_n_groups or (not experiment.groups and experiment.samples < 6):
                group_details = ", ".join(f"{g.name}: N={g.sample_count}" for g in low_n_groups) if low_n_groups else f"Total N={experiment.samples}"
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.WARNING,
                    message=f"Low independent biological replication detected ({group_details}).",
                    explanation=(
                        "With N < 3 independent biological replicates per group, statistical tests have severely compromised degrees "
                        "of freedom. Estimating biological population variance and gene-specific dispersion is highly uncertain, "
                        "limiting power to detect subtle effect sizes and increasing vulnerability to unmodeled outlier samples."
                    ),
                    suggested_correction=(
                        "Increase biological replication to at least N >= 3 to 5 independent subjects per condition. "
                        "If additional samples cannot be acquired, report findings with explicitly bounded uncertainty and "
                        "mandate independent cohort validation before drawing strong biological conclusions."
                    ),
                    references=[
                        "Schurch et al. (2016) How many biological replicates are needed in an RNA-seq experiment and which differential expression tool should you use? RNA, 22(6), 839-851."
                    ]
                )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Independent biological replication appears adequate.",
            explanation="Sample counts meet minimal power recommendations."
        )

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        res = self.evaluate_experiment(episode.experiment)
        if not res.passed:
            if episode.scientific_checks.sample_size_adequate is False:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=True,
                    severity=RuleSeverity.INFO,
                    message="Episode correctly identified low biological replication / sample size limitations.",
                    explanation="Scientific checks accurately flagged sample size inadequacy."
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.WARNING,
                    message="Episode marked sample_size_adequate=true despite N < 3 biological subjects per group.",
                    explanation=res.explanation,
                    suggested_correction="Set scientific_checks.sample_size_adequate = false and document power limitations.",
                    references=res.references
                )
        return res

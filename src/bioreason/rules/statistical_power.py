"""
Rule POWER_001: Detect low independent biological replication warning (heuristic).
Conceptually defined as LOW_INDEPENDENT_REPLICATION_WARNING.
Note: Low independent biological N != Formal Power Analysis.
"""

from typing import Optional, List
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AnalysisObjective,
)
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class StatisticalPowerRule(Rule):
    rule_id = "POWER_001"
    name = "LOW_INDEPENDENT_REPLICATION_WARNING"
    category = "statistical_reasoning"
    description = (
        "Heuristic warning detecting experimental designs with low independent biological replication "
        "(e.g. N < 3 per group in differential or comparative analyses). "
        "Explicitly notes that low N is a heuristic risk indicator, NOT a formal mathematical power calculation."
    )

    def __init__(self, low_n_threshold: int = 3):
        self.low_n_threshold = low_n_threshold

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        # Triggers heuristic warning when independent biological samples per group < low_n_threshold
        if experiment.objective in [
            AnalysisObjective.DIFFERENTIAL_EXPRESSION,
            AnalysisObjective.SUPERVISED_CLASSIFICATION,
            AnalysisObjective.BIOMARKER_DISCOVERY,
        ]:
            low_n_groups = [g for g in experiment.groups if g.sample_count < self.low_n_threshold]
            if low_n_groups or (not experiment.groups and experiment.samples < (self.low_n_threshold * 2)):
                group_details = ", ".join(f"{g.name}: N={g.sample_count}" for g in low_n_groups) if low_n_groups else f"Total N={experiment.samples}"
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.WARNING,
                    message=f"Low independent biological replication warning ({group_details}, threshold N < {self.low_n_threshold}).",
                    explanation=(
                        f"Heuristic warning: With N < {self.low_n_threshold} independent biological replicates per condition, "
                        "degrees of freedom for variance and dispersion estimation are minimal, heightening vulnerability to unmodeled outliers. "
                        "CRITICAL SCIENTIFIC DISTINCTION: Low biological sample size (low N) is a heuristic risk warning and is NOT "
                        "equivalent to a formal statistical power calculation. Statistical power depends multi-factorially on expected effect size (delta/sigma), "
                        "biological population variance, statistical model distribution (e.g. Negative Binomial in RNA-seq), repeated-measures structure, "
                        "paired vs unpaired design, number of groups, endpoint dynamic range, alpha level (with multiple testing control), desired power (1-beta), "
                        "and technical precision. A formal power analysis (POWER_002) is required to mathematically quantify detectable effect sizes."
                    ),
                    suggested_correction=(
                        "Where feasible, increase biological replication to N >= 3 to 5 independent subjects per condition. "
                        "Conduct a formal prospective or simulation-based power analysis (POWER_002) for the specific assay and effect size. "
                        "If additional samples cannot be acquired, report findings with explicitly bounded uncertainty and mandate "
                        "independent external cohort replication before asserting definitive biological conclusions."
                    ),
                    references=[
                        "Schurch et al. (2016) How many biological replicates are needed in an RNA-seq experiment and which differential expression tool should you use? RNA, 22(6), 839-851.",
                        "Button et al. (2013) Power failure: why small sample size undermines the reliability of neuroscience. Nature Reviews Neuroscience, 14(5), 365-376."
                    ]
                )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Independent biological replication meets minimal heuristic threshold.",
            explanation=f"Sample counts meet the heuristic threshold (N >= {self.low_n_threshold} per group). Note: Formal power analysis (POWER_002) remains recommended for rigorous design."
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
                    message="Episode correctly flagged low biological replication / sample size limitations.",
                    explanation="Scientific checks accurately flagged sample size inadequacy as a heuristic limitation."
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.WARNING,
                    message=f"Episode marked sample_size_adequate=true despite N < {self.low_n_threshold} biological subjects per group.",
                    explanation=res.explanation,
                    suggested_correction="Set scientific_checks.sample_size_adequate = false and document low-N heuristic limitations.",
                    references=res.references
                )
        return res


class FormalPowerAnalysisRule(Rule):
    """
    Architecture placeholder for POWER_002: Formal Power Analysis Required.
    Future rule will check for explicit effect size, variance assumptions, and simulation/analytic power calculations.
    """
    rule_id = "POWER_002"
    name = "FORMAL_POWER_ANALYSIS_REQUIRED"
    category = "statistical_reasoning"
    description = (
        "Evaluates whether a formal prospective or retrospective power calculation was documented, "
        "accounting for effect size, dispersion, and multiple-testing FDR adjustment."
    )

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Formal power analysis check (POWER_002) is ready for Phase 2 integration.",
            explanation="POWER_002 architecture placeholder reserved for full parametric and simulation-based power modeling."
        )

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        return self.evaluate_experiment(episode.experiment)


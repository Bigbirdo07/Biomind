"""
Rule: Detect batch effect confounding with experimental phenotypes.
"""

from typing import Optional
from bioreason.schemas.experiment import ExperimentSpec
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class BatchConfoundingRule(Rule):
    rule_id = "CONF_001"
    name = "Perfect or Severe Batch/Phenotype Confounding"
    category = "confounding"
    description = "Detects experimental designs where sequencing batch or processing date is completely confounded with condition."

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        if experiment.batch_structure and experiment.batch_structure.confounded_with_group:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=RuleSeverity.ERROR,
                message="Batch structure is completely confounded with the biological condition of interest.",
                explanation=(
                    "When all control samples are processed in Batch A and all diseased/treated samples are processed in Batch B, "
                    "technical batch variation (e.g., reagent lot, temperature, sequencing lane) is mathematically collinear with "
                    "the biological variable. No computational adjustment (ComBat, limma removeBatchEffect) can disentangle "
                    "true biology from technical artifacts without destroying the biological signal or introducing phantom differences."
                ),
                suggested_correction=(
                    "Redesign the wet-lab experiment with randomized balanced batch assignment (block design). "
                    "If data is already collected, explicitly document that any observed differential signal is an unresolvable "
                    "combination of batch and biology, and require independent validation in a balanced cohort."
                ),
                references=[
                    "Leek et al. (2010) Tackling the widespread and critical impact of batch effects in high-throughput data. Nature Reviews Genetics, 11(10), 733-739.",
                    "Nygaard, V., Rødland, E. A., & Hovig, E. (2016) Methods that remove batch effects also distort true differences. Biostatistics, 17(1), 29-39."
                ]
            )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="No complete batch confounding detected.",
            explanation="Batch structure appears balanced or unconfounded."
        )

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        res = self.evaluate_experiment(episode.experiment)
        if not res.passed:
            if episode.scientific_checks.confounding_detected is True:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=True,
                    severity=RuleSeverity.INFO,
                    message="Episode correctly identified batch confounding in experimental design.",
                    explanation="Scientific checks accurately flagged confounding."
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message="Episode failed to flag confounding despite confounded batch structure.",
                    explanation=res.explanation,
                    suggested_correction="Set scientific_checks.confounding_detected = true and note limitation in interpretation.",
                    references=res.references
                )
        return res

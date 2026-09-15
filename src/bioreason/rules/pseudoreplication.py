"""
Rule: Detect pseudoreplication and improper experimental unit modeling in single-cell and biological assays.
"""

from typing import Optional
from bioreason.schemas.experiment import ExperimentSpec, AssayType, ExperimentalUnitLevel
from bioreason.schemas.workflow import WorkflowPlan
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class PseudoreplicationRule(Rule):
    rule_id = "PSEUDO_001"
    name = "Pseudoreplication in Single-Cell / Hierarchical Biological Assays"
    category = "experimental_design"
    description = (
        "Ensures that individual cells or sub-replicates are not treated as independent biological replicates "
        "when the true experimental unit is the organism, animal, or patient."
    )

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        # Case 1: Assay is scRNA-seq/snRNA-seq, experimental unit is animal/patient/organism,
        # but sample count per group is critically low (e.g. 1 animal per condition with thousands of cells)
        if experiment.assay in [AssayType.SINGLE_CELL_RNA_SEQ, AssayType.SINGLE_NUCLEUS_RNA_SEQ]:
            if experiment.experimental_unit in [
                ExperimentalUnitLevel.ANIMAL,
                ExperimentalUnitLevel.PATIENT,
                ExperimentalUnitLevel.ORGANISM,
            ]:
                for grp in experiment.groups:
                    if grp.sample_count < 3 and grp.cell_count and grp.cell_count > 100:
                        return RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.name,
                            passed=False,
                            severity=RuleSeverity.ERROR,
                            message=f"Group '{grp.name}' has only {grp.sample_count} biological subject(s) with {grp.cell_count} cells.",
                            explanation=(
                                "Cells from the same organism share genetic background, microenvironment, and technical processing. "
                                "Treating individual cells as independent biological observations inflates statistical power, produces "
                                "artificially deflated p-values, and constitutes classic pseudoreplication."
                            ),
                            suggested_correction=(
                                "Aggregate cells into sample-level pseudobulk profiles (e.g., sum counts per biological sample) "
                                "and perform differential analysis with DESeq2/edgeR, or employ generalized linear mixed models (GLMMs) "
                                "with random intercepts for individual biological subjects."
                            ),
                            references=[
                                "Squair et al. (2021) Confronting false discoveries in single-cell differential expression. Nature Communications, 12:5692.",
                                "Hurlbert, S. H. (1984) Pseudoreplication and the design of ecological field experiments. Ecological Monographs, 54(2), 187-211."
                            ]
                        )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="No obvious pseudoreplication detected in experiment design.",
            explanation="Biological replicates and experimental units appear properly aligned."
        )

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        res = self.evaluate_experiment(episode.experiment)
        if not res.passed:
            if episode.scientific_checks.replication_valid is False:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=True,
                    severity=RuleSeverity.INFO,
                    message="Episode correctly flagged pseudoreplication in the experimental design.",
                    explanation="Scientific checks accurately identified replication invalidity."
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message="Episode marked 'replication_valid: true' despite severe pseudoreplication in experiment.",
                    explanation=res.explanation,
                    suggested_correction="Update scientific_checks.replication_valid to false and provide pseudobulk or GLMM correction.",
                    references=res.references
                )
        return res

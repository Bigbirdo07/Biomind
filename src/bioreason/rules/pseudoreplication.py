"""
Rule PSEUDO_001: Detect pseudoreplication and independence violations across biological hierarchies.
"""

from typing import Optional
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AssayType,
    ExperimentalUnitLevel,
    ObservationalUnitLevel,
    AnalysisUnitLevel,
    ReplicateType,
)
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class PseudoreplicationRule(Rule):
    rule_id = "PSEUDO_001"
    name = "Independence / Pseudoreplication Violation"
    category = "experimental_design"
    description = (
        "Ensures that subordinate, correlated, or technical observations (e.g. single cells, technical replicates, "
        "repeated longitudinal measurements) are not treated as independent biological units of replication."
    )

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        # Case 1: Technical replicates treated as independent biological replicates
        if experiment.replicate_type == ReplicateType.TECHNICAL:
            if experiment.analysis_unit in [AnalysisUnitLevel.CELL, AnalysisUnitLevel.READ, None]:
                for grp in experiment.groups:
                    if grp.technical_replicates_per_sample and grp.technical_replicates_per_sample > 1:
                        return RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.name,
                            passed=False,
                            severity=RuleSeverity.ERROR,
                            message=f"Group '{grp.name}' treats {grp.technical_replicates_per_sample} technical replicates per sample as independent biological replicates.",
                            explanation=(
                                "Technical replicates measure the precision of the assay instrument or protocol, not biological variation "
                                "across a population. Treating technical aliquots as independent inflates sample size and produces artificially "
                                "deflated p-values."
                            ),
                            suggested_correction=(
                                "Collapse technical replicates per biological sample prior to inferential testing (e.g., using "
                                "DESeq2::collapseReplicates or calculating the mean/sum per subject)."
                            ),
                            references=[
                                "Blainey et al. (2014) Points of Significance: Replication. Nature Methods 11:879-880.",
                                "Hurlbert, S. H. (1984) Pseudoreplication and the design of ecological field experiments. Ecological Monographs, 54(2), 187-211."
                            ]
                        )

        # Case 2: Hierarchical unit (animal/patient/organism) with single cells treated as independent units of analysis
        is_hierarchical_subject = experiment.experimental_unit in [
            ExperimentalUnitLevel.ANIMAL,
            ExperimentalUnitLevel.PATIENT,
            ExperimentalUnitLevel.ORGANISM,
        ]
        
        if is_hierarchical_subject:
            # If the analysis unit is explicitly individual cells, or if single-cell assay without pseudobulk/hierarchical modeling
            is_cell_level_analysis = (
                experiment.analysis_unit == AnalysisUnitLevel.CELL
                or (
                    experiment.assay in [AssayType.SINGLE_CELL_RNA_SEQ, AssayType.SINGLE_NUCLEUS_RNA_SEQ]
                    and experiment.analysis_unit != AnalysisUnitLevel.PSEUDOBULK_SAMPLE
                    and any(g.cell_count and g.cell_count > 100 for g in experiment.groups)
                )
            )

            if is_cell_level_analysis:
                total_cells = sum(g.cell_count or 0 for g in experiment.groups)
                total_subjects = sum(g.sample_count for g in experiment.groups) or experiment.samples
                
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message=(
                        f"Analysis treats individual cells (total: {total_cells}) as independent biological replicates across "
                        f"{total_subjects} biological subject(s)."
                    ),
                    explanation=(
                        "Cells sampled from the same organism share genetic background, microenvironment, and batch conditions. "
                        "Treating thousands of single cells as independent observations constitutes classic pseudoreplication, "
                        "severely underestimating variance and yielding false-positive discovery rates exceeding 50% under the null."
                    ),
                    suggested_correction=(
                        "Aggregate single-cell counts into sample-level pseudobulk profiles (summing counts per cell type per subject) "
                        "and test with DESeq2/edgeR, or fit Generalized Linear Mixed Models (GLMMs) with random intercepts for each biological subject."
                    ),
                    references=[
                        "Squair et al. (2021) Confronting false discoveries in single-cell differential expression. Nature Communications, 12:5692.",
                        "Zimmerman et al. (2021) Practical solution to pseudoreplication in single-cell RNA-seq. Nature Communications, 12:738."
                    ]
                )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="No pseudoreplication or independence violation detected.",
            explanation="Experimental units and analytical units are properly aligned."
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

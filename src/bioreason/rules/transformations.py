"""
Rule: Detect invalid input transformations for statistical bioinformatics tools.
"""

from typing import Optional
from bioreason.schemas.experiment import ExperimentSpec, DataType, AnalysisObjective
from bioreason.schemas.workflow import WorkflowPlan, MLModelType, NormalizationMethod
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class TransformationCompatibilityRule(Rule):
    rule_id = "TRANS_001"
    name = "DESeq2 / edgeR Input Data Type Compatibility"
    category = "transformations"
    description = "Ensures count-based differential expression tools receive un-normalized raw integer counts."

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        if experiment.objective == AnalysisObjective.DIFFERENTIAL_EXPRESSION:
            if experiment.input_data_type in [
                DataType.NORMALIZED_COUNTS,
                DataType.LOG_NORMALIZED_COUNTS,
                DataType.TPM_FPKM_RPKM,
            ]:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message=f"Input data type '{experiment.input_data_type.value}' is incompatible with count-based differential expression.",
                    explanation=(
                        "Tools like DESeq2 and edgeR model count variance using the Negative Binomial distribution, explicitly "
                        "incorporating library size size-factors and mean-variance dispersion estimations internally. "
                        "Passing pre-normalized, log-transformed, or TPM/FPKM values breaks the discrete Poisson/Negative-Binomial "
                        "error model, leading to corrupted dispersion estimates and invalid p-values."
                    ),
                    suggested_correction=(
                        "Provide raw, un-normalized integer count matrices directly to DESeq2 (using DESeqDataSetFromMatrix) or edgeR (DGEList). "
                        "If only TPM/log-counts are available, use linear modeling frameworks designed for continuous data such as limma-trend."
                    ),
                    references=[
                        "Love, M. I., Huber, W., & Anders, S. (2014) Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. Genome Biology, 15(12), 550.",
                        "Robinson, M. D., McCarthy, D. J., & Smyth, G. K. (2010) edgeR: a Bioconductor package for differential expression analysis of digital gene expression data. Bioinformatics, 26(1), 139-140."
                    ]
                )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Input data type is compatible with analytical objective.",
            explanation="Appropriate data format provided for differential expression modeling."
        )

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        res = self.evaluate_experiment(episode.experiment)
        if not res.passed:
            if episode.scientific_checks.transformation_valid is False:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=True,
                    severity=RuleSeverity.INFO,
                    message="Episode correctly identified invalid transformation / data type in proposed analysis.",
                    explanation="Scientific checks accurately flagged transformation mismatch."
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message="Episode marked transformation_valid=true despite using pre-normalized counts in count-based model.",
                    explanation=res.explanation,
                    suggested_correction="Update scientific_checks.transformation_valid = false and recommend raw count inputs.",
                    references=res.references
                )
        return res

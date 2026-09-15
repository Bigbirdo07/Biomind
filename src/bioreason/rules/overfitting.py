"""
Rule: High-dimensional biological data overfitting and model interpretability.
"""

from typing import Optional
from bioreason.schemas.workflow import (
    WorkflowPlan,
    MLModelType,
    FeatureSelectionMethod,
)
from .base import Rule, RuleResult, RuleSeverity


class HighDimensionalOverfittingRule(Rule):
    rule_id = "OVERFIT_001"
    name = "Unregularized High-Dimensional Biological Modeling (p >> n)"
    category = "machine_learning"
    description = "Detects unregularized high-capacity models applied directly to high-dimensional biological feature spaces without sparsity or stability validation."

    def evaluate_workflow(self, workflow: WorkflowPlan) -> Optional[RuleResult]:
        # If workflow uses unregularized complex models on genomic features without feature selection or stability
        complex_models = [MLModelType.MULTILAYER_PERCEPTRON, MLModelType.RBF_SVM]
        has_complex_model = any(m in complex_models for m in workflow.models)
        
        if (
            has_complex_model
            and workflow.feature_selection.method == FeatureSelectionMethod.NONE
            and not workflow.interpretability.bootstrap_feature_stability
        ):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=RuleSeverity.WARNING,
                message="Complex unregularized model used on high-dimensional genomic features without sparsity or stability validation.",
                explanation=(
                    "In typical biological datasets with thousands of genes and dozens/hundreds of samples (p >> n), "
                    "high-capacity models easily memorize noise and generate non-reproducible feature sets. "
                    "For biomarker discovery, sparse regularized linear models (LASSO / Elastic Net) with bootstrap stability "
                    "provide superior generalization, interpretability, and wet-lab validation feasibility."
                ),
                suggested_correction=(
                    "Incorporate L1/ElasticNet regularization, enforce sparse feature selection, and evaluate bootstrap "
                    "feature selection frequency across cross-validation folds."
                ),
                references=[
                    "Meinshausen, N., & Bühlmann, P. (2010) Stability selection. JRSS B, 72(4), 417-473."
                ]
            )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Model complexity and regularization are balanced.",
            explanation="Regularization and validation parameters appear sound."
        )

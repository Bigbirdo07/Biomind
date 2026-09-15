"""
Rules: Detect data leakage in biological machine learning workflows.
"""

from typing import Optional
from bioreason.schemas.workflow import (
    WorkflowPlan,
    FitScope,
    FeatureSelectionMethod,
    SplitType,
    ExperimentalUnitLevel
)
from bioreason.schemas.episode import ScientificReasoningEpisode
from .base import Rule, RuleResult, RuleSeverity


class FeatureSelectionLeakageRule(Rule):
    rule_id = "LEAK_001"
    name = "Feature Selection Before Train/Test Separation"
    category = "data_leakage"
    description = "Detects feature selection fitted on the entire dataset prior to cross-validation or testing splits."

    def evaluate_workflow(self, workflow: WorkflowPlan) -> Optional[RuleResult]:
        if (
            workflow.feature_selection.method != FeatureSelectionMethod.NONE
            and workflow.feature_selection.fit_scope == FitScope.FULL_DATASET
        ):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=RuleSeverity.ERROR,
                message="Feature selection is configured with fit_scope='full_dataset'.",
                explanation=(
                    "Selecting features on the entire dataset prior to splitting leaks target labels and sample information "
                    "from the validation/test sets into model training. In high-dimensional biological data (e.g. p = 20,000 genes), "
                    "this generates severely over-optimistic cross-validation performance (e.g., AUC ~ 1.0 on pure noise)."
                ),
                suggested_correction=(
                    "Fit feature selection strictly on training folds inside each cross-validation loop using an "
                    "end-to-end scikit-learn Pipeline or nested cross-validation."
                ),
                references=[
                    "Ambroise, C. & McLachlan, G. J. (2002) Selection bias in gene extraction on the basis of microarray gene-expression data. PNAS, 99(10), 6562-6566.",
                    "Hastie, T., Tibshirani, R., & Friedman, J. (2009) The Elements of Statistical Learning (Section 7.10.2)."
                ]
            )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Feature selection scope is properly constrained to training folds.",
            explanation="No global feature selection leakage detected."
        )


class PreprocessingLeakageRule(Rule):
    rule_id = "LEAK_002"
    name = "Global Preprocessing / Scaling / Dimensionality Reduction Leakage"
    category = "data_leakage"
    description = "Detects PCA, imputation, or feature scaling fitted globally on full datasets before partitioning."

    def evaluate_workflow(self, workflow: WorkflowPlan) -> Optional[RuleResult]:
        if workflow.preprocessing.fit_scope == FitScope.FULL_DATASET:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                passed=False,
                severity=RuleSeverity.ERROR,
                message="Preprocessing is configured with fit_scope='full_dataset'.",
                explanation=(
                    "Fitting PCA, standard scalers, or imputation models on the full dataset incorporates distribution and "
                    "variance statistics from held-out validation/test partitions, leading to information leakage."
                ),
                suggested_correction=(
                    "Encapsulate preprocessing in a Pipeline: fit scalers, imputation, and PCA strictly on training partitions, "
                    "then transform validation/test sets using the fitted parameters."
                ),
                references=[
                    "Varoquaux, G. (2018) Cross-validation failure: Small sample sizes lead to large error bars. NeuroImage, 180, 68-77."
                ]
            )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Preprocessing scope is properly isolated to training partitions.",
            explanation="No global preprocessing leakage detected."
        )


class GroupLeakageRule(Rule):
    rule_id = "LEAK_003"
    name = "Cross-Validation Group Leakage for Hierarchical / Multi-Observation Biological Units"
    category = "data_leakage"
    description = "Detects random cross-validation splitting when observations originate from shared biological subjects."

    def evaluate_workflow(self, workflow: WorkflowPlan) -> Optional[RuleResult]:
        # If experimental unit is hierarchical (e.g. animal or patient level) but split is naive random k-fold
        if workflow.experimental_unit_level in [
            ExperimentalUnitLevel.ANIMAL,
            ExperimentalUnitLevel.PATIENT,
            ExperimentalUnitLevel.ORGANISM,
        ]:
            if workflow.split.outer_cv in [SplitType.RANDOM_KFOLD, SplitType.STRATIFIED_KFOLD]:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    passed=False,
                    severity=RuleSeverity.ERROR,
                    message=f"Split strategy '{workflow.split.outer_cv.value}' does not group by biological subject.",
                    explanation=(
                        "When multiple observations (e.g., cells, technical replicates, longitudinal samples) originate from the "
                        "same organism or patient, random partitioning allows samples from the same subject into both training and "
                        "test folds. The classifier learns subject-specific idiosyncrasies rather than generalizable disease biology, "
                        "causing cross-validation AUC ~ 0.99 while external test AUC collapses to random guessing (~0.50)."
                    ),
                    suggested_correction=(
                        "Use GroupKFold or StratifiedGroupKFold grouped by the subject identifier (e.g., animal_id, patient_id) "
                        "so all observations from a given biological subject remain exclusively within either train or test in any fold."
                    ),
                    references=[
                        "Little et al. (2017) Using and understanding cross-validation strategies. Perspectives in Science, 10, 100-110."
                    ]
                )
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            passed=True,
            severity=RuleSeverity.INFO,
            message="Group split structure is appropriate for experimental unit hierarchy.",
            explanation="No group-level leakage detected in cross-validation scheme."
        )

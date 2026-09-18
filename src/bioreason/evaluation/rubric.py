"""
Deterministic scientific rubric scorer for benchmark evaluation with critical failure analysis and error taxonomy.
"""

from typing import Dict, Any, List, Optional
from bioreason.schemas.benchmark import BenchmarkItem, EvaluationScore, RubricCriterion
from bioreason.models.base import ModelPrediction


CRITICAL_FAILURE_TRIGGERS = [
    ("pseudoreplication", "MISSED_PSEUDOREPLICATION", ["cells are independent", "30000 independent samples", "treat each cell as replicate"]),
    ("leakage", "MISSED_LEAKAGE", ["pca never leaks", "feature selection on all samples is fine", "leakage is harmless"]),
    ("confounding", "MISSED_CONFOUNDING", ["combat will fix perfectly", "batch has no effect", "valid drug effect despite collinearity"]),
    ("causality", "OVERCLAIMED_CAUSALITY", ["causes", "proven causal mechanism", "shap proves causation"]),
    ("transformation", "INVALID_TRANSFORMATION", ["deseq2 expects log counts", "tpm is recommended for deseq2"]),
]


class ScientificRubricScorer:
    """
    Evaluates model predictions against structured multi-dimensional scientific rubrics.
    Tracks critical failures and classifies model errors into canonical taxonomy.
    """

    @staticmethod
    def score_criterion(text: str, criterion: RubricCriterion) -> float:
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Positive key point coverage
        matched_positives = 0
        for kp in criterion.key_points:
            kp_words = [w for w in kp.lower().split() if len(w) > 4]
            if any(w in text_lower for w in kp_words):
                matched_positives += 1
                
        pos_ratio = matched_positives / max(len(criterion.key_points), 1)
        
        # Negative penalty
        penalty = 0.0
        for np in criterion.negative_points:
            np_words = [w for w in np.lower().split() if len(w) > 4]
            if len(np_words) > 0 and all(w in text_lower for w in np_words[:2]):
                penalty += 0.25

        score = max(0.0, min(1.0, pos_ratio - penalty))
        return round(score, 3)

    def evaluate_prediction(self, benchmark_item: BenchmarkItem, prediction: ModelPrediction) -> EvaluationScore:
        rubric = benchmark_item.scoring_rubric
        
        # Determine flaw detection from either boolean flag or identified_issues list
        if prediction.flaw_detected is not None:
            pred_flaw_present = prediction.flaw_detected
        elif prediction.identified_issues and len(prediction.identified_issues) > 0:
            pred_flaw_present = any(i.lower() not in ["none", "no issues", "valid", "no flaw"] for i in prediction.identified_issues)
        else:
            pred_flaw_present = False

        expected_flaw_present = benchmark_item.flawed_analysis_present
        flaw_detected_binary = (pred_flaw_present == expected_flaw_present)
        
        # Full concatenated text for lexical and semantic checking
        full_text_parts = [
            prediction.primary_assessment or "",
            prediction.scientific_rationale or "",
            " ".join(prediction.identified_issues),
            " ".join(prediction.recommended_actions),
            " ".join(prediction.limitations_noted),
            " ".join(prediction.unsupported_claims),
            prediction.raw_response or "",
        ]
        raw_text = " ".join(full_text_parts).lower()

        # 1. Flaw detection score
        flaw_detection_score = 1.0 if flaw_detected_binary else 0.0
        flaw_type_str = prediction.flaw_type or " ".join(prediction.identified_issues)
        if flaw_type_str and benchmark_item.flaw_type:
            if benchmark_item.flaw_type.lower() in flaw_type_str.lower():
                flaw_detection_score = 1.0
            elif flaw_detected_binary:
                flaw_detection_score = 0.85

        # 2. Scientific explanation
        rationale_text = f"{prediction.primary_assessment or ''} {prediction.scientific_rationale or ''} {' '.join(prediction.identified_issues)} {prediction.raw_response or ''}"
        explanation_score = self.score_criterion(rationale_text, rubric.scientific_explanation)

        # 3. Correction quality
        correction_text = f"{prediction.proposed_correction or ''} {' '.join(prediction.recommended_actions)} {prediction.raw_response or ''}"
        correction_score = self.score_criterion(correction_text, rubric.correction_quality)

        # 4. Uncertainty calibration
        limitations_combined = f"{' '.join(prediction.limitations_noted)} {' '.join(prediction.unsupported_claims)} {rationale_text}"
        calibration_score = self.score_criterion(limitations_combined, rubric.uncertainty_calibration)

        # 5. Interpretation quality
        interp_combined = f"{' '.join(prediction.supported_claims)} {' '.join(prediction.unsupported_claims)} {rationale_text}"
        interpretation_score = self.score_criterion(interp_combined, rubric.interpretation_quality)

        # 6. Critical failure and taxonomy evaluation
        critical_failure = False
        identified_failure_modes: List[str] = []

        # If a flaw was present, but model failed to detect it
        if benchmark_item.flawed_analysis_present and not pred_flaw_present:
            critical_failure = True
            if benchmark_item.flaw_type:
                ft = benchmark_item.flaw_type.lower()
                if "pseudo" in ft:
                    identified_failure_modes.append("MISSED_PSEUDOREPLICATION")
                elif "leak" in ft:
                    identified_failure_modes.append("MISSED_LEAKAGE")
                elif "confound" in ft or "batch" in ft:
                    identified_failure_modes.append("MISSED_CONFOUNDING")
                elif "transform" in ft or "count" in ft or "tpm" in ft:
                    identified_failure_modes.append("INVALID_TRANSFORMATION")
                else:
                    identified_failure_modes.append("STATISTICAL_ERROR")

        # Check explicit critical trigger phrases in response
        for category, mode, bad_phrases in CRITICAL_FAILURE_TRIGGERS:
            if any(p in raw_text for p in bad_phrases):
                critical_failure = True
                if mode not in identified_failure_modes:
                    identified_failure_modes.append(mode)

        # Check scoring breakdown critical errors if present on benchmark item
        if benchmark_item.scoring_breakdown and benchmark_item.scoring_breakdown.critical_errors:
            for ce in benchmark_item.scoring_breakdown.critical_errors:
                if ce.lower() in raw_text:
                    critical_failure = True
                    if "CRITICAL_ASSERTION_VIOLATION" not in identified_failure_modes:
                        identified_failure_modes.append("CRITICAL_ASSERTION_VIOLATION")

        # Confidence Calibration Penalty / Reward
        conf = (prediction.confidence or "MEDIUM").upper()
        if critical_failure and conf == "HIGH":
            # Severe overconfidence penalty for endorsing critical scientific error
            calibration_score = max(0.0, calibration_score - 0.4)
            if "OVERCONFIDENT_CRITICAL_FAILURE" not in identified_failure_modes:
                identified_failure_modes.append("OVERCONFIDENT_CRITICAL_FAILURE")
        elif not critical_failure and conf in ["HIGH", "MEDIUM"] and flaw_detected_binary:
            calibration_score = min(1.0, calibration_score + 0.1)

        # False Alarm Detection: scenario was scientifically valid, but model flagged a critical methodological flaw
        false_alarm = False
        if not benchmark_item.flawed_analysis_present and pred_flaw_present:
            false_alarm = True

        # Correction Actionability Score: assesses actionability and actionable guidance
        actionability_keywords = ["pipeline", "fold", "pseudobulk", "mixed model", "random effect", "within", "formula", "stratified", "permute", "benjamini", "fdr"]
        actionable_matches = sum(1 for kw in actionability_keywords if kw in correction_text.lower())
        actionability_bonus = min(0.3, actionable_matches * 0.1)
        correction_actionability = min(1.0, correction_score + actionability_bonus) if pred_flaw_present else 1.0

        # Primary Issue Prioritization
        primary_issue_prioritized = True
        if benchmark_item.expected_decision and benchmark_item.expected_decision.primary_issue:
            p_issue = benchmark_item.expected_decision.primary_issue.lower()
            # If the model produced identified issues, check if the first issue or primary assessment captures it
            first_issue_text = f"{prediction.primary_assessment or ''} {(prediction.identified_issues[0] if prediction.identified_issues else '')}".lower()
            p_words = [w for w in p_issue.split() if len(w) > 4]
            if p_words and not any(w in first_issue_text for w in p_words) and not (benchmark_item.flawed_analysis_present == False):
                primary_issue_prioritized = False

        # Composite weighted score
        weights = [
            rubric.flaw_detection.weight,
            rubric.scientific_explanation.weight,
            rubric.correction_quality.weight,
            rubric.uncertainty_calibration.weight,
            rubric.interpretation_quality.weight,
        ]
        total_weight = sum(weights) or 5.0
        composite = (
            flaw_detection_score * rubric.flaw_detection.weight
            + explanation_score * rubric.scientific_explanation.weight
            + correction_score * rubric.correction_quality.weight
            + calibration_score * rubric.uncertainty_calibration.weight
            + interpretation_score * rubric.interpretation_quality.weight
        ) / total_weight

        # Hard-negative & Uncertainty metadata
        is_hard_negative = (not benchmark_item.flawed_analysis_present)
        no_error_correct = is_hard_negative and (not pred_flaw_present)
        is_insufficient_info = ("insufficient" in (benchmark_item.flaw_type or "").lower()) or ("insufficient" in benchmark_item.ground_truth_rationale.lower())
        high_confidence_critical_error = critical_failure and (conf == "HIGH")

        return EvaluationScore(
            item_id=benchmark_item.item_id,
            difficulty=benchmark_item.difficulty,
            flaw_detection_score=flaw_detection_score,
            explanation_score=explanation_score,
            correction_score=correction_score,
            calibration_score=calibration_score,
            interpretation_score=interpretation_score,
            composite_score=round(composite, 3),
            flaw_detected_binary=flaw_detected_binary,
            critical_failure=critical_failure,
            false_alarm=false_alarm,
            correction_actionability_score=round(correction_actionability, 3),
            primary_issue_prioritized=primary_issue_prioritized,
            identified_failure_modes=identified_failure_modes,
            is_hard_negative=is_hard_negative,
            no_error_correct=no_error_correct,
            is_insufficient_info=is_insufficient_info,
            high_confidence_critical_error=high_confidence_critical_error,
            comments=f"Flaw matched: {flaw_detected_binary}, Critical Fail: {critical_failure}, False Alarm: {false_alarm}, Composite: {composite:.3f}"
        )



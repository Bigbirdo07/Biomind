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
        raw_text = f"{prediction.scientific_rationale or ''} {prediction.raw_response or ''}".lower()

        # 1. Flaw detection
        pred_flaw_present = prediction.flaw_detected if prediction.flaw_detected is not None else False
        expected_flaw_present = benchmark_item.flawed_analysis_present
        flaw_detected_binary = (pred_flaw_present == expected_flaw_present)
        
        flaw_detection_score = 1.0 if flaw_detected_binary else 0.0
        if prediction.flaw_type and benchmark_item.flaw_type:
            if benchmark_item.flaw_type.lower() in prediction.flaw_type.lower():
                flaw_detection_score = 1.0
            elif flaw_detected_binary:
                flaw_detection_score = 0.75

        # 2. Scientific explanation
        rationale_text = prediction.scientific_rationale or prediction.raw_response
        explanation_score = self.score_criterion(rationale_text, rubric.scientific_explanation)

        # 3. Correction quality
        correction_text = prediction.proposed_correction or prediction.raw_response
        correction_score = self.score_criterion(correction_text, rubric.correction_quality)

        # 4. Uncertainty calibration
        calib_text = f"{prediction.scientific_rationale or ''} {' '.join(prediction.limitations_noted)}"
        calibration_score = self.score_criterion(calib_text, rubric.uncertainty_calibration)

        # 5. Interpretation quality
        interp_text = f"{prediction.scientific_rationale or ''} {' '.join(prediction.limitations_noted)}"
        interpretation_score = self.score_criterion(interp_text, rubric.interpretation_quality)

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
                elif "transform" in ft or "count" in ft:
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
                    identified_failure_modes.append("CRITICAL_ASSERTION_VIOLATION")

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

        # Heavy penalty if critical failure occurred
        if critical_failure:
            composite = max(0.0, composite * 0.5)

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
            identified_failure_modes=identified_failure_modes,
            comments=f"Flaw matched: {flaw_detected_binary}, Critical Fail: {critical_failure}, Composite: {composite:.3f}"
        )

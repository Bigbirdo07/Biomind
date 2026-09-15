"""
Deterministic scientific rubric scorer for benchmark evaluation.
"""

from typing import Dict, Any, List
from bioreason.schemas.benchmark import BenchmarkItem, EvaluationScore, RubricCriterion
from bioreason.models.base import ModelPrediction


class ScientificRubricScorer:
    """
    Evaluates model predictions against structured multi-dimensional scientific rubrics.
    Avoids naive exact text matching by analyzing structured fields, key scientific concept coverage,
    and penalized negative claims.
    """

    @staticmethod
    def score_criterion(text: str, criterion: RubricCriterion) -> float:
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Calculate positive key point coverage
        matched_positives = 0
        for kp in criterion.key_points:
            # Check if any main terms of keypoint are covered in text
            kp_words = [w for w in kp.lower().split() if len(w) > 4]
            if any(w in text_lower for w in kp_words):
                matched_positives += 1
                
        pos_ratio = matched_positives / max(len(criterion.key_points), 1)
        
        # Calculate negative penalty
        penalty = 0.0
        for np in criterion.negative_points:
            np_words = [w for w in np.lower().split() if len(w) > 4]
            if len(np_words) > 0 and all(w in text_lower for w in np_words[:2]):
                penalty += 0.25

        score = max(0.0, min(1.0, pos_ratio - penalty))
        return round(score, 3)

    def evaluate_prediction(self, benchmark_item: BenchmarkItem, prediction: ModelPrediction) -> EvaluationScore:
        rubric = benchmark_item.scoring_rubric

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

        return EvaluationScore(
            item_id=benchmark_item.item_id,
            flaw_detection_score=flaw_detection_score,
            explanation_score=explanation_score,
            correction_score=correction_score,
            calibration_score=calibration_score,
            interpretation_score=interpretation_score,
            composite_score=round(composite, 3),
            flaw_detected_binary=flaw_detected_binary,
            comments=f"Flaw matched: {flaw_detected_binary}, Composite: {composite:.3f}"
        )

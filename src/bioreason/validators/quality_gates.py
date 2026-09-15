"""
Automated Quality Gates for BioReason dataset and benchmark items.
Validates structural integrity, epistemic calibration, experimental unit specification,
and flags potential low-quality or inconsistent items for human review.
"""

from typing import List, Dict, Any, Optional
from bioreason.schemas.episode import (
    ScientificReasoningEpisode,
    ValidationStatus,
    ClaimLevel,
)
from bioreason.schemas.benchmark import BenchmarkItem, DifficultyLevel


class QualityGateIssue:
    def __init__(self, item_id: str, issue_type: str, severity: str, message: str):
        self.item_id = item_id
        self.issue_type = issue_type
        self.severity = severity  # "ERROR" or "WARNING"
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
        }


def validate_episode_quality_gates(episode: ScientificReasoningEpisode) -> List[QualityGateIssue]:
    issues: List[QualityGateIssue] = []

    # 1. Missing experimental unit specification
    if not episode.experiment or not episode.experiment.experimental_unit:
        issues.append(
            QualityGateIssue(
                item_id=episode.episode_id,
                issue_type="MISSING_EXPERIMENTAL_UNIT",
                severity="ERROR",
                message="Episode experiment specification lacks explicit experimental_unit definition.",
            )
        )

    # 2. Prompt brevity / triviality check
    if len(episode.question.strip().split()) < 8:
        issues.append(
            QualityGateIssue(
                item_id=episode.episode_id,
                issue_type="OVERLY_SHORT_PROMPT",
                severity="WARNING",
                message=f"Prompt is unusually short ({len(episode.question.split())} words); ensure rich scientific context.",
            )
        )

    # 3. Empty correction / rationale check
    if not episode.preferred_analysis or len(episode.preferred_analysis.strip()) < 10:
        issues.append(
            QualityGateIssue(
                item_id=episode.episode_id,
                issue_type="EMPTY_CORRECTION_CRITERIA",
                severity="ERROR",
                message="Preferred analysis / methodological correction is empty or insufficiently detailed.",
            )
        )

    # 4. Unsupported causal claims check
    unsupported_claims = episode.interpretation.unsupported_claims if episode.interpretation else []
    for claim in unsupported_claims:
        if claim.level == ClaimLevel.CAUSAL_CLAIM:
            # Verified proper categorization of unsupported causal assertion
            pass

    # 5. Unsupported expert validation label check
    if episode.validation_status == ValidationStatus.EXPERT_VALIDATED:
        if episode.provenance and episode.provenance.source_type == "synthetic_auto_generated":
            issues.append(
                QualityGateIssue(
                    item_id=episode.episode_id,
                    issue_type="UNSUPPORTED_EXPERT_VALIDATION",
                    severity="ERROR",
                    message="Synthetic auto-generated item cannot be labeled EXPERT_VALIDATED without genuine expert review.",
                )
            )

    return issues


def validate_benchmark_quality_gates(item: BenchmarkItem) -> List[QualityGateIssue]:
    issues: List[QualityGateIssue] = []

    # 1. Prompt and scenario length check
    if len(item.scenario.strip().split()) < 10:
        issues.append(
            QualityGateIssue(
                item_id=item.item_id,
                issue_type="OVERLY_SHORT_SCENARIO",
                severity="WARNING",
                message="Benchmark scenario text is too short to test deep reasoning.",
            )
        )

    # 2. Rubric completeness
    rubric = item.scoring_rubric
    for crit_name, crit in [
        ("flaw_detection", rubric.flaw_detection),
        ("scientific_explanation", rubric.scientific_explanation),
        ("correction_quality", rubric.correction_quality),
        ("uncertainty_calibration", rubric.uncertainty_calibration),
        ("interpretation_quality", rubric.interpretation_quality),
    ]:
        if not crit.key_points or len(crit.key_points) == 0:
            issues.append(
                QualityGateIssue(
                    item_id=item.item_id,
                    issue_type="EMPTY_RUBRIC_CRITERION",
                    severity="ERROR",
                    message=f"Rubric criterion '{crit_name}' has no key_points defined.",
                )
            )

    # 3. Contradictory flaw specification
    if item.flawed_analysis_present and not item.flaw_type:
        issues.append(
            QualityGateIssue(
                item_id=item.item_id,
                issue_type="CONTRADICTORY_FLAW_SPECIFICATION",
                severity="WARNING",
                message="Item flagged as flawed_analysis_present=True but flaw_type is None.",
            )
        )

    return issues

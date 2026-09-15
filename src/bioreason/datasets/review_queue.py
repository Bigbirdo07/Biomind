"""
Human Review Queue system for exporting cases requiring human scientific review.
Categories:
- ambiguous_gold_answer
- contamination_concern
- conflicting_rule
- low_confidence_auto_generated
- source_uncertainty
- domain_expertise_required
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class ReviewQueueManager:
    """Manages structured human review queue exports."""

    CATEGORIES = [
        "ambiguous_gold_answer",
        "contamination_concern",
        "conflicting_rule",
        "low_confidence_auto_generated",
        "source_uncertainty",
        "domain_expertise_required",
    ]

    def __init__(self, base_dir: str = "review_queue"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for cat in self.CATEGORIES:
            (self.base_dir / cat).mkdir(parents=True, exist_ok=True)

    def add_case(
        self,
        category: str,
        item_id: str,
        item_data: Dict[str, Any],
        flag_reason: str,
        suggested_reviewer: Optional[str] = None,
    ) -> Path:
        if category not in self.CATEGORIES:
            raise ValueError(f"Unknown review category '{category}'. Must be one of {self.CATEGORIES}")

        entry = {
            "item_id": item_id,
            "category": category,
            "flag_reason": flag_reason,
            "suggested_reviewer": suggested_reviewer,
            "data": item_data,
        }

        target_file = self.base_dir / category / f"{item_id}.json"
        with open(target_file, "w") as f:
            json.dump(entry, f, indent=2)
        return target_file

    def get_queue_summary(self) -> Dict[str, int]:
        summary = {}
        for cat in self.CATEGORIES:
            cat_dir = self.base_dir / cat
            count = len(list(cat_dir.glob("*.json")))
            summary[cat] = count
        return summary

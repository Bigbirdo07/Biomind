"""
Base classes and interfaces for the BioReason deterministic scientific rule engine.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from bioreason.schemas.experiment import ExperimentSpec
from bioreason.schemas.workflow import WorkflowPlan
from bioreason.schemas.episode import ScientificReasoningEpisode


class RuleSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    severity: RuleSeverity
    message: str
    explanation: str
    suggested_correction: Optional[str] = None
    references: List[str] = Field(default_factory=list)


class Rule:
    """Abstract base class for deterministic scientific rules."""
    rule_id: str = "RULE_000"
    name: str = "Base Rule"
    category: str = "general"
    description: str = ""

    def evaluate_experiment(self, experiment: ExperimentSpec) -> Optional[RuleResult]:
        """Evaluate rule against an experiment specification."""
        return None

    def evaluate_workflow(self, workflow: WorkflowPlan) -> Optional[RuleResult]:
        """Evaluate rule against a workflow plan."""
        return None

    def evaluate_episode(self, episode: ScientificReasoningEpisode) -> Optional[RuleResult]:
        """Evaluate rule against a full scientific reasoning episode."""
        return None

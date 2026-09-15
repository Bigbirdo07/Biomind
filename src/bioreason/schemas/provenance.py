"""
Typed schemas for experiment provenance and run tracking.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp: str
    git_commit: Optional[str] = None
    git_dirty: bool = False
    model_name: str
    model_revision: Optional[str] = "main"
    tokenizer_revision: Optional[str] = "main"
    dataset_version: str
    benchmark_version: str
    training_config: Dict[str, Any] = Field(default_factory=dict)
    random_seed: int = 42
    learning_rate: float
    optimizer: str = "adamw_torch"
    scheduler: str = "cosine"
    precision: str = "bf16"
    gpu_type: Optional[str] = None
    gpu_count: int = 1
    training_duration_seconds: Optional[float] = None
    total_tokens_trained: Optional[int] = None
    checkpoint_path: Optional[str] = None
    evaluation_metrics: Dict[str, float] = Field(default_factory=dict)

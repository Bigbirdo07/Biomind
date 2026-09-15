"""
Dataset loaders and serializers for scientific episodes and benchmark items.
"""

import json
import os
from pathlib import Path
from typing import List, Union, Dict, Any
import yaml
from bioreason.schemas.episode import ScientificReasoningEpisode
from bioreason.schemas.benchmark import BenchmarkItem
from bioreason.schemas.experiment import ExperimentSpec
from bioreason.schemas.workflow import WorkflowPlan


def load_yaml_or_json(path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        elif path.suffix == ".json":
            return json.load(f)
        else:
            # Attempt json first, then yaml
            content = f.read()
            try:
                return json.loads(content)
            except Exception:
                return yaml.safe_load(content)


def load_episode(path: Union[str, Path]) -> ScientificReasoningEpisode:
    data = load_yaml_or_json(path)
    return ScientificReasoningEpisode.model_validate(data)


def load_benchmark_item(path: Union[str, Path]) -> BenchmarkItem:
    data = load_yaml_or_json(path)
    return BenchmarkItem.model_validate(data)


def load_experiment_spec(path: Union[str, Path]) -> ExperimentSpec:
    data = load_yaml_or_json(path)
    return ExperimentSpec.model_validate(data)


def load_workflow_plan(path: Union[str, Path]) -> WorkflowPlan:
    data = load_yaml_or_json(path)
    return WorkflowPlan.model_validate(data)


def load_episodes_from_dir(directory: Union[str, Path]) -> List[ScientificReasoningEpisode]:
    directory = Path(directory)
    episodes = []
    for file_path in directory.glob("**/*"):
        if file_path.suffix in [".json", ".yaml", ".yml"] and file_path.is_file():
            try:
                episodes.append(load_episode(file_path))
            except Exception as e:
                # If file doesn't match episode schema, skip or raise
                pass
    return episodes


def load_benchmark_from_dir(directory: Union[str, Path]) -> List[BenchmarkItem]:
    directory = Path(directory)
    items = []
    for file_path in directory.glob("**/*"):
        if file_path.suffix in [".json", ".yaml", ".yml"] and file_path.is_file():
            try:
                items.append(load_benchmark_item(file_path))
            except Exception:
                pass
    return items

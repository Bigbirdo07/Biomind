"""
Generates 45 hand-curated high-quality scientific reasoning episodes (BioReasonTrain v0.2)
and 45 held-out benchmark items (BioReasonBench v0.2) for Phase 1.
"""

import json
from pathlib import Path

TRAIN_DIR = Path("training_data/examples")
BENCH_DIR = Path("benchmark/examples")
CONFIGS_DIR = Path("configs/examples")

TRAIN_DIR.mkdir(parents=True, exist_ok=True)
BENCH_DIR.mkdir(parents=True, exist_ok=True)
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# Load or Define 45 Training Episodes
# -------------------------------------------------------------------------

from generate_phase1_dataset_data import get_all_training_episodes, get_all_benchmark_items

episodes = get_all_training_episodes()
benchmark_items = get_all_benchmark_items()

# Write all training episodes
for ep in episodes:
    file_path = TRAIN_DIR / f"{ep['episode_id'].lower()}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(ep, f, indent=2)

# Write all benchmark items
for item in benchmark_items:
    file_path = BENCH_DIR / f"{item['item_id'].lower()}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2)

print(f"Generated {len(episodes)} training episodes and {len(benchmark_items)} benchmark items.")

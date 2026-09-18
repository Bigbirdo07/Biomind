#!/usr/bin/env python
"""
Live BioReason chat integration check.

This script intentionally requires the real BioReason inference route. It does
not accept mock adapters or static responses as a successful validation.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bioreason.models.inference_router import BioReasonInferenceError, BioReasonInferenceRouter


TEST_TURNS = [
    "hello",
    "what can you do",
    "Build me an RNA-seq pipeline.",
    "I have 18 tumor and 17 normal independent patients, batch column sequencing_batch, counts at /scratch/project/cancer/counts.csv.",
    "Why are you using PCA?",
    "Which genes drive PC1?",
    "Actually use 50 PCs.",
    "Where do I change the file path?",
]


def main() -> int:
    router = BioReasonInferenceRouter(ROOT)
    print(json.dumps({"startup_status": router.startup_status}, indent=2))
    messages = []
    transcript = []
    for user_text in TEST_TURNS:
        messages.append({"role": "user", "content": user_text})
        start = time.perf_counter()
        try:
            result = router.generate(messages)
        except BioReasonInferenceError as exc:
            print("BIOREASON_INFERENCE_FAILED")
            print(str(exc))
            return 2
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        messages.append({"role": "assistant", "content": result.text})
        transcript.append(
            {
                "user": user_text,
                "assistant": result.text,
                "model": result.model,
                "checkpoint": result.checkpoint,
                "backend": result.backend,
                "device": result.device,
                "precision": result.precision,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "latency_ms": elapsed_ms,
            }
        )
    print(json.dumps({"transcript": transcript}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

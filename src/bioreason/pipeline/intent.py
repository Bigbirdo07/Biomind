"""
src/bioreason/pipeline/intent.py

Pipeline Intent Classifier for BioReason.
Determines whether a user turn is:
- PIPELINE_BUILD: Requesting creation or extension of a computational pipeline
- PIPELINE_DEBUG: Reporting an error, exception, or troubleshooting issue with a pipeline
- PIPELINE_EXPLAIN: Asking "why", "how", or conceptual questions about a pipeline stage/method (e.g. PCA loadings)
- CODE_ONLY: Asking directly for the raw code script
- SCIENTIFIC_AUDIT: Asking to critique or audit an experimental design / methodology
- GENERAL_CHAT: Conversational inquiries, confirmations ("yes"), parameter adjustments ("change to 50 PCs")
"""

import re
from typing import Optional, Dict, Any, List
from bioreason.schemas.guided_pipeline import PipelineIntent, PipelineState, PipelineContext


class PipelineIntentClassifier:
    """Classifies user intent within the BioReason conversational context."""

    def __init__(self, model_adapter: Optional[Any] = None):
        self.model_adapter = model_adapter

    def classify(self, message: str, current_state: PipelineState, context: Optional[PipelineContext] = None) -> PipelineIntent:
        text = message.strip().lower()

        # 1. Check for explicit error / traceback / debugging intent
        if any(err in text for err in ["filenotfounderror", "valueerror", "indexerror", "traceback", "error:", "failed", "crash", "bug"]):
            return PipelineIntent.PIPELINE_DEBUG

        # 2. Check for explanation intent ("why pca", "why did you", "what is loading", "scores vs loadings", "which genes drive")
        if any(kw in text for kw in ["why pca", "why did you", "what is loading", "scores vs", "which genes", "explain pca", "how does pca", "why log", "why standardize", "what does that mean"]):
            return PipelineIntent.PIPELINE_EXPLAIN

        # 3. Check for code request intent ("where is the code", "show me the code", "give me code", "code please", "show script")
        if any(kw in text for kw in ["where is the code", "show me the code", "give me the code", "view code", "generate code", "show script", "where is code", "give code"]):
            return PipelineIntent.CODE_ONLY

        # 4. Check for pipeline build intent
        pipeline_keywords = [
            "build an rna-seq", "build rna-seq", "build pipeline", "create pipeline", "make pipeline",
            "guided pipeline", "differential expression pipeline", "single cell pipeline", "scrna pipeline",
            "bulk rna-seq pipeline", "rnaseq pipeline", "rna-seq differential-expression pipeline",
            "rna-seq differential expression pipeline", "pipeline for", "construct pipeline", "workflow for"
        ]
        if any(kw in text for kw in pipeline_keywords):
            return PipelineIntent.PIPELINE_BUILD

        # 5. Check if currently in an active pipeline flow
        if current_state in [PipelineState.INTAKE_REQUIRED, PipelineState.INTAKE_PARTIAL, PipelineState.READY_TO_PLAN, PipelineState.PLAN_READY, PipelineState.CODE_READY]:
            # If user provides data/counts/paths or answers intake
            if any(term in text for term in ["count", "counts", "fastq", "tumor", "normal", "sample", "patient", "independent", "paired", "batch", "path", "/scratch", "/data", ".csv", ".tsv", "n_pcs", "change to", "50 pcs", "yes", "no"]):
                return PipelineIntent.PIPELINE_BUILD

        # 6. Check for scientific audit
        if any(kw in text for kw in ["audit", "critique", "evaluate design", "pseudoreplication", "leakage", "flaw in"]):
            return PipelineIntent.SCIENTIFIC_AUDIT

        return PipelineIntent.GENERAL_CHAT

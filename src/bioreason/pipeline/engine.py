"""
src/bioreason/pipeline/engine.py

Central Guided Pipeline Reasoning Engine for BioReason.
Coordinates multi-turn conversation memory, intent classification,
experimental intake validation, rule auditing, and dynamic code generation.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from bioreason.schemas.guided_pipeline import (
    PipelineIntent,
    PipelineState,
    ResponseSource,
    PipelineContext,
    GuidedPipelineData,
    GuidedPipelineResponse,
)
from bioreason.models.base import GenerationConfig
from bioreason.models.inference_router import BioReasonInferenceError, BioReasonInferenceRouter
from bioreason.rules.engine import ScientificRuleEngine
from .intent import PipelineIntentClassifier
from .state_machine import PipelineStateManager
from .generator import GuidedPipelineGenerator
from .file_inspector import FileInspector


class BioReasonPipelineEngine:
    """Core reasoning engine powering dynamic Guided Pipeline Mode."""

    def __init__(self, model_adapter: Optional[Any] = None):
        self.model_adapter = model_adapter
        self.inference_router = None if model_adapter else BioReasonInferenceRouter(Path(__file__).resolve().parent.parent.parent.parent)
        self.state_managers: Dict[str, PipelineStateManager] = {}
        self.intent_classifier = PipelineIntentClassifier(model_adapter)
        self.generator = GuidedPipelineGenerator()
        self.rule_engine = ScientificRuleEngine()
        self.file_inspector = FileInspector()
        self.recent_responses: Dict[str, List[str]] = {}

    def get_or_create_state_manager(self, session_id: str) -> PipelineStateManager:
        if session_id not in self.state_managers:
            self.state_managers[session_id] = PipelineStateManager()
        return self.state_managers[session_id]

    def process_turn(
        self,
        session_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        attached_file_path: Optional[str] = None,
        dev_mode: bool = False,
    ) -> GuidedPipelineResponse:
        start = time.perf_counter()
        mgr = self.get_or_create_state_manager(session_id)
        raw_text = user_message.strip()
        lower_text = raw_text.lower()

        # 1. If file attached, inspect it
        file_info = None
        if attached_file_path:
            file_info = self.file_inspector.inspect_file(attached_file_path)
            if "file_path" in file_info:
                if file_info.get("is_count_matrix"):
                    mgr.context.file_paths["counts"] = file_info["file_path"]
                    mgr.context.input_type = "count_matrix"
                elif file_info.get("is_metadata"):
                    mgr.context.file_paths["metadata"] = file_info["file_path"]

        # 2. Extract experimental details from user text
        extracted = mgr.update_from_user_text(raw_text)

        # 3. Classify intent
        intent = self.intent_classifier.classify(raw_text, mgr.state, mgr.context)

        # 4. State Machine Routing

        def with_provenance(response: GuidedPipelineResponse, source: ResponseSource) -> GuidedPipelineResponse:
            latency_ms = int((time.perf_counter() - start) * 1000)
            response.source_trace = source
            response.provenance = {
                "conversation_id": session_id,
                "turn_id": len(conversation_history or []) + 1,
                "model": "BR-VERIFIED-SFT-002",
                "checkpoint": "BR-VERIFIED-SFT-002 (final_adapter)",
                "response_source": source.value,
                "mode": response.mode,
                "pipeline_state": response.pipeline_state.value,
                "pipeline_state_snapshot": response.pipeline_context.model_dump() if response.pipeline_context else None,
                "generation_parameters": None,
                "latency_ms": latency_ms,
            }
            self._record_response(session_id, response.message)
            return response

        if "what did you change" in lower_text or "what changed" in lower_text:
            last_change = mgr.context.inferred_fields.get("last_change")
            msg = last_change or "I have not recorded a pipeline parameter change in this conversation yet."
            if last_change and "N_PCS" in last_change:
                msg = (
                    f"I changed the PCA configuration: `{last_change}`.\n\n"
                    f"In the generated code this is the `N_PCS = {mgr.context.n_pcs}` line in "
                    f"`1. User Configuration & File Paths`, and the PCA chunk now computes up to "
                    f"{mgr.context.n_pcs} principal components."
                )
            return with_provenance(GuidedPipelineResponse(
                status="success",
                mode="conversational",
                message=msg,
                pipeline_state=mgr.state,
                pipeline_context=mgr.context,
                guided_pipeline=mgr.generated_pipeline,
                diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state},
            ), ResponseSource.BACKEND_DERIVED)

        if "n_pcs" in extracted:
            if mgr.generated_pipeline:
                mgr.generated_pipeline = self.generator.build_guided_pipeline(mgr.context)
            return with_provenance(GuidedPipelineResponse(
                status="success",
                mode="guided_pipeline" if mgr.generated_pipeline else "conversational",
                message=(
                    f"Done. I updated the PCA configuration to `N_PCS = {mgr.context.n_pcs}`. "
                    f"This changes the PCA scores output to use up to {mgr.context.n_pcs} principal components; "
                    f"the file paths and experimental design are unchanged."
                ),
                pipeline_state=mgr.state,
                pipeline_context=mgr.context,
                guided_pipeline=mgr.generated_pipeline,
                diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state},
            ), ResponseSource.BACKEND_DERIVED)

        # Case A: User asks "where is the code?", "show code", "give script"
        if intent == PipelineIntent.CODE_ONLY or ("code" in lower_text and any(k in lower_text for k in ["where", "show", "give", "view"])):
            if mgr.generated_pipeline:
                return with_provenance(GuidedPipelineResponse(
                    status="success",
                    mode="guided_pipeline",
                    message="Here is the synchronized Code and Guide view for your pipeline:",
                    pipeline_state=PipelineState.CODE_READY,
                    pipeline_context=mgr.context,
                    guided_pipeline=mgr.generated_pipeline,
                    diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state}
                ), ResponseSource.BACKEND_DERIVED)
            else:
                # Generate from context
                pipeline_data = self.generator.build_guided_pipeline(mgr.context)
                mgr.generated_pipeline = pipeline_data
                mgr.state = PipelineState.CODE_READY
                return with_provenance(GuidedPipelineResponse(
                    status="success",
                    mode="guided_pipeline",
                    message="Here is the synchronized Code and Guide view for your pipeline:",
                    pipeline_state=PipelineState.CODE_READY,
                    pipeline_context=mgr.context,
                    guided_pipeline=pipeline_data,
                    diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state}
                ), ResponseSource.BACKEND_DERIVED)

        # Case B: Explanation follow-up (e.g. "why pca?", "which genes drive pc1?", "scores vs loadings")
        if intent == PipelineIntent.PIPELINE_EXPLAIN or any(q in lower_text for q in ["why pca", "why did you use pca", "which genes", "pc1", "loadings", "scores vs"]):
            n_pcs = mgr.context.n_pcs or 20
            exp_unit = mgr.context.experimental_unit or "Patient"
            if "which genes" in lower_text or "drive pc1" in lower_text or "loading" in lower_text:
                resp_text = (
                    f"### Gene Loadings & PC1 Drivers\n\n"
                    f"In this pipeline, **PC1** represents the axis of greatest transcriptomic variance across your `{exp_unit}` cohort. "
                    f"Mathematically:\n\n"
                    f"$$PC_1 = w_1 \\cdot \\text{{Gene}}_1 + w_2 \\cdot \\text{{Gene}}_2 + \\dots + w_n \\cdot \\text{{Gene}}_n$$\n\n"
                    f"- **Loadings ($w_i$)** measure the weight and direction each individual gene contributes to PC1. In scikit-learn, these are accessed via `pca.components_[0]`.\n"
                    f"- **Scores** represent the coordinate of each individual sample along that PC axis.\n\n"
                    f"In **Chunk 5 (PCA & Gene Loadings Analysis)**, top positive and negative drivers are extracted and exported to `results/pca_gene_loadings.csv`."
                )
            else:
                resp_text = (
                    f"### Why PCA is Used in This Workflow\n\n"
                    f"1. **Unsupervised Cohort Inspection**: PCA reduces thousands of gene expression dimensions into orthogonal principal components (top {n_pcs} PCs) to inspect whether samples naturally cluster by biological group (or whether technical batch confounders dominate).\n"
                    f"2. **Variance Capture**: PCA identifies dominant directions of biological variation without using class labels (avoiding supervised overfitting).\n"
                    f"3. **Loadings Interpretation**: Unlike non-linear embeddings (t-SNE/UMAP), PCA is directly interpretable: each component is a linear combination of original genes."
                )

            return with_provenance(GuidedPipelineResponse(
                status="success",
                mode="conversational",
                message=resp_text,
                pipeline_state=mgr.state,
                pipeline_context=mgr.context,
                guided_pipeline=mgr.generated_pipeline,
                diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state}
            ), ResponseSource.BACKEND_DERIVED)

        # Case C: Debugging / Error Traceback
        if intent == PipelineIntent.PIPELINE_DEBUG:
            mgr.state = PipelineState.DEBUGGING
            error_diag = self._diagnose_pipeline_error(raw_text, mgr.context)
            return with_provenance(GuidedPipelineResponse(
                status="success",
                mode="conversational",
                message=error_diag,
                pipeline_state=PipelineState.DEBUGGING,
                pipeline_context=mgr.context,
                guided_pipeline=mgr.generated_pipeline,
                diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state}
            ), ResponseSource.BACKEND_DERIVED)

        # Case D: Pipeline Build / Intake Progress.
        #
        # Only the "enough info is known -> generate real code" branch stays
        # deterministic/BACKEND_DERIVED (legitimate mechanical codegen from
        # already-extracted structured facts). The "info is missing -> ask
        # about it" branch used to return a canned template gated entirely
        # by a narrow regex extractor (state_machine.update_from_user_text)
        # that only recognizes a fixed vocabulary (groups must be exactly
        # tumor/normal/treated/control/..., "independent" must say the
        # literal phrase "independent patient", input format must say
        # "h5ad"/"10x"/"scrna", etc). Any real conversation outside that
        # vocabulary (e.g. a non-human species, an unlisted group naming
        # scheme, a file format the regex doesn't recognize) left `missing`
        # permanently non-empty, so this branch re-asked the exact same
        # canned question every turn regardless of what the user actually
        # said -- bypassing the real model, the mode router, and even the
        # repeat-response guard below (which only covers the model-generated
        # path). Found via live product testing. Fixed by falling through
        # to the real model call instead of returning a canned prompt: the
        # PIPELINE_INTAKE mode overlay already asks for missing info in
        # natural, context-aware language and correctly transitions once
        # real info arrives (verified in live testing), without being
        # gated by this extractor's narrow vocabulary.
        if intent == PipelineIntent.PIPELINE_BUILD or mgr.state in [PipelineState.INTAKE_REQUIRED, PipelineState.INTAKE_PARTIAL, PipelineState.READY_TO_PLAN]:
            missing = mgr.get_missing_required_fields()

            if missing:
                mgr.state = PipelineState.INTAKE_REQUIRED
                # Fall through to the real model call below instead of
                # returning a canned, extractor-gated template.
            else:
                # All required info is present -> Build Plan and Full Guided Pipeline
                mgr.state = PipelineState.CODE_READY
                pipeline_data = self.generator.build_guided_pipeline(mgr.context)
                mgr.generated_pipeline = pipeline_data

                summary_msg = (
                    f"### Experimental Design Foundation Established\n\n"
                    f"- **Experimental Unit**: `{mgr.context.experimental_unit or 'Patient'}` ({mgr.context.sample_count} samples: {', '.join(f'{g}: {c}' for g, c in mgr.context.group_counts.items())})\n"
                    f"- **Study Design**: `{'Paired within subject' if mgr.context.paired_design else 'Independent biological subjects'}`\n"
                    f"- **Batch Factor**: `{mgr.context.batch_columns[0] if mgr.context.batch_columns else 'None declared (inspecting in PCA)'}`\n"
                    f"- **Input File**: `{mgr.context.file_paths.get('counts', '/PATH/TO/counts.csv')}`\n\n"
                    f"I have constructed your customized Guided Pipeline with synchronized Code and Guide panes below:"
                )

                return with_provenance(GuidedPipelineResponse(
                    status="success",
                    mode="guided_pipeline",
                    message=summary_msg,
                    pipeline_state=PipelineState.CODE_READY,
                    pipeline_context=mgr.context,
                    guided_pipeline=pipeline_data,
                    diagnostics={"intent": intent, "extracted": extracted, "state": mgr.state}
                ), ResponseSource.BACKEND_DERIVED)

        # Case E (Scientific Audit Request) intentionally removed: it previously
        # returned hand-coded, fabricated audit text (e.g. "Workflow structure
        # is methodologically sound.") tagged BACKEND_DERIVED -- not a real
        # model call. Per the project's verified-generation-only principle,
        # SCIENTIFIC_AUDIT now falls through to the real model call below,
        # where the server-side mode router independently (and reliably,
        # given the explicit "audit" language that triggered this legacy
        # keyword classification) selects SCIENTIFIC_AUDIT mode and applies
        # the structured-audit overlay to a genuine MODEL_GENERATED response.

        # Default / General turn: real model call, routed through the
        # mode router + overlay orchestrator on the serving side (see
        # bioreason.inference.orchestrator). No local system prompt is
        # constructed here -- the orchestrator selects the mode-appropriate
        # system prompt itself from the actual conversation.
        history_messages = self._build_model_history(conversation_history or [])
        pipeline_context_summary = self._summarize_pipeline_context(mgr.context)
        config = GenerationConfig(max_new_tokens=768, temperature=0.3, top_p=0.9, do_sample=True)
        try:
            if self.model_adapter:
                prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history_messages) + f"\nUSER: {raw_text}\nASSISTANT:"
                model_text = self.model_adapter.generate(prompt, config)
                model_meta = {
                    "backend": "injected_adapter",
                    "input_tokens": None,
                    "output_tokens": None,
                    "device": "test_adapter",
                    "precision": "unknown",
                    "router_mode": None,
                    "router_confidence": None,
                }
                resolved_mode = "conversational"
            else:
                inference = self.inference_router.generate(
                    history_messages, raw_text, pipeline_context_summary, config
                )
                model_text = inference.text
                model_meta = inference.__dict__
                resolved_mode = (inference.router_mode or "conversational").lower()
        except BioReasonInferenceError as exc:
            raise exc

        if self._is_suspicious_repeat(session_id, model_text):
            raise BioReasonInferenceError("BIOREASON_INFERENCE_FAILED: suspicious repeated response detected.")

        resp = GuidedPipelineResponse(
            status="success",
            mode=resolved_mode,
            message=model_text,
            pipeline_state=mgr.state,
            pipeline_context=mgr.context,
            diagnostics={"intent": intent, "state": mgr.state, "model_status": model_meta},
        )
        resp = with_provenance(resp, ResponseSource.MODEL_GENERATED)
        resp.provenance["generation_parameters"] = config.model_dump()
        resp.provenance.update(model_meta)
        if model_meta.get("checkpoint"):
            resp.model_checkpoint = model_meta["checkpoint"]
        return resp

    def _build_model_history(
        self,
        conversation_history: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """Plain user/assistant history, no system prompt -- the mode router/
        overlay orchestrator on the serving side selects the mode-appropriate
        system prompt itself, based on this history and the latest message."""
        messages: List[Dict[str, str]] = []
        for msg in conversation_history[-12:]:
            role = msg.get("role")
            if role in {"user", "assistant"} and msg.get("content"):
                messages.append({"role": role, "content": str(msg["content"])})
        return messages

    def _summarize_pipeline_context(self, context: PipelineContext) -> Optional[str]:
        """One-line, human-readable summary of the known experiment facts,
        passed to the router/overlay orchestrator as pipeline_context_summary
        so it can factor known context into PIPELINE_* mode decisions without
        needing the full PipelineContext schema."""
        parts = []
        if context.sample_count:
            parts.append(f"{context.sample_count} samples")
        if context.group_counts:
            parts.append(", ".join(f"{g}: {c}" for g, c in context.group_counts.items()))
        if context.experimental_unit:
            parts.append(f"unit={context.experimental_unit}")
        if context.paired_design is not None:
            parts.append("paired" if context.paired_design else "independent")
        if context.batch_columns:
            parts.append(f"batch={context.batch_columns[0]}")
        if context.file_paths:
            parts.append(", ".join(f"{k}={v}" for k, v in context.file_paths.items()))
        return "; ".join(parts) if parts else None

    def _record_response(self, session_id: str, text: str) -> None:
        if not text:
            return
        normalized = " ".join(text.lower().split())
        recent = self.recent_responses.setdefault(session_id, [])
        recent.append(normalized)
        del recent[:-5]

    def _is_suspicious_repeat(self, session_id: str, text: str) -> bool:
        normalized = " ".join((text or "").lower().split())
        if not normalized:
            return False
        recent = self.recent_responses.get(session_id, [])
        return recent.count(normalized) >= 1 and len(normalized) > 120

    def _diagnose_pipeline_error(self, error_text: str, context: PipelineContext) -> str:
        lower = error_text.lower()
        if "filenotfounderror" in lower:
            counts_p = context.file_paths.get("counts", "/PATH/TO/counts.csv")
            return (
                f"### 🔍 Diagnostic: File Not Found Error\n\n"
                f"- **Pipeline Stage**: `Stage 1: User Configuration & File Paths` (or `Stage 2: Metadata Loading`)\n"
                f"- **Likely Cause**: The path `{counts_p}` does not exist on the current filesystem or lacks read permissions.\n"
                f"- **What to Check**: Run `ls -l {counts_p}` or `pwd` in your terminal to confirm the exact absolute path.\n"
                f"- **How to Fix**: Update `COUNTS_FILE = \"...\"` in Chunk 1 or type the path into the interactive configuration field at the top of the pipeline."
            )
        elif "inconsistent numbers of samples" in lower or "mismatch" in lower or "keyerror" in lower:
            return (
                f"### 🔍 Diagnostic: Sample ID Index Mismatch\n\n"
                f"- **Pipeline Stage**: `Stage 2 / Stage 3: Metadata Alignment & Filtering`\n"
                f"- **Likely Cause**: The sample column names in your count matrix do not match the row index of your metadata table.\n"
                f"- **How to Fix**:\n"
                f"```diff\n"
                f"- counts = pd.read_csv(COUNTS_FILE, index_col=0)\n"
                f"+ counts = pd.read_csv(COUNTS_FILE, index_col=0)\n"
                f"+ counts.columns = counts.columns.str.strip()  # remove leading/trailing whitespace\n"
                f"```"
            )
        else:
            return (
                f"### 🔍 Contextual Pipeline Troubleshooting\n\n"
                f"- **Detected Issue**: Runtime exception encountered during execution.\n"
                f"- **Context**: {context.sample_count or 'Unknown'} samples, {context.experimental_unit or 'Patient'} level.\n"
                f"- **Recommended Remediation**: Inspect intermediate tensor shapes before the failing operation using `print(X.shape)`."
            )

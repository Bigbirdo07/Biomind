"""
Production inference routing for BioReason chat.

This module deliberately does not synthesize scientific answers when the model is
unavailable. It either returns text from the configured BioReason checkpoint /
remote Unity endpoint, or raises an explicit inference error.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import GenerationConfig
from .hf_adapter import HuggingFaceModelAdapter


BIOREASON_VERSION = "v0.2"
BIOREASON_MODEL_NAME = "BR-VERIFIED-SFT-002"
BIOREASON_BASE_MODEL = "Qwen/Qwen2.5-14B-Instruct"
BIOREASON_CHECKPOINT = "BR-VERIFIED-SFT-002 (final_adapter)"
DEFAULT_LOCAL_CHECKPOINT = "outputs/verified_training/BR-VERIFIED-SFT-002/final_adapter"


class BioReasonInferenceError(RuntimeError):
    """Raised when real BioReason inference cannot be performed."""


@dataclass
class InferenceResult:
    text: str
    model: str
    checkpoint: str
    backend: str
    device: str
    precision: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: int
    router_mode: Optional[str] = None
    router_confidence: Optional[float] = None


class BioReasonInferenceRouter:
    """Routes chat prompts to local BioReason weights or a private Unity server."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.backend = os.environ.get("BIOREASON_BACKEND", "local").strip().lower()
        self.local_checkpoint = Path(
            os.environ.get("BIOREASON_CHECKPOINT_PATH", str(workspace_dir / DEFAULT_LOCAL_CHECKPOINT))
        )
        self.unity_url = os.environ.get("BIOREASON_UNITY_URL", "").strip()
        self.precision = os.environ.get("BIOREASON_PRECISION", "bfloat16")
        self._adapter: Optional[HuggingFaceModelAdapter] = None
        self._startup_status = self._probe_startup_status()

    @property
    def startup_status(self) -> Dict[str, Any]:
        return dict(self._startup_status)

    def _probe_startup_status(self) -> Dict[str, Any]:
        if self.backend == "unity":
            if not self.unity_url:
                return {
                    "bioreason_version": BIOREASON_VERSION,
                    "base_model": BIOREASON_BASE_MODEL,
                    "checkpoint": BIOREASON_CHECKPOINT,
                    "backend": "unity",
                    "device": "UNAVAILABLE",
                    "precision": self.precision,
                    "status": "UNAVAILABLE",
                    "detail": "BIOREASON_UNITY_URL is not configured",
                }
            # Query the live server's own /health rather than trusting a static
            # constant -- status always reflects whichever model is actually
            # running on the currently-connected Unity job, no manual syncing
            # needed when a different checkpoint (e.g. 14B vs 32B) is served.
            try:
                req = urllib.request.Request(self.unity_url.rstrip("/") + "/health")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    health = json.loads(resp.read().decode("utf-8"))
                if health.get("status") == "READY":
                    adapter_name = Path(str(health.get("adapter_path", ""))).name or BIOREASON_MODEL_NAME
                    return {
                        "bioreason_version": BIOREASON_VERSION,
                        "base_model": health.get("base_model", BIOREASON_BASE_MODEL),
                        "checkpoint": f"{adapter_name} (final_adapter)",
                        "adapter_sha256": health.get("adapter_sha256"),
                        "backend": "unity",
                        "device": health.get("device", "Unity GPU via private endpoint"),
                        "precision": self.precision,
                        "status": "READY",
                        "detail": f"Connected to live Unity server at {self.unity_url}",
                    }
                return {
                    "bioreason_version": BIOREASON_VERSION,
                    "base_model": BIOREASON_BASE_MODEL,
                    "checkpoint": BIOREASON_CHECKPOINT,
                    "backend": "unity",
                    "device": "UNAVAILABLE",
                    "precision": self.precision,
                    "status": "UNAVAILABLE",
                    "detail": f"Unity server at {self.unity_url} reported status={health.get('status')}",
                }
            except (urllib.error.URLError, OSError, ValueError) as exc:
                return {
                    "bioreason_version": BIOREASON_VERSION,
                    "base_model": BIOREASON_BASE_MODEL,
                    "checkpoint": BIOREASON_CHECKPOINT,
                    "backend": "unity",
                    "device": "UNAVAILABLE",
                    "precision": self.precision,
                    "status": "UNAVAILABLE",
                    "detail": f"Unity endpoint unreachable at {self.unity_url}: {exc}",
                }

        required = ["adapter_config.json", "adapter_model.safetensors"]
        present = {name: (self.local_checkpoint / name).exists() for name in required}
        ready = self.local_checkpoint.exists() and all(present.values())
        return {
            "bioreason_version": BIOREASON_VERSION,
            "base_model": BIOREASON_BASE_MODEL,
            "checkpoint": BIOREASON_CHECKPOINT,
            "checkpoint_path": str(self.local_checkpoint),
            "backend": "local",
            "device": "auto" if ready else "UNAVAILABLE",
            "precision": self.precision,
            "status": "READY" if ready else "UNAVAILABLE",
            "detail": "Local adapter weights found" if ready else f"Missing local checkpoint files: {present}",
        }

    def print_startup_banner(self) -> None:
        status = self.startup_status
        print("BioReason Version:", status["bioreason_version"])
        print("Base:", status["base_model"])
        print("Checkpoint:", status["checkpoint"])
        print("Backend:", status["backend"])
        print("Device:", status["device"])
        print("Precision:", status["precision"])
        print("Status:", status["status"])
        if status.get("detail"):
            print("Detail:", status["detail"])

    def generate(
        self,
        history: List[Dict[str, str]],
        user_message: str,
        pipeline_context_summary: Optional[str] = None,
        config: Optional[GenerationConfig] = None,
    ) -> InferenceResult:
        start = time.perf_counter()
        if self.backend == "unity":
            result = self._generate_unity(history, user_message, pipeline_context_summary, config)
        else:
            result = self._generate_local(history, user_message, pipeline_context_summary, config)
        result.latency_ms = int((time.perf_counter() - start) * 1000)
        return result

    def _generate_local(
        self,
        history: List[Dict[str, str]],
        user_message: str,
        pipeline_context_summary: Optional[str],
        config: Optional[GenerationConfig],
    ) -> InferenceResult:
        if self.startup_status["status"] != "READY":
            raise BioReasonInferenceError(
                "LOCAL_MODEL_RESOURCE_BLOCKER: BioReason checkpoint weights are unavailable locally. "
                f"Expected adapter at {self.local_checkpoint}."
            )

        if self._adapter is None:
            self._adapter = HuggingFaceModelAdapter(
                model_name_or_path=BIOREASON_BASE_MODEL,
                adapter_path=str(self.local_checkpoint),
                load_in_4bit=os.environ.get("BIOREASON_LOAD_IN_4BIT", "1") == "1",
                device_map="auto",
                torch_dtype=self.precision,
            )

        # Route through the same mode router/overlay orchestrator used by the
        # Unity live server, so local and remote backends behave identically
        # (mode-conditioned, MODEL_GENERATED — never a fixed canned prompt).
        from bioreason.inference.orchestrator import run_orchestrated_turn

        gen_config = config or GenerationConfig(max_new_tokens=1024, temperature=0.2, do_sample=True)

        def local_generate_fn(messages: List[Dict[str, str]], max_new_tokens: int) -> str:
            prompt = self._format_messages(messages)
            local_config = GenerationConfig(
                max_new_tokens=max_new_tokens,
                temperature=gen_config.temperature,
                do_sample=gen_config.do_sample,
                top_p=gen_config.top_p,
                repetition_penalty=gen_config.repetition_penalty,
            )
            return self._adapter.generate(prompt, local_config).strip()

        result = run_orchestrated_turn(
            generate_fn=local_generate_fn,
            history=history,
            user_message=user_message,
            pipeline_context_summary=pipeline_context_summary,
            main_max_new_tokens=gen_config.max_new_tokens,
        )
        return InferenceResult(
            text=result.response,
            model=BIOREASON_MODEL_NAME,
            checkpoint=BIOREASON_CHECKPOINT,
            backend="local",
            device=str(getattr(getattr(self._adapter, "model", None), "device", "auto")),
            precision=self.precision,
            input_tokens=None,
            output_tokens=None,
            latency_ms=0,
            router_mode=result.router.mode,
            router_confidence=result.router.confidence,
        )

    def _generate_unity(
        self,
        history: List[Dict[str, str]],
        user_message: str,
        pipeline_context_summary: Optional[str],
        config: Optional[GenerationConfig],
    ) -> InferenceResult:
        if not self.unity_url:
            raise BioReasonInferenceError("BIOREASON_INFERENCE_FAILED: BIOREASON_UNITY_URL is not configured.")

        payload = {
            "history": history,
            "user_message": user_message,
            "pipeline_context_summary": pipeline_context_summary,
        }
        req = urllib.request.Request(
            self.unity_url.rstrip("/") + "/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise BioReasonInferenceError(f"BIOREASON_INFERENCE_FAILED: Unity endpoint unavailable: {exc}") from exc

        text = str(data.get("text") or "").strip()
        if not text:
            raise BioReasonInferenceError("BIOREASON_INFERENCE_FAILED: Unity endpoint returned an empty response.")

        unity_model_name = str(data.get("model", BIOREASON_MODEL_NAME))
        unity_checkpoint = f"{unity_model_name} (final_adapter)"
        return InferenceResult(
            text=text,
            model=unity_model_name,
            checkpoint=f"{unity_checkpoint} (sha256={data.get('adapter_sha256', '')[:16]}...)" if data.get("adapter_sha256") else unity_checkpoint,
            backend="unity",
            device=str(data.get("device", "Unity GPU")),
            precision=str(data.get("precision", self.precision)),
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            latency_ms=0,
            router_mode=data.get("router_mode"),
            router_confidence=data.get("router_confidence"),
        )

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        lines = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        lines.append("ASSISTANT:")
        return "\n".join(lines)

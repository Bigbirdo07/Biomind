#!/usr/bin/env python3
"""
Persistent inference server for BioReason's verified model.

Loads the base model + a verified adapter ONCE at startup (reusing the same
merge-and-load pattern already proven in verified_conversation_eval.py /
verified_eval.py), keeps it resident in GPU memory, and serves real
model_generate() calls over HTTP — routed through the mode router/overlay
orchestrator (src/bioreason/inference/orchestrator.py) so every response is
genuinely MODEL_GENERATED and mode-conditioned, not canned text.

Unlike every other script in this project (which load, run one batch, and
exit), this process is meant to keep running for the lifetime of a live
chat session, so the local BioReason chat server can call it repeatedly
without incurring a ~1-2 minute model-load cost per turn.

Endpoints:
  GET  /health   -> {"status": "READY", "model", "adapter_sha256", ...}
  POST /generate -> body: {"history": [{"role","content"},...],
                            "user_message": str,
                            "pipeline_context_summary": str | null}
                    response: {"text", "router_mode", "router_confidence",
                               "response_source": "MODEL_GENERATED",
                               "latency_ms"}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.inference.orchestrator import run_orchestrated_turn
from bioreason.training.verified_sft_trainer import sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--max-new-tokens", type=int, default=400)
    parser.add_argument("--router-max-new-tokens", type=int, default=80)
    parser.add_argument("--dtype", default="bfloat16")
    return parser.parse_args()


class ModelState:
    """Holds the loaded model/tokenizer, populated once at startup."""

    model = None
    tokenizer = None
    device = None
    adapter_sha256: str = ""
    base_model_path: str = ""
    adapter_path: str = ""
    max_new_tokens: int = 400
    router_max_new_tokens: int = 80
    load_error: str = ""


STATE = ModelState()


def load_model(args: argparse.Namespace) -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = Path(args.base_model_path)
    adapter = Path(args.adapter_path)
    adapter_file = adapter / "adapter_model.safetensors"
    if not adapter_file.exists():
        raise FileNotFoundError(f"Adapter weights not found: {adapter_file}")

    STATE.adapter_sha256 = sha256_file(adapter_file)
    STATE.base_model_path = str(base)
    STATE.adapter_path = str(adapter)
    STATE.max_new_tokens = args.max_new_tokens
    STATE.router_max_new_tokens = args.router_max_new_tokens

    print(f"Loading base model from {base} ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(base), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(base), torch_dtype=dtype, device_map="auto", trust_remote_code=True,
    )
    print(f"Loading adapter from {adapter} (sha256={STATE.adapter_sha256[:16]}...) ...", flush=True)
    model = PeftModel.from_pretrained(model, str(adapter))
    model = model.merge_and_unload()
    model.eval()

    STATE.model = model
    STATE.tokenizer = tokenizer
    STATE.device = next(model.parameters()).device
    print(f"Model ready on {STATE.device}.", flush=True)


def generate_fn(messages, max_new_tokens: int) -> str:
    import torch

    tokenizer = STATE.tokenizer
    model = STATE.model
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            repetition_penalty=1.0,
            pad_token_id=tokenizer.eos_token_id,
        )
    output_ids = generated[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(output_ids, skip_special_tokens=True).strip()


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            if STATE.load_error:
                self._send_json(503, {"status": "ERROR", "detail": STATE.load_error})
                return
            if STATE.model is None:
                self._send_json(503, {"status": "LOADING"})
                return
            self._send_json(200, {
                "status": "READY",
                "base_model": STATE.base_model_path,
                "adapter_path": STATE.adapter_path,
                "adapter_sha256": STATE.adapter_sha256,
                "device": str(STATE.device),
            })
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/generate":
            self._send_json(404, {"error": "not found"})
            return
        if STATE.model is None:
            self._send_json(503, {"error": "model not ready", "detail": STATE.load_error or "still loading"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"error": f"invalid JSON: {exc}"})
            return

        history = body.get("history") or []
        user_message = body.get("user_message") or ""
        pipeline_context_summary = body.get("pipeline_context_summary")
        if not user_message:
            self._send_json(400, {"error": "user_message is required"})
            return

        t0 = time.time()
        try:
            result = run_orchestrated_turn(
                generate_fn=generate_fn,
                history=history,
                user_message=user_message,
                pipeline_context_summary=pipeline_context_summary,
                main_max_new_tokens=STATE.max_new_tokens,
                router_max_new_tokens=STATE.router_max_new_tokens,
            )
        except Exception as exc:
            self._send_json(500, {"error": f"generation failed: {exc}"})
            return

        latency_ms = int((time.time() - t0) * 1000)
        self._send_json(200, {
            "text": result.response,
            "router_mode": result.router.mode,
            "router_confidence": result.router.confidence,
            "router_explicit_user_request": result.router.explicit_user_request,
            "audit_regeneration_used": result.audit_regeneration_used,
            "code_lint_warnings": result.code_lint_warnings,
            "code_lint_regeneration_used": result.code_lint_regeneration_used,
            "execution_verified": result.execution_verified,
            "execution_error": result.execution_error,
            "execution_regeneration_used": result.execution_regeneration_used,
            "response_source": "MODEL_GENERATED",
            "model": Path(STATE.adapter_path).name,
            "adapter_sha256": STATE.adapter_sha256,
            "latency_ms": latency_ms,
        })

    def log_message(self, fmt, *fmt_args):
        print(f"[{self.log_date_time_string()}] {fmt % fmt_args}", flush=True)


def main() -> None:
    args = parse_args()
    try:
        load_model(args)
    except Exception as exc:
        STATE.load_error = str(exc)
        print(f"MODEL LOAD FAILED: {exc}", flush=True)
        raise

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"BioReason verified model server listening on {args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()

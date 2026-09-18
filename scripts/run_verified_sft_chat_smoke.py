#!/usr/bin/env python3
"""Run a live chat smoke test against a verified SFT LoRA adapter."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_sft_trainer import SYSTEM_PROMPT, sha256_file, write_json


PROMPTS = [
    "hello",
    "what can you do",
    "what is PCA",
    "explain pseudoreplication",
    "Build me an RNA-seq pipeline.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--output", default="outputs/verified_training/BR-VERIFIED-SFT-001/live_chat_smoke.json")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    return parser.parse_args()


def main() -> None:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    args = parse_args()
    adapter = Path(args.adapter_path)
    if not (adapter / "adapter_model.safetensors").exists():
        raise RuntimeError(f"Missing adapter weights: {adapter / 'adapter_model.safetensors'}")
    if (adapter / "adapter_model.safetensors").stat().st_size <= 0:
        raise RuntimeError(f"Zero-byte adapter weights: {adapter / 'adapter_model.safetensors'}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, str(adapter))
    model.eval()

    transcript = []
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for prompt in PROMPTS:
        history.append({"role": "user", "content": prompt})
        text = tokenizer.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt").to(model.device)
        start = time.time()
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )
        output_ids = generated[0][inputs["input_ids"].shape[-1] :]
        response = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        history.append({"role": "assistant", "content": response})
        transcript.append(
            {
                "user": prompt,
                "assistant": response,
                "input_tokens": int(inputs["input_ids"].shape[-1]),
                "output_tokens": int(output_ids.shape[-1]),
                "latency_seconds": time.time() - start,
                "response_source": "MODEL_GENERATED",
            }
        )

    output = Path(args.output)
    write_json(
        output,
        {
            "status": "LIVE_SFT_CHAT_SMOKE_COMPLETE",
            "base_model_path": args.base_model_path,
            "adapter_path": str(adapter),
            "adapter_sha256": sha256_file(adapter / "adapter_model.safetensors"),
            "transcript": transcript,
        },
    )
    print(output)


if __name__ == "__main__":
    main()

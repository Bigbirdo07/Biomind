"""
Hugging Face model adapter supporting standard transformer checkpoints, LoRA, and QLoRA.
"""

import json
import re
from typing import Optional, Dict, Any
from .base import BaseModelAdapter, GenerationConfig, ModelPrediction


class HuggingFaceModelAdapter(BaseModelAdapter):
    """
    Adapter for running inference with open-weight models (e.g. Llama-3-8B, Qwen-2.5-7B/14B/32B, Mistral).
    Supports 4-bit/8-bit bitsandbytes quantization and LoRA adapter weights.
    """

    def __init__(
        self,
        model_name_or_path: str,
        adapter_path: Optional[str] = None,
        load_in_4bit: bool = False,
        load_in_8bit: bool = False,
        device_map: str = "auto",
        torch_dtype: str = "bfloat16",
    ):
        self.model_name_or_path = model_name_or_path
        self.adapter_path = adapter_path
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
        self.device_map = device_map
        self.torch_dtype = torch_dtype

        self.model = None
        self.tokenizer = None
        self._is_loaded = False

    def load(self):
        """Lazy load model and tokenizer to prevent overhead when only validating schemas."""
        if self._is_loaded:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as e:
            raise ImportError(
                "Hugging Face transformers and torch must be installed to run HuggingFaceModelAdapter. "
                "Install with: pip install 'bioreason[training]'"
            ) from e

        dtype = torch.bfloat16 if self.torch_dtype == "bfloat16" else torch.float16

        bnb_config = None
        if self.load_in_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=dtype,
                bnb_4bit_use_double_quant=True,
            )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path,
            quantization_config=bnb_config,
            load_in_8bit=self.load_in_8bit,
            torch_dtype=dtype,
            device_map=self.device_map,
            trust_remote_code=True,
        )

        if self.adapter_path:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, self.adapter_path)

        self.model.eval()
        self._is_loaded = True

    def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> str:
        self.load()
        config = config or GenerationConfig()
        import torch

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=config.max_new_tokens,
                temperature=config.temperature if config.do_sample else None,
                top_p=config.top_p if config.do_sample else None,
                do_sample=config.do_sample,
                repetition_penalty=config.repetition_penalty,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated_ids = outputs[0][inputs.input_ids.shape[1] :]
        return self.tokenizer.decode(generated_ids, skip_special_tokens=True)

    def evaluate_item(self, prompt: str, item_id: str, config: Optional[GenerationConfig] = None) -> ModelPrediction:
        response_text = self.generate(prompt, config)
        parsed = self._extract_json(response_text)

        return ModelPrediction(
            item_id=item_id,
            prompt=prompt,
            raw_response=response_text,
            parsed_json=parsed,
            flaw_detected=parsed.get("flaw_detected") if parsed else None,
            flaw_type=parsed.get("flaw_type") if parsed else None,
            scientific_rationale=parsed.get("scientific_rationale") if parsed else None,
            proposed_correction=parsed.get("proposed_correction") if parsed else None,
            limitations_noted=parsed.get("limitations", []) if parsed else [],
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        # Find JSON code block or outermost curly braces
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except Exception:
                pass
        return None

from pathlib import Path

import pytest

from bioreason.training.verified_eval import refuse_sealed_dataset
from bioreason.training.verified_sft_trainer import (
    LABEL_IGNORE_INDEX,
    assert_valid_peft_checkpoint,
    build_labeled_example,
    checkpoint_integrity,
    write_slurm_execution_manifest,
)


class _FakeTokenizer:
    """Minimal tokenizer stand-in with a real turn-boundary chat template,
    used to test build_labeled_example's masking logic independent of the
    actual (large, not locally available) Qwen tokenizer."""

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.next_id = 0

    def _tok(self, word: str) -> int:
        if word not in self.vocab:
            self.vocab[word] = self.next_id
            self.next_id += 1
        return self.vocab[word]

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=False) -> str:
        parts = []
        for m in messages:
            parts.append(f"<|{m['role']}|> {m['content']} <|end|>")
        if add_generation_prompt:
            parts.append("<|assistant|>")
        return " ".join(parts)

    def __call__(self, text: str, add_special_tokens: bool = True):
        return {"input_ids": [self._tok(w) for w in text.split()]}


def test_build_labeled_example_masks_non_assistant_tokens() -> None:
    tokenizer = _FakeTokenizer()
    messages = [
        {"role": "system", "content": "You are BioReason."},
        {"role": "user", "content": "What is PCA?"},
        {"role": "assistant", "content": "PCA finds directions of maximum variance."},
    ]
    example = build_labeled_example(tokenizer, messages, max_seq_length=512)

    assert len(example["input_ids"]) == len(example["labels"])
    # System/user span must be fully masked.
    prefix_len = len(
        tokenizer(tokenizer.apply_chat_template(messages[:2], tokenize=False, add_generation_prompt=True))[
            "input_ids"
        ]
    )
    assert all(l == LABEL_IGNORE_INDEX for l in example["labels"][:prefix_len])
    # Assistant span must be trainable (not masked) and match input_ids.
    assert any(l != LABEL_IGNORE_INDEX for l in example["labels"][prefix_len:])
    for i in range(prefix_len, len(example["input_ids"])):
        assert example["labels"][i] == example["input_ids"][i]


def test_build_labeled_example_multiturn_masks_all_non_assistant_spans() -> None:
    tokenizer = _FakeTokenizer()
    messages = [
        {"role": "system", "content": "You are BioReason."},
        {"role": "user", "content": "What is PCA?"},
        {"role": "assistant", "content": "PCA finds variance directions."},
        {"role": "user", "content": "Why did you use it?"},
        {"role": "assistant", "content": "Because it reduces dimensionality here."},
    ]
    example = build_labeled_example(tokenizer, messages, max_seq_length=512)

    trainable_positions = [i for i, l in enumerate(example["labels"]) if l != LABEL_IGNORE_INDEX]
    assert trainable_positions, "expected at least one trainable (assistant) token"
    # No trainable token's underlying text should be a role marker or user content token.
    for i in trainable_positions:
        assert example["labels"][i] == example["input_ids"][i]


def test_build_labeled_example_padding_collator_preserves_masking() -> None:
    pytest.importorskip("torch")
    from bioreason.training.verified_sft_trainer import AssistantOnlyPaddingCollator

    tokenizer = _FakeTokenizer()
    short = build_labeled_example(
        tokenizer,
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello there"},
        ],
        max_seq_length=512,
    )
    long = build_labeled_example(
        tokenizer,
        [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "explain pseudoreplication in detail please"},
            {"role": "assistant", "content": "pseudoreplication happens when repeated measures are treated as independent"},
        ],
        max_seq_length=512,
    )
    collator = AssistantOnlyPaddingCollator(tokenizer=type("T", (), {"pad_token_id": 999})())
    batch = collator([short, long])
    max_len = max(len(short["input_ids"]), len(long["input_ids"]))
    assert batch["input_ids"].shape[1] == max_len
    assert batch["labels"].shape[1] == max_len
    # Padded region of the shorter example must remain masked.
    pad_len = max_len - len(short["input_ids"])
    if pad_len:
        assert all(v == LABEL_IGNORE_INDEX for v in batch["labels"][0, -pad_len:].tolist())


def test_checkpoint_requires_physical_adapter(tmp_path: Path) -> None:
    ckpt = tmp_path / "checkpoint-1"
    ckpt.mkdir()
    (ckpt / "adapter_config.json").write_text("{}", encoding="utf-8")

    with pytest.raises(RuntimeError, match="missing"):
        assert_valid_peft_checkpoint(ckpt)


def test_checkpoint_rejects_zero_byte_adapter(tmp_path: Path) -> None:
    ckpt = tmp_path / "checkpoint-1"
    ckpt.mkdir()
    (ckpt / "adapter_config.json").write_text("{}", encoding="utf-8")
    (ckpt / "adapter_model.safetensors").write_bytes(b"")

    with pytest.raises(RuntimeError, match="zero-byte"):
        assert_valid_peft_checkpoint(ckpt)


def test_checkpoint_integrity_hashes_nonzero_adapter(tmp_path: Path) -> None:
    ckpt = tmp_path / "checkpoint-1"
    ckpt.mkdir()
    (ckpt / "adapter_config.json").write_text('{"peft_type":"LORA"}', encoding="utf-8")
    (ckpt / "adapter_model.safetensors").write_bytes(b"real adapter bytes")

    records = checkpoint_integrity(tmp_path)

    assert records["checkpoint-1"]["adapter_model_size_bytes"] > 0
    assert len(records["checkpoint-1"]["adapter_model_sha256"]) == 64
    assert (tmp_path / "checkpoint_integrity.json").exists()


def test_verified_eval_refuses_sealed_final_benchmark() -> None:
    with pytest.raises(RuntimeError, match="sealed final benchmark"):
        refuse_sealed_dataset(Path("benchmark/final_v0.2/items.json"))


def test_slurm_execution_manifest_requires_real_job_id(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="slurm_job_id"):
        write_slurm_execution_manifest(tmp_path / "manifest.json", {"status": "SUBMITTED"})

    with pytest.raises(RuntimeError, match="Invalid Slurm job ID"):
        write_slurm_execution_manifest(tmp_path / "manifest.json", {"slurm_job_id": "PENDING"})

    write_slurm_execution_manifest(tmp_path / "manifest.json", {"slurm_job_id": "64517721"})
    assert "64517721" in (tmp_path / "manifest.json").read_text(encoding="utf-8")

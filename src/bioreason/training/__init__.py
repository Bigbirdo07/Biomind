"""
BioReason training modules.
"""

__all__ = [
    "TrainingConfig",
    "PeftMethod",
    "PrecisionType",
    "LoraConfigSpec",
    "ScientificSFTTrainer",
    "format_episode_to_instruction",
]


def __getattr__(name):
    if name in {"TrainingConfig", "PeftMethod", "PrecisionType", "LoraConfigSpec"}:
        from .config import LoraConfigSpec, PeftMethod, PrecisionType, TrainingConfig

        return {
            "TrainingConfig": TrainingConfig,
            "PeftMethod": PeftMethod,
            "PrecisionType": PrecisionType,
            "LoraConfigSpec": LoraConfigSpec,
        }[name]
    if name in {"ScientificSFTTrainer", "format_episode_to_instruction"}:
        from .sft_trainer import ScientificSFTTrainer, format_episode_to_instruction

        return {
            "ScientificSFTTrainer": ScientificSFTTrainer,
            "format_episode_to_instruction": format_episode_to_instruction,
        }[name]
    raise AttributeError(name)

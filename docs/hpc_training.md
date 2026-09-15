# HPC & UMass Amherst Unity Cluster Training

All BioReason training infrastructure is designed for High-Performance Computing (HPC) environments running the Slurm Workload Manager (e.g. UMass Amherst Unity cluster).

---

## Key HPC Design Requirements

1. **Non-Interactive Execution**: All training pipelines run via batch scripts (`sbatch`) with clear stdout and stderr file redirection.
2. **Preemption & Signal Handling**: Scripts trap `SIGUSR1` (sent prior to time-limit expiry or node preemption) to trigger safe checkpoint saving to durable disk.
3. **Scratch Storage Isolation**: Large Hugging Face model weights and tokenized cache directories are written to `$TMPDIR` or node-local NVMe scratch (`/tmp/$USER/hf_cache`), preventing home directory quota exhaustion.
4. **Checkpoint Resumption**: Training automatically checks for the latest valid checkpoint and resumes optimizer states and token counters seamlessly.

---

## Slurm Job Submission Examples

### Single-GPU Development (QLoRA / Smoke Test)
```bash
sbatch configs/slurm/unity_single_gpu.slurm configs/training/qlora_sft_p0.yaml
```

### Multi-GPU Node Training (LoRA / FSDP)
```bash
sbatch configs/slurm/unity_multi_gpu.slurm configs/training/lora_sft_p0.yaml
```

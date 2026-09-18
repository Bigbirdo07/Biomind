"""
src/bioreason/pipeline/state_machine.py

Manages multi-turn conversation state for BioReason Guided Pipeline Mode.
Extracts user parameters, determines missing required information,
maintains conversation memory across turns, and resolves follow-ups.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from bioreason.schemas.guided_pipeline import (
    PipelineIntent,
    PipelineState,
    PipelineContext,
    PipelineFoundation,
    PipelinePlan,
    ShapeProgressionStep,
    ConfigField,
)


class PipelineStateManager:
    """Maintains pipeline state across conversation turns."""

    def __init__(self):
        self.state = PipelineState.IDLE
        self.context = PipelineContext()
        self.active_plan: Optional[PipelinePlan] = None
        self.generated_pipeline: Optional[Any] = None

    def reset(self):
        self.state = PipelineState.IDLE
        self.context = PipelineContext()
        self.active_plan = None
        self.generated_pipeline = None

    def update_from_user_text(self, text: str) -> Dict[str, Any]:
        """
        Extracts experimental parameters and structural constraints directly from user text.
        Never fabricates values if not mentioned.
        """
        extracted = {}
        raw = text.strip()
        lower = raw.lower()

        # 1. File Path Extraction (absolute or cluster paths)
        path_match = re.search(r'([/\w\.\-]+/(?:[/\w\.\-]+\.(?:csv|tsv|txt|h5ad|fastq|fq|bam|vcf)))', raw, re.IGNORECASE)
        if path_match:
            p = path_match.group(1).strip()
            if "counts" in p.lower() or "matrix" in p.lower() or "expr" in p.lower() or p.endswith(".csv") or p.endswith(".tsv"):
                self.context.file_paths["counts"] = p
                self.context.input_type = self.context.input_type or "count_matrix"
                self.context.matrix_orientation = self.context.matrix_orientation or "genes_x_samples"
                extracted["counts_file"] = p
                extracted["input_type"] = self.context.input_type
            elif "meta" in p.lower():
                self.context.file_paths["metadata"] = p
                extracted["metadata_file"] = p
            else:
                self.context.file_paths["input"] = p
                extracted["input_file"] = p

        # 2. Input format
        if "count matrix" in lower or "counts matrix" in lower or "gene count" in lower or "count table" in lower:
            self.context.input_type = "count_matrix"
            self.context.matrix_orientation = "genes_x_samples"
            extracted["input_type"] = "count_matrix"
        elif "fastq" in lower or "fastq.gz" in lower or "raw reads" in lower:
            self.context.input_type = "fastq"
            extracted["input_type"] = "fastq"
        elif "h5ad" in lower or "single cell" in lower or "10x" in lower or "scrna" in lower:
            self.context.input_type = "h5ad"
            self.context.matrix_orientation = "cells_x_genes"
            extracted["input_type"] = "h5ad"
        elif "bam" in lower:
            self.context.input_type = "bam"
            extracted["input_type"] = "bam"

        # 3. Sample Counts and Groups (e.g. "18 tumor and 17 normal", "20 tumor, 20 normal")
        group_match = re.findall(r'(\d+)\s+([a-zA-Z\-_]+)', lower)
        found_groups = {}
        for count_str, grp_name in group_match:
            if grp_name in ["tumor", "normal", "treated", "control", "infected", "uninfected", "responder", "nonresponder", "cases", "controls"]:
                c = int(count_str)
                name_cap = grp_name.capitalize()
                found_groups[name_cap] = c

        if found_groups:
            self.context.group_counts.update(found_groups)
            self.context.groups = list(self.context.group_counts.keys())
            self.context.sample_count = sum(self.context.group_counts.values())
            extracted["group_counts"] = found_groups
            extracted["sample_count"] = self.context.sample_count

        # 4. Experimental Unit & Pairing
        if "independent patient" in lower or "different patient" in lower or "independent samples" in lower or "unpaired" in lower:
            self.context.experimental_unit = "Patient"
            self.context.observation_unit = "Biopsy"
            self.context.measurement_unit = "Count Matrix"
            self.context.paired_design = False
            self.context.subject_count = self.context.sample_count
            extracted["experimental_unit"] = "Patient"
            extracted["paired_design"] = False
        elif "paired" in lower or "same patient" in lower or "matched" in lower:
            self.context.experimental_unit = "Patient"
            self.context.observation_unit = "Biopsy"
            self.context.paired_design = True
            # In paired design, subject count is half the sample count if tumor/normal paired
            if self.context.sample_count:
                self.context.subject_count = self.context.sample_count // 2
            extracted["experimental_unit"] = "Patient"
            extracted["paired_design"] = True

        # 5. Batch variables
        batch_match = re.search(r'batch (?:column|variable|factor)?\s*(?:is|called|named|=)\s*([a-zA-Z0-9_\-]+)', lower)
        if batch_match:
            b_col = batch_match.group(1).strip()
            if b_col not in self.context.batch_columns:
                self.context.batch_columns.append(b_col)
            extracted["batch_column"] = b_col
        elif "run_id" in lower:
            if "run_id" not in self.context.batch_columns:
                self.context.batch_columns.append("run_id")
            extracted["batch_column"] = "run_id"
        elif "sequencing_batch" in lower:
            if "sequencing_batch" not in self.context.batch_columns:
                self.context.batch_columns.append("sequencing_batch")
            extracted["batch_column"] = "sequencing_batch"

        # 6. Biological question / Analysis Goal
        if "cancer" in lower or "tumor" in lower:
            self.context.biological_question = "Transcriptomic differences and biomarker discovery in tumor vs normal tissue."
            self.context.analysis_goal = "differential_expression_and_pca"
        elif "single cell" in lower or "scrna" in lower:
            self.context.analysis_goal = "clustering_and_cell_typing"

        # 7. Parameter adjustments (e.g. "change to 50 pcs", "n_pcs = 50", "50 pcs", "use 50 components")
        pc_match = re.search(r'(?:change to|use|set|switch to|n_pcs\s*=\s*)?\s*(\d+)\s*(?:pcs|components|principal components)', lower)
        if not pc_match:
            pc_match = re.search(r'(?:change to|use|set|switch to|n_pcs\s*=\s*)\s*(\d+)', lower)

        if pc_match:
            new_pcs = int(pc_match.group(1))
            if 2 <= new_pcs <= 500:
                self.context.n_pcs = new_pcs
                self.context.inferred_fields["last_change"] = f"N_PCS updated to {new_pcs}"
                extracted["n_pcs"] = new_pcs

        return extracted

    def get_missing_required_fields(self) -> List[str]:
        """Identifies minimal required experimental information not yet supplied."""
        missing = []
        if not self.context.input_type:
            missing.append("input_format")
        if not self.context.groups or not self.context.group_counts:
            missing.append("groups_and_replicate_counts")
        if self.context.paired_design is None:
            missing.append("paired_or_independent_design")
        return missing

    def generate_intake_question_prompt(self, missing_fields: List[str]) -> str:
        """Generates conversational, targeted intake questions."""
        questions = []
        q_idx = 1

        if "input_format" in missing_fields:
            questions.append(f"{q_idx}. Are you starting from raw FASTQ files, aligned BAMs, or a gene count matrix (CSV/TSV)?")
            q_idx += 1

        if "groups_and_replicate_counts" in missing_fields:
            questions.append(f"{q_idx}. What are your biological comparison groups (e.g., Tumor vs. Normal, Treated vs. Control), and approximately how many samples are in each?")
            q_idx += 1

        if "paired_or_independent_design" in missing_fields:
            questions.append(f"{q_idx}. Are samples from independent biological subjects (patients/animals) or paired from the same subjects?")
            q_idx += 1

        questions_text = "\n".join(questions)
        return (
            f"Before I construct the pipeline, I need to confirm {len(questions)} key aspects of your experiment to ensure the mathematical and biological models are valid:\n\n"
            f"{questions_text}\n\n"
            f"*(If you have a batch factor such as sequencing run or an existing file path, you can mention that as well.)*"
        )

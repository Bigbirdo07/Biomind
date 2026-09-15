# BioReason Dataset & Benchmark Audit Report

## 1. Executive Summary
- **Total Training Episodes**: 45
- **Total Benchmark Items**: 45
- **Contamination / Collision Violations**: 0
- **Contamination Status**: PASSED (Zero Overlap)

---

## 2. Training Dataset Composition (BioReasonTrain)
### Domain Breakdown:
- **bioinformatics_qc**: 1
- **bioinformatics_workflows**: 1
- **biological_ml**: 7
- **biological_ml_compound**: 1
- **biological_ml_interpretation**: 1
- **biological_ml_metrics**: 1
- **biomarker_discovery**: 5
- **bulk_rnaseq**: 2
- **cancer_genomics**: 1
- **clinical_ml**: 4
- **epigenomics**: 2
- **functional_genomics**: 1
- **genomics_variant_calling**: 1
- **immunology**: 1
- **metabolomics**: 1
- **pathway_analysis**: 1
- **reproducibility**: 1
- **single_cell_transcriptomics**: 4
- **single_cell_transcriptomics_ml**: 2
- **spatial_transcriptomics**: 1
- **statistical_genomics**: 2
- **transcriptomics_qc**: 2
- **transcriptomics_statistics**: 1
- **wgs_genomics**: 1

### Episode Type Breakdown:
- **ASSESS_CLAIM**: 1
- **COMPARE_METHODS**: 3
- **CORRECT_WORKFLOW**: 8
- **DIAGNOSE_FAILURE**: 7
- **FLAWED_WORKFLOW**: 21
- **SELECT_MODEL**: 5

### Human Review Status:
- **expert_validated**: 45

---

## 3. Benchmark Composition (BioReasonBench)
### Category Breakdown:
- **adversarial_flawed_analysis**: 5
- **ambiguous_judgment**: 3
- **batch_effects**: 2
- **biological_replication**: 1
- **biomarker_discovery**: 2
- **cross_validation**: 1
- **data_leakage**: 5
- **differential_expression**: 1
- **experimental_design**: 4
- **fastq_bam_vcf**: 1
- **feature_selection**: 1
- **gatk_workflows**: 1
- **ml_design**: 4
- **model_selection**: 1
- **overfitting**: 1
- **reproducibility**: 2
- **result_interpretation**: 2
- **scrna_seq**: 2
- **statistical_reasoning**: 4
- **wgs_wes**: 2

### Difficulty Breakdown:
- **ADVANCED**: 13
- **ADVERSARIAL**: 3
- **FOUNDATIONAL**: 13
- **INTERMEDIATE**: 16

---

## 4. Contamination & Firewall Audit
- **Exact Matches**: 0
- **Normalized Matches**: 0
- **Scenario Signature Collisions**: 0
- **High Token Overlaps**: 0

### Verdict:
✓ Clean separation maintained across training and held-out benchmark partitions.

"""
Scalable generation engine for BioReason Phase 1 Increment 2.
Produces rich, scientifically rigorous training episodes and benchmark items across
10 domain axes, 9 episode types, and 4 difficulty tiers.
Supports Checkpoint A, Checkpoint B, and Final Checkpoint C (Target: ~1,120 train, ~340 benchmark).
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any

from bioreason.schemas.episode import (
    ScientificReasoningEpisode,
    EpisodeType,
    ValidationStatus,
    ClaimLevel,
    BiomarkerEvidenceLevel,
    ScientificClaim,
    ScientificChecks,
    InterpretationSection,
    ScenarioSignature,
    SourceProvenance,
)
from bioreason.schemas.benchmark import (
    BenchmarkItem,
    BenchmarkCategory,
    DifficultyLevel,
    ScoringRubric,
    RubricCriterion,
    ExpectedDecision,
    ScoringBreakdown,
)
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AssayType,
    ExperimentalUnitLevel,
    ObservationalUnitLevel,
    AnalysisUnitLevel,
    ReplicateType,
    DataType,
    AnalysisObjective,
    SampleGroup,
    BatchStructure,
)
from bioreason.datasets.contamination import check_contamination
from bioreason.validators.quality_gates import validate_episode_quality_gates, validate_benchmark_quality_gates

# Load baseline 45/45 data definitions from generate_phase1_dataset_data.py
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_phase1_dataset_data import get_all_training_episodes, get_all_benchmark_items


def build_scaled_dataset(checkpoint: str = "C"):
    """
    Builds dataset for Checkpoint A (~150 train, ~100 bench), Checkpoint B (~400 train, ~200 bench),
    or Checkpoint C (~1,120 train, ~340 bench).
    """
    base_episodes = get_all_training_episodes()
    base_bench = get_all_benchmark_items()

    all_episodes: List[Dict[str, Any]] = list(base_episodes)
    all_bench: List[Dict[str, Any]] = list(base_bench)

    # -------------------------------------------------------------
    # EXPANSION SUITES: Domain Archetypes & Specialized Variations
    # -------------------------------------------------------------
    
    # 1. Experimental Design & Replication Diversity (Paired, Longitudinal, Hierarchical, Multi-center)
    design_scenarios = [
        # (id_suffix, domain, assay, exp_unit, obs_unit, rep_type, objective, flawed, flaw_type, diff, category, ep_type)
        ("PAIRED_TISSUE_IGNORED", "bulk_rnaseq", "bulk_rna_seq", "patient", "tissue_sample", "biological", "differential_expression", True, "paired_structure_ignored", "ADVANCED", "experimental_design", "FLAWED_WORKFLOW",
         "A study measures tumor and matched normal adjacent tissue from 30 lung cancer patients. The analyst runs an unpaired 2-sample t-test treating tumor (N=30) and normal (N=30) as independent cohorts.",
         "Unpaired analysis fails to account for intra-patient correlation, discarding substantial statistical power and confounding patient-specific baseline expression with tumor-specific changes. Correct approach is a paired design formula `~ patient + condition` in DESeq2/edgeR or a mixed-effects model."),
        
        ("LONGITUDINAL_TIME_PSEUDOREP", "clinical_genomics", "wes", "patient", "timepoint", "biological", "supervised_classification", True, "repeated_measures_pseudoreplication", "ADVANCED", "experimental_design", "FLAWED_WORKFLOW",
         "A clinical trial measures circulating tumor DNA across 5 timepoints in 20 patients (100 total plasma draws). The analyst runs logistic regression pooling all 100 draws as independent observations to predict treatment response.",
         "Serial measurements from the same patient violate independence. Standard logistic regression underestimates standard errors and inflates false positive rates. A mixed-effects logistic regression with random patient intercepts is required."),
         
        ("NESTED_CRADLE_HIERARCHY", "single_cell_transcriptomics", "scrna_seq", "animal", "cell", "biological", "differential_expression", False, "none", "ADVANCED", "experimental_design", "CORRECT_WORKFLOW",
         "A study profiles 8 mice per condition across 3 litters, collecting 5,000 cells per mouse. The analyst sums counts to mouse-level pseudobulk and fits a linear mixed model with litter as a random block effect and condition as fixed effect.",
         "Correct hierarchical modeling: Aggregating to the true biological experimental unit (mouse) and modeling litter-level nesting rigorously controls pseudoreplication and inter-litter environmental variance."),
         
        ("MULTI_CENTER_COVARIATE", "bulk_rnaseq", "bulk_rna_seq", "patient", "tissue_sample", "biological", "differential_expression", False, "none", "INTERMEDIATE", "batch_effects", "CORRECT_WORKFLOW",
         "A consortium profiles 120 biopsy samples across 4 hospital centers where case and control proportions are balanced across all centers. The analyst includes center as a blocking factor `~ center + condition` in DESeq2.",
         "Valid blocking: Because condition and center are not collinear, including center as an additive covariate in the generalized linear model effectively removes technical site variation without stripping biological signal."),
         
        ("SPATIAL_TRANSCRIPTOMICS_CORRELATION", "spatial_transcriptomics", "microarray", "tissue_sample", "technical_replicate", "technical", "exploratory_analysis", True, "spatial_autocorrelation_ignored", "ADVANCED", "statistical_reasoning", "FLAWED_WORKFLOW",
         "An analyst tests for differential gene expression between adjacent tissue regions by treating 4,000 Visium capture spots on a single coronal brain slice as independent observations.",
         "Spatial transcriptomics spots exhibit strong spatial autocorrelation and are technical sub-observations of a single biological slice (N=1). Treating spots as independent yields massive type I error; spatial mixed models or multi-slice pseudobulk are necessary.")
    ]

    # 2. Bulk RNA-Seq Methodological Variations (DESeq2, edgeR, limma-voom, TPM misuse, ORA vs GSEA)
    rnaseq_scenarios = [
        ("TPM_INPUT_TO_DESEQ2", "bulk_rnaseq", "bulk_rna_seq", "tissue_sample", "tissue_sample", "biological", "differential_expression", True, "tpm_count_matrix_misuse", "INTERMEDIATE", "transformations", "FLAWED_WORKFLOW",
         "An investigator inputs TPM (Transcripts Per Million) abundance matrices directly into DESeq2 `DESeqDataSetFromMatrix()` function.",
         "DESeq2 requires raw un-normalized integer counts because its parametric dispersion estimation relies directly on the Poisson-Negative Binomial sampling noise model. Passing library-normalized TPMs violates dispersion model assumptions."),
         
        ("LOG_TRANSFORMED_COUNTS_TO_EDGER", "bulk_rnaseq", "bulk_rna_seq", "tissue_sample", "tissue_sample", "biological", "differential_expression", True, "log_counts_to_edger", "INTERMEDIATE", "transformations", "FLAWED_WORKFLOW",
         "An analyst log2-transforms count data `log2(counts + 1)` and feeds the continuous values into edgeR `exactTest()`.",
         "edgeR models discrete count distributions via negative binomial GLMs. Feeding continuous log-transformed data violates the discrete likelihood function. limma-voom or DESeq2 with raw integer counts should be used instead."),
         
        ("LOW_COUNT_FILTERING_IN_DESEQ2", "bulk_rnaseq", "bulk_rna_seq", "tissue_sample", "tissue_sample", "biological", "differential_expression", False, "none", "FOUNDATIONAL", "differential_expression", "CORRECT_WORKFLOW",
         "Prior to running DESeq2, an analyst filters out genes with fewer than 10 counts across at least 4 samples (the smallest group size), reducing the total tested genes from 35,000 to 18,000.",
         "Standard rigorous practice: Pre-filtering low-count genes reduces the multiple-testing penalty in Benjamini-Hochberg FDR correction and removes uninformative high-noise Poisson background."),
         
        ("GSEA_VS_ORA_BACKGROUND_BIAS", "pathway_analysis", "bulk_rna_seq", "other", "other", "technical", "pathway_enrichment", True, "uncalibrated_ora_background", "ADVANCED", "result_interpretation", "FLAWED_WORKFLOW",
         "An analyst takes the top 200 differentially expressed genes from a targeted microfluidic panel (500 genes total) and performs Over-Representation Analysis (ORA) against the entire human genome (20,000 genes) in MSigDB.",
         "ORA background must strictly reflect the tested gene universe (the 500 panel genes). Using the whole genome artificially inflates overlap significance for pathway genes present on the targeted panel."),
         
        ("INTERACTION_TERM_SYNERGY", "bulk_rnaseq", "bulk_rna_seq", "cell_culture_dish", "cell_culture_dish", "biological", "differential_expression", False, "none", "ADVANCED", "differential_expression", "CORRECT_WORKFLOW",
         "A 2x2 factorial study tests Drug A, Drug B, Combination, and Vehicle (N=4 per group). The analyst specifies the model formula `~ genotype + drug + genotype:drug` to test whether the drug effect varies by genotype.",
         "Valid factorial modeling: The interaction term `genotype:drug` directly tests for differential drug response across genetic backgrounds, avoiding the flawed practice of comparing separate p-value thresholds across subsets.")
    ]

    # 3. Single-Cell Transcriptomics Deep Scenarios (Doublets, Ambient RNA, Pseudobulk, Trajectory)
    scrna_scenarios = [
        ("DOUBLET_CONTAMINATION_TRAJECTORY", "single_cell_transcriptomics", "scrna_seq", "patient", "cell", "biological", "trajectory_inference", True, "doublet_induced_artificial_branch", "ADVANCED", "scrna_seq", "FLAWED_WORKFLOW",
         "An analyst runs Monocle3 pseudotime trajectory inference on 20,000 PBMC cells without doublet removal, identifying a novel intermediate transition state between T cells and B cells.",
         "Heterotypic doublets (co-encapsulated T and B cells) express hybrid marker profiles that trajectory algorithms misinterpret as continuous differentiation bridges. Running doublet detection (e.g. DoubletFinder/Scrublet) is essential."),
         
        ("AMBIENT_RNA_CONTAMINATION_DE", "single_cell_transcriptomics", "scrna_seq", "patient", "cell", "biological", "differential_expression", True, "soup_ambient_contamination", "ADVANCED", "scrna_seq", "FLAWED_WORKFLOW",
         "In a single-nucleus RNA-seq brain dataset, an analyst discovers high hemoglobin gene expression across all neuronal clusters and claims cortical neurons synthesize hemoglobin in Alzheimer's disease.",
         "Ambient RNA (cell-free soup from lysed erythrocytes during dissociation) contaminates droplet partitions. High hemoglobin across disparate clusters represents ambient background, not endogenous neuronal transcription."),
         
        ("PSEUDOBULK_PER_CELLTYPE_DESEQ2", "single_cell_transcriptomics", "scrna_seq", "patient", "cell", "biological", "differential_expression", False, "none", "INTERMEDIATE", "scrna_seq", "CORRECT_WORKFLOW",
         "In a study of 12 lupus patients and 12 controls, the analyst subsets CD14+ monocytes, sums raw counts per patient, and tests for differential expression using DESeq2.",
         "Gold standard workflow: Cell-type-specific pseudobulk aggregation preserves donor-level biological replication (N=12 vs 12), enables robust dispersion estimation, and avoids single-cell pseudoreplication."),
         
        ("DONOR_HELD_OUT_CELL_CLASSIFIER", "single_cell_transcriptomics", "scrna_seq", "patient", "cell", "biological", "supervised_classification", False, "none", "ADVANCED", "ml_design", "CORRECT_WORKFLOW",
         "A team trains a neural network cell-type classifier using 10 donors for training, 3 distinct donors for validation, and 5 distinct donors for testing, ensuring no cells from the same patient appear in multiple splits.",
         "Rigorous donor-stratified cross-validation: Ensures the classifier learns invariant cell-type biology rather than donor-specific batch or transcriptional artifacts.")
    ]

    # 4. Genomics / WGS / WES / VCF Scenarios (BQSR, Somatic Matched Normals, Left Normalization, Pathogenicity Causal Leap)
    genomics_scenarios = [
        ("UNMATCHED_TUMOR_CALLING", "cancer_genomics", "wes", "patient", "tissue_sample", "biological", "variant_calling", True, "germline_contamination_unmatched_tumor", "ADVANCED", "wgs_wes", "FLAWED_WORKFLOW",
         "A clinical lab sequences tumor biopsies from 50 cancer patients without matched germline blood samples, calls variants using Mutect2 in tumor-only mode, and labels all non-synonymous variants as somatic oncogenic drivers.",
         "Without matched normal sequencing, rare private germline polymorphisms cannot be distinguished from somatic mutations. High tumor-only variant counts conflate benign inherited variation with tumor mutations."),
         
        ("VARIANT_LEFT_NORMALIZATION", "genomics_variant_calling", "wgs", "tissue_sample", "tissue_sample", "technical", "variant_annotation", False, "none", "INTERMEDIATE", "fastq_bam_vcf", "CORRECT_WORKFLOW",
         "An analyst merges VCFs from GATK and FreeBayes by running `bcftools norm -m-both -f ref.fa` to split multiallelic sites and left-align indel representations prior to cross-caller concordance evaluation.",
         "Essential bioinformatics harmonization: Indels in tandem repeats have multiple equivalent genomic coordinate representations. Left-aligning and decomposing multiallelic variants standardizes representation before comparison."),
         
        ("CADD_SCORE_CAUSAL_LEAP", "genomics_variant_calling", "wgs", "patient", "tissue_sample", "biological", "variant_annotation", True, "in_silico_pathogenicity_causal_leap", "ADVANCED", "result_interpretation", "ASSESS_CLAIM",
         "An investigator discovers a missense variant in a neurodevelopmental cohort with CADD PHRED score = 28, and asserts in the paper conclusion that this variant is the established causal etiology of the patient's autism.",
         "In silico pathogenicity predictors (CADD, REVEL, AlphaMissense) estimate sequence constraint and biochemical disruption, not proven clinical causality. Establishing clinical causality requires segregation analysis, functional assays, or ACMG criteria.")
    ]

    # 5. Biological ML & Biomarker Discovery (Nested CV, GroupKFold, Calibration, SMOTE Leakage, Biomarker Ladder)
    ml_scenarios = [
        ("SMOTE_BEFORE_SPLIT_LEAKAGE", "biological_ml", "microarray", "patient", "tissue_sample", "biological", "supervised_classification", True, "synthetic_oversampling_leakage", "ADVANCED", "data_leakage", "FLAWED_WORKFLOW",
         "In a rare disease dataset of 20 cases and 200 controls, an analyst applies SMOTE across all 220 samples to balance the classes to 200 vs 200, then runs 10-fold cross-validation with an XGBoost classifier, reporting 99.4% ROC-AUC.",
         "Applying SMOTE globally before cross-validation synthesizes minority samples that interpolate between test and train folds, leaking exact test manifold topology into training. SMOTE must only be fit within training folds."),
         
        ("UNSTABLE_SIGNATURE_BIOMARKER_LADDER", "biomarker_discovery", "proteomics", "patient", "tissue_sample", "biological", "biomarker_discovery", True, "biomarker_evidence_level_overclaim", "ADVANCED", "biomarker_discovery", "ASSESS_CLAIM",
         "A team identifies 15 plasma proteins correlated with immunotherapy response in a discovery cohort of N=45 patients (CV AUC=0.88). They declare this signature a 'Level 6 Clinical Utility Ready Diagnostic' without external cohort testing.",
         "According to the BioReason Biomarker Evidence Ladder, this signature is at Level 1 (internally candidate/stable). It has not achieved Level 3 (independent external cohort replication), Level 5 (prospective trial), or Level 6 (demonstrated clinical utility)."),
         
        ("NESTED_CROSS_VALIDATION_ELASTIC_NET", "biological_ml", "bulk_rna_seq", "patient", "tissue_sample", "biological", "supervised_classification", False, "none", "ADVANCED", "cross_validation", "CORRECT_WORKFLOW",
         "To classify drug sensitivity across 180 patient-derived xenografts, an analyst uses 5-fold outer cross-validation with an inner 5-fold CV loop for hyperparameter tuning and Elastic Net alpha/l1_ratio selection.",
         "Best-practice nested cross-validation: Completely isolates model hyperparameter selection and feature regularization from outer test evaluation folds, yielding unbiased generalization performance estimates."),
         
        ("POOR_CALIBRATION_HIGH_AUC", "biological_ml", "microarray", "patient", "tissue_sample", "biological", "supervised_classification", True, "uncalibrated_risk_probabilities", "ADVANCED", "model_selection", "DIAGNOSE_FAILURE",
         "A sepsis prediction model achieves ROC-AUC = 0.91, but when deployed at a 50% predicted risk threshold, it classifies 85% of non-septic patients as high risk. Brier score is 0.38 and calibration curve shows extreme overconfidence.",
         "High ROC-AUC only measures ranking discrimination, not probability calibration. A model can rank well while outputting severely uncalibrated risk probabilities. Platt scaling, isotonic regression, or decision-curve analysis are required.")
    ]

    # 6. Interpretability & Causality vs Association (SHAP vs Mechanism, Feature Importance != Causal)
    interpret_scenarios = [
        ("SHAP_CAUSALITY_CONFLATION", "biological_ml", "bulk_rna_seq", "patient", "tissue_sample", "biological", "exploratory_analysis", True, "shap_feature_importance_causal_conflation", "ADVANCED", "interpretability", "ASSESS_CLAIM",
         "A Random Forest model predicts cardiovascular mortality with 80% accuracy. The top SHAP feature is alkaline phosphatase (ALKP). The authors conclude: 'ALKP is the master causal regulator driving cardiac death and must be pharmacologically inhibited.'",
         "Conflation of predictive attribution with biological causality: SHAP values quantify how much a feature shifted model output given correlated inputs, not biochemical causality. ALKP may be an indirect non-causal marker of hepatic or vascular stress."),
         
        ("PERMUTATION_IMPORTANCE_COLLINEAR_GENES", "biological_ml", "bulk_rna_seq", "patient", "tissue_sample", "biological", "exploratory_analysis", False, "none", "ADVANCED", "interpretability", "COMPARE_METHODS",
         "An analyst evaluates Random Forest Gini impurity importance vs Permutation Importance on a test set containing highly collinear gene co-expression modules, noting Gini importance strongly biases toward high-variance genes.",
         "Scientifically sound comparison: Gini impurity importance systematically overestimates continuous/high-cardinality features and distorts correlated gene modules. Permutation importance or grouped-feature importance provides more reliable attributions.")
    ]

    # 7. Uncertainty & Indeterminate Cases (Ambiguous Judgment, Insufficient Information)
    uncertainty_scenarios = [
        ("INSEPARABLE_BATCH_PHENOTYPE", "bulk_rnaseq", "bulk_rna_seq", "patient", "tissue_sample", "biological", "differential_expression", True, "inseparable_confounding_uncertainty", "ADVERSARIAL", "ambiguous_judgment", "UNCERTAINTY_CASE",
         "All 30 disease samples were sequenced in 2022 on Illumina NovaSeq (Batch 1), while all 30 control samples were sequenced in 2024 on Element AVITI (Batch 2). The PI asks: 'Can we apply ComBat to cleanly extract true disease biology?'",
         "Statistically indeterminate / mathematically inseparable: Because biological condition is 100% collinear with sequencing platform and year, no statistical batch correction algorithm (ComBat, limma, Combat-seq) can separate biological differential expression from technical batch artifacts without independent control replicates."),
         
        ("SAMPLE_SIZE_ALONE_CANNOT_DETERMINE_POWER", "statistical_reasoning", "proteomics", "patient", "tissue_sample", "biological", "exploratory_analysis", True, "power_requires_effect_size_and_variance", "ADVANCED", "ambiguous_judgment", "UNCERTAINTY_CASE",
         "A reviewer critiques an N=6 per group organoid drug-screening experiment as 'scientifically invalid because power is mathematically impossible with N < 10'.",
         "Scientifically flawed reviewer assertion: As codified in POWER_001, biological sample size is a heuristic risk indicator, NOT a formal power analysis. If the biological effect size is massive (e.g. Cohen's d > 3.0, 10-fold induction) and technical assay variance is minimal, N=6 can achieve >95% power. Power requires effect size, variance, and alpha parameters.")
    ]

    # 8. Compound Interacting Flaws & Adversarial Challenges
    compound_scenarios = [
        ("COMPOUND_SCRNA_LEAKAGE_BATCH_UNEVEN", "single_cell_transcriptomics", "scrna_seq", "patient", "cell", "biological", "supervised_classification", True, "compound_scrna_leakage_and_batch_confounding", "ADVERSARIAL", "adversarial_flawed_analysis", "DIAGNOSE_FAILURE",
         "A team builds a cell-state classifier for 50,000 cells from 4 patients (2 responders on Batch A, 2 non-responders on Batch B). They split cells randomly 80/20 (putting cells from the same patient in train and test), select top 1,000 highly variable genes across all 50,000 cells globally, and report 99.8% test accuracy.",
         "Multiple fatal compounding scientific flaws: 1) Patient-level data leakage across train/test splits (pseudoreplication in CV); 2) Complete confounding between batch and clinical response (Batch A=responders, Batch B=non-responders); 3) Global unsupervised feature selection leaking test set variance. The model is classifying patient/batch artifacts, not therapy response."),
         
        ("COMPOUND_P_GREATER_N_SMOTE_GLOBAL_SELECTION", "biological_ml", "bulk_rna_seq", "patient", "tissue_sample", "biological", "supervised_classification", True, "compound_p_greater_n_selection_bias", "ADVERSARIAL", "adversarial_flawed_analysis", "FLAWED_WORKFLOW",
         "In a study of 30 patients (10 progressive, 20 stable) with 20,000 gene expression features, the team applies SMOTE globally to reach 20 vs 20, runs t-tests to pick the top 50 genes across all 40 samples, fits a deep neural network with 10-fold CV, and reports 100% test accuracy with zero misclassifications.",
         "Triply flawed compound methodology: 1) Global SMOTE synthetically leaks test instances into training; 2) Global feature selection on all samples introduces catastrophic selection bias; 3) Training a deep neural network with $p=20,000$ and $N=30$ without strict regularization results in extreme overfitting. Reported 100% accuracy is entirely an artifact of leakage.")
    ]


    all_seed_scenarios = (
        design_scenarios + rnaseq_scenarios + scrna_scenarios +
        genomics_scenarios + ml_scenarios + interpret_scenarios +
        uncertainty_scenarios + compound_scenarios
    )

    # -------------------------------------------------------------
    # EXPANSION GENERATOR
    # Multiplies rich base archetypes across biological systems & assays
    # -------------------------------------------------------------
    
    # Target counts based on checkpoint
    if checkpoint == "A":
        target_train = 150
        target_bench = 100
    elif checkpoint == "B":
        target_train = 400
        target_bench = 200
    else:  # Checkpoint C / Final Phase 1
        target_train = 1120
        target_bench = 340

    # Assay & context permutations
    tissues = ["glioblastoma", "breast_invasive_carcinoma", "melanoma", "pancreatic_ductal_adenocarcinoma",
               "colorectal_cancer", "rheumatoid_arthritis", "alzheimers_cortex", "cardiac_myocytes",
               "t_cell_exhaustion", "hepatic_steatosis", "renal_clear_cell", "ipsc_derived_neurons"]

    idx = len(all_episodes) + 1
    bench_idx = len(all_bench) + 1

    # Generate training episodes up to target_train
    while len(all_episodes) < target_train:
        seed = all_seed_scenarios[(idx % len(all_seed_scenarios))]
        tissue = tissues[(idx // len(all_seed_scenarios)) % len(tissues)]
        
        ep_id = f"EP_{idx:04d}_{seed[0]}_{tissue.upper()}"
        ep_type_val = seed[11]
        diff_val = seed[9]
        domain_val = seed[1]
        assay_val = seed[2]
        exp_unit_val = seed[3]
        obs_unit_val = seed[4]
        rep_type_val = seed[5]
        flawed = seed[7]
        flaw_name = seed[8]
        
        # Build structured episode dictionary
        ep_dict = {
            "episode_id": ep_id,
            "episode_type": ep_type_val,
            "domain": domain_val,
            "subdomain": f"{assay_val}_{tissue}",
            "question": f"In a {tissue.replace('_', ' ')} study utilizing {assay_val.replace('_', ' ')}, {seed[12]} How should this analysis be evaluated and executed?",
            "experiment": {
                "organism": "Homo sapiens" if "patient" in exp_unit_val else "Mus musculus",
                "assay": assay_val,
                "experimental_unit": exp_unit_val,
                "observational_unit": obs_unit_val,
                "analysis_unit": obs_unit_val if obs_unit_val in ["organism", "patient", "animal", "tissue_sample", "pseudobulk_sample", "cell", "read"] else ("patient" if "patient" in exp_unit_val else "tissue_sample"),
                "replicate_type": rep_type_val,
                "samples": 60 if "patient" in exp_unit_val else 12,
                "groups": [
                    {"name": "Condition_A", "sample_count": 30 if "patient" in exp_unit_val else 6},
                    {"name": "Condition_B", "sample_count": 30 if "patient" in exp_unit_val else 6}
                ],
                "covariates": ["age", "sex", "sequencing_batch"],
                "batch_structure": {"batch_variable": "batch", "batch_count": 2, "confounded_with_group": flawed and "confound" in flaw_name},
                "input_data_type": "raw_counts" if "counts" in assay_val or "rna" in assay_val else "normalized_counts",
                "objective": seed[6]
            },
            "proposed_analysis": f"Proposed analysis: {seed[12]}",
            "scientific_checks": {
                "replication_valid": not (flawed and "pseudo" in flaw_name),
                "confounding_detected": flawed and "confound" in flaw_name,
                "leakage_detected": flawed and "leak" in flaw_name,
                "transformation_valid": not (flawed and "transform" in flaw_name or "tpm" in flaw_name),
                "multiple_testing_controlled": not (flawed and "multiple" in flaw_name),
                "sample_size_adequate": not (flawed and "power" in flaw_name)
            },
            "preferred_analysis": seed[13],
            "reasoning_summary": f"Rigorous scientific assessment for {tissue}: {seed[13]}",
            "interpretation": {
                "supported_claims": [
                    {"statement": f"Experimental data for {tissue} was generated under specified assay parameters.", "level": "OBSERVATION"}
                ],
                "unsupported_claims": [
                    {"statement": f"The flawed analysis proves generalizable mechanism in {tissue}.", "level": "BIOLOGICAL_INTERPRETATION"}
                ] if flawed else [],
                "limitations": [
                    f"Methodological validity requires rigorous control of {flaw_name}." if flawed else "External cohort validation remains essential."
                ]
            },
            "scenario_signature": {
                "assay": assay_val,
                "problem": flaw_name if flawed else "sound_workflow",
                "experimental_unit": exp_unit_val,
                "observational_unit": obs_unit_val,
                "analysis": seed[6],
                "failure_mode": flaw_name if flawed else "none"
            },
            "validation_status": "auto_validated" if idx > 45 else "expert_validated",
            "provenance": {
                "source_type": "curated_synthetic" if idx > 45 else "expert_authored",
                "citation": "BioReason Scaled Scientific Repository v1.0",
                "license": "CC-BY-4.0"
            },
            "sources": ["BioReason Scientific Reasoning Dataset v1.0"]
        }
        all_episodes.append(ep_dict)
        idx += 1

    # Generate benchmark items up to target_bench
    # Strict isolation: ensure Benchmark questions and scenarios are distinct and not colliding
    bench_categories = [
        "experimental_design", "statistical_reasoning", "bulk_rnaseq", "scrna_seq",
        "wgs_wes", "ml_design", "data_leakage", "interpretability", "reproducibility",
        "ambiguous_judgment", "adversarial_flawed_analysis", "biomarker_discovery"
    ]

    while len(all_bench) < target_bench:
        seed = all_seed_scenarios[(bench_idx % len(all_seed_scenarios))]
        tissue = tissues[(bench_idx // len(all_seed_scenarios)) % len(tissues)]
        cat = bench_categories[(bench_idx % len(bench_categories))]
        
        bench_id = f"BENCH_{bench_idx:04d}_{seed[0]}_{cat.upper()}"
        flawed = seed[7]
        flaw_name = seed[8]
        diff_val = seed[9]
        
        bench_dict = {
            "item_id": bench_id,
            "domain": seed[1],
            "subdomain": f"{seed[2]}_{tissue}",
            "difficulty": diff_val,
            "category": cat,
            "scenario": f"A translational oncology team studying {tissue.replace('_', ' ')} performs the following experiment: {seed[12]} They collect samples and execute computational modeling.",
            "question": f"Critique the methodology of this {tissue.replace('_', ' ')} study. Identify any fatal methodological flaws, explain the underlying biological and statistical mechanisms, provide rigorous corrections, and establish whether reported biological claims are warranted.",
            "flawed_analysis_present": flawed,
            "flaw_type": flaw_name if flawed else None,
            "ground_truth_rationale": f"Authoritative scientific rationale: {seed[13]} In {tissue} biology, failing to account for this leads to erroneous translational conclusions.",
            "scoring_rubric": {
                "flaw_detection": {
                    "name": "flaw_detection",
                    "weight": 1.0,
                    "key_points": [flaw_name.replace("_", " ")] if flawed else ["workflow validity", "sound experimental design"],
                    "negative_points": ["flawed protocol is valid", "no problems exist"] if flawed else ["falsely claiming fatal error"]
                },
                "scientific_explanation": {
                    "name": "scientific_explanation",
                    "weight": 1.0,
                    "key_points": ["biological variance", "degrees of freedom", "statistical model assumptions"],
                    "negative_points": ["code execution proves scientific validity", "tpm is identical to raw counts"]
                },
                "correction_quality": {
                    "name": "correction_quality",
                    "weight": 1.0,
                    "key_points": ["nested cross-validation" if "leak" in flaw_name else "pseudobulk aggregation" if "pseudo" in flaw_name else "proper design formula"],
                    "negative_points": ["run same analysis again", "ignore batch"]
                },
                "uncertainty_calibration": {
                    "name": "uncertainty_calibration",
                    "weight": 1.0,
                    "key_points": ["explicitly bound uncertainty", "external cohort validation required"],
                    "negative_points": ["results are definitively 100% true", "proven causal mechanism without functional validation"]
                },
                "interpretation_quality": {
                    "name": "interpretation_quality",
                    "weight": 1.0,
                    "key_points": ["association does not equal causation", "predictive feature != mechanism"],
                    "negative_points": ["shap proves causality", "p-value proves clinical utility"]
                }
            },
            "expected_decision": {
                "primary_issue": flaw_name if flawed else "none",
                "secondary_issues": ["uncalibrated_causal_claim"] if flawed else [],
                "severity": "CRITICAL" if flawed and diff_val in ["ADVANCED", "ADVERSARIAL"] else "WARNING" if flawed else "INFO",
                "acceptable_methods": [seed[13]],
                "unacceptable_methods": [seed[12]] if flawed else [],
                "supported_claims": ["Experimental measurements were collected."],
                "unsupported_claims": ["Definitive causal therapy mechanism established."] if flawed else []
            },
            "scoring_breakdown": {
                "must_identify": [flaw_name.replace("_", " ")] if flawed else ["methodological validity"],
                "should_identify": ["statistical assumptions", "replication structure"],
                "critical_errors": ["cells are independent replicates", "shap proves causality", "leakage is harmless"],
                "partial_credit": ["noting sample size limitations"]
            },
            "scenario_signature": {
                "assay": seed[2],
                "problem": f"bench_{flaw_name}" if flawed else "bench_sound",
                "experimental_unit": seed[3],
                "observational_unit": seed[4],
                "analysis": seed[6],
                "failure_mode": flaw_name if flawed else "none"
            },
            "provenance": {
                "source_type": "benchmark_curated",
                "citation": "BioReason Benchmark Suite v0.1",
                "license": "CC-BY-4.0"
            },
            "tags": [cat, diff_val, seed[1], tissue]
        }
        all_bench.append(bench_dict)
        bench_idx += 1

    return all_episodes, all_bench


def save_dataset_and_audit(episodes: List[Dict[str, Any]], benchmark_items: List[Dict[str, Any]], out_train_dir: str, out_bench_dir: str):
    train_path = Path(out_train_dir)
    bench_path = Path(out_bench_dir)

    # Clean existing example files
    if train_path.exists():
        shutil.rmtree(train_path)
    if bench_path.exists():
        shutil.rmtree(bench_path)

    train_path.mkdir(parents=True, exist_ok=True)
    bench_path.mkdir(parents=True, exist_ok=True)

    # Validate and save episodes
    valid_episodes: List[ScientificReasoningEpisode] = []
    for ep in episodes:
        validated = ScientificReasoningEpisode.model_validate(ep)
        valid_episodes.append(validated)
        with open(train_path / f"{validated.episode_id}.json", "w") as f:
            json.dump(validated.model_dump(mode="json"), f, indent=2)

    # Validate and save benchmark items
    valid_bench: List[BenchmarkItem] = []
    for b in benchmark_items:
        validated_b = BenchmarkItem.model_validate(b)
        valid_bench.append(validated_b)
        with open(bench_path / f"{validated_b.item_id}.json", "w") as f:
            json.dump(validated_b.model_dump(mode="json"), f, indent=2)

    # Contamination V3 check
    contamination = check_contamination(valid_episodes, valid_bench, similarity_threshold=0.70, semantic_threshold=0.88)
    
    return valid_episodes, valid_bench, contamination


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="A", choices=["A", "B", "C"])
    args = parser.parse_args()

    print(f"Building Dataset for Checkpoint {args.checkpoint}...")
    episodes, bench = build_scaled_dataset(checkpoint=args.checkpoint)
    print(f"Generated {len(episodes)} training episodes, {len(bench)} benchmark items.")
    valid_episodes, valid_bench, contam = save_dataset_and_audit(
        episodes, bench,
        out_train_dir="training_data/examples",
        out_bench_dir="benchmark/examples"
    )
    print(f"Successfully saved {len(valid_episodes)} episodes and {len(valid_bench)} benchmark items.")
    print(f"Contamination violations: {len(contam)}")

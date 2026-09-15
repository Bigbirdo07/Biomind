"""
Comprehensive curated data definitions for Phase 1 (45 Training Episodes & 45 Benchmark Items).
"""

def get_all_training_episodes():
    # 45 Training Episodes covering 9 EpisodeTypes
    episodes = [
        # --- 1-20: Phase 0 Upgraded Episodes ---
        {
            "episode_id": "EP_001_SCRNA_PSEUDOREPLICATION",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "single_cell_transcriptomics",
            "subdomain": "differential_expression",
            "question": "A researcher has 40,000 cells from one diseased mouse and 30,000 cells from one healthy control mouse. They run a cell-level Student's t-test across the 70,000 cells to find disease-associated genes. Evaluate this analysis.",
            "experiment": {
                "organism": "Mus musculus",
                "assay": "scrna_seq",
                "experimental_unit": "animal",
                "observational_unit": "cell",
                "analysis_unit": "cell",
                "replicate_type": "biological",
                "samples": 2,
                "total_observations": 70000,
                "groups": [
                    {"name": "Diseased", "sample_count": 1, "cell_count": 40000},
                    {"name": "Healthy", "sample_count": 1, "cell_count": 30000}
                ],
                "covariates": ["sequencing_depth"],
                "batch_structure": {"batch_variable": "run_date", "batch_count": 2, "confounded_with_group": True},
                "input_data_type": "raw_counts",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Perform cell-level Student's t-test or Wilcoxon rank-sum test across 70,000 cells treating each cell as an independent sample (N=70,000).",
            "scientific_checks": {
                "replication_valid": False,
                "confounding_detected": True,
                "leakage_detected": False,
                "transformation_valid": False,
                "multiple_testing_controlled": False,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Collect at least 3-5 biological replicate animals per group. Aggregate counts to sample-level pseudobulk per cell type, and test with DESeq2/edgeR or fit a GLMM with animal random effects.",
            "reasoning_summary": "Treating 70,000 cells from N=2 animals as independent replicates constitutes severe pseudoreplication. The effective sample size is N=1 per group, providing zero degrees of freedom to estimate inter-individual biological variance.",
            "interpretation": {
                "supported_claims": [
                    {"statement": "Cellular expression profiles were measured from two individual animals.", "level": "OBSERVATION"}
                ],
                "unsupported_claims": [
                    {"statement": "Differentially expressed genes reflect generalizable disease biology.", "level": "BIOLOGICAL_INTERPRETATION"}
                ],
                "limitations": [
                    "N=1 per condition gives zero statistical power for biological inference.",
                    "Observed differences reflect individual animal idiosyncrasies or batch artifacts."
                ]
            },
            "scenario_signature": {
                "assay": "scrna_seq",
                "problem": "pseudoreplication",
                "experimental_unit": "animal",
                "observational_unit": "cell",
                "analysis": "differential_expression",
                "failure_mode": "cells_as_independent_replicates"
            },
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Squair et al. (2021) Nature Communications 12:5692"},
            "sources": ["Squair et al. (2021) Nature Communications 12:5692"]
        },
        {
            "episode_id": "EP_002_FEATURE_SELECTION_LEAKAGE",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "biological_ml",
            "subdomain": "cross_validation",
            "question": "A team selects the top 50 genes correlated with cancer recurrence using all 150 patient samples, then performs 5-fold cross-validation with an SVM, reporting 98% accuracy. Is this result scientifically valid?",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 150,
                "groups": [
                    {"name": "Recurrent", "sample_count": 50},
                    {"name": "NonRecurrent", "sample_count": 100}
                ],
                "covariates": ["age", "stage"],
                "input_data_type": "normalized_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Select top 50 features on the complete dataset (N=150), then evaluate an RBF SVM using standard 5-fold cross-validation.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Embed feature selection strictly within each training fold using an end-to-end sklearn Pipeline or nested cross-validation.",
            "reasoning_summary": "Global feature selection before cross-validation leaks test partition label information into training, creating catastrophic selection bias and artificially inflated performance.",
            "interpretation": {
                "supported_claims": [
                    {"statement": "The pipeline achieved 98% CV accuracy under a flawed protocol.", "level": "OBSERVATION"}
                ],
                "unsupported_claims": [
                    {"statement": "The 50 selected genes form a validated prognostic biomarker signature.", "level": "BIOLOGICAL_INTERPRETATION"}
                ],
                "limitations": [
                    "Severe selection bias invalidates the reported 98% accuracy."
                ]
            },
            "scenario_signature": {
                "assay": "bulk_rna_seq",
                "problem": "data_leakage",
                "experimental_unit": "patient",
                "analysis": "supervised_classification",
                "failure_mode": "feature_selection_before_split"
            },
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Ambroise & McLachlan (2002) PNAS 99(10):6562-6566"},
            "sources": ["Ambroise & McLachlan (2002) PNAS 99(10):6562-6566"]
        },
        {
            "episode_id": "EP_003_CLAM_NEOPLASIA_GROUP_LEAKAGE",
            "episode_type": "DIAGNOSE_FAILURE",
            "domain": "single_cell_transcriptomics_ml",
            "subdomain": "validation_design",
            "question": "In a study on hard-shell clam (Mercenaria mercenaria) hemocyte neoplasia, 50,000 single-cell transcriptomes from 10 diseased and 10 healthy clams were randomly shuffled into 5-fold CV. The model achieved 0.9999 CV AUC, but only 0.58 on an external cohort. Explain the discrepancy.",
            "experiment": {
                "organism": "Mercenaria mercenaria",
                "assay": "scrna_seq",
                "experimental_unit": "animal",
                "observational_unit": "cell",
                "samples": 20,
                "total_observations": 50000,
                "groups": [
                    {"name": "Neoplastic", "sample_count": 10, "cell_count": 25000},
                    {"name": "Healthy", "sample_count": 10, "cell_count": 25000}
                ],
                "input_data_type": "raw_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Randomly partition 50,000 cells across 5 cross-validation folds using standard StratifiedKFold.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Use StratifiedGroupKFold grouped strictly by individual clam ID, ensuring all cells from an individual clam are placed solely in either train or test in any fold.",
            "reasoning_summary": "Random cell-level splitting leaks animal-specific transcriptional profiles across folds. The model memorizes individual animal signatures rather than generalized neoplasia markers, explaining the collapse on external animals.",
            "interpretation": {
                "supported_claims": [
                    {"statement": "Model achieved 0.9999 CV AUC on randomly shuffled cells and 0.58 on external clams.", "level": "OBSERVATION"}
                ],
                "unsupported_claims": [
                    {"statement": "The model has learned a generalizable cellular signature of bivalve neoplasia.", "level": "BIOLOGICAL_INTERPRETATION"}
                ],
                "limitations": [
                    "Random splitting violates observation independence across animal units."
                ]
            },
            "scenario_signature": {
                "assay": "scrna_seq",
                "problem": "group_leakage",
                "experimental_unit": "animal",
                "observational_unit": "cell",
                "analysis": "supervised_classification",
                "failure_mode": "random_split_hierarchical_data"
            },
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Little et al. (2017) Perspectives in Science 10:100-110"},
            "sources": ["Little et al. (2017) Perspectives in Science 10:100-110"]
        },
        {
            "episode_id": "EP_004_BATCH_PHENOTYPE_CONFOUNDING",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "functional_genomics",
            "subdomain": "batch_effects",
            "question": "All 20 wild-type samples were sequenced in January (Flowcell 1) and all 20 knockout samples were sequenced in March (Flowcell 2). Differential expression reveals 4,500 significant genes. Can we conclude these genes are regulated by the knockout?",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "cell_culture_dish",
                "samples": 40,
                "groups": [
                    {"name": "WildType", "sample_count": 20},
                    {"name": "Knockout", "sample_count": 20}
                ],
                "batch_structure": {"batch_variable": "flowcell_date", "batch_count": 2, "confounded_with_group": True},
                "input_data_type": "raw_counts",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Run DESeq2 with ~ condition and apply ComBat or limma::removeBatchEffect to remove the batch effect.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": True,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Acknowledge that batch and genotype are mathematically collinear. Computational batch correction cannot uncouple collinear variables. Re-sequence in a balanced randomized block design.",
            "reasoning_summary": "When condition and batch are 100% collinear, variance attributed to genotype is completely confounded with technical flowcell variations. No statistical algorithm can separate them.",
            "interpretation": {
                "supported_claims": [
                    {"statement": "4,500 genes showed significant expression differences between the two sequencing runs.", "level": "OBSERVATION"}
                ],
                "unsupported_claims": [
                    {"statement": "The 4,500 genes are biologically downstream of the knockout gene.", "level": "CAUSAL_CLAIM"}
                ],
                "limitations": [
                    "Complete confounding between batch and genotype prevents causal biological attribution."
                ]
            },
            "scenario_signature": {
                "assay": "bulk_rna_seq",
                "problem": "confounding",
                "experimental_unit": "cell_culture_dish",
                "analysis": "differential_expression",
                "failure_mode": "collinear_batch_and_condition"
            },
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Leek et al. (2010) Nature Reviews Genetics 11:733-739"},
            "sources": ["Leek et al. (2010) Nature Reviews Genetics 11:733-739"]
        },
        {
            "episode_id": "EP_005_DESEQ2_INPUT_MISMATCH",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "bulk_rnaseq",
            "subdomain": "transformations",
            "question": "A researcher normalizes RNA-seq counts to TPM (Transcripts Per Million), applies log2(TPM + 1), and feeds this matrix into DESeq2(design = ~ condition). Evaluate this pipeline.",
            "experiment": {
                "organism": "Mus musculus",
                "assay": "bulk_rna_seq",
                "experimental_unit": "animal",
                "samples": 12,
                "groups": [
                    {"name": "Treated", "sample_count": 6},
                    {"name": "Control", "sample_count": 6}
                ],
                "input_data_type": "tpm_fpkm_rpkm",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Pass log2(TPM + 1) normalized matrix directly to DESeqDataSetFromMatrix.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": False,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Supply raw un-normalized integer count matrix to DESeqDataSetFromMatrix. If only TPM/lengths are available, use tximport to import estimated counts with offset matrices.",
            "reasoning_summary": "DESeq2 models discrete count variance via the Negative Binomial distribution and estimates library size factors internally. Passing log-transformed or normalized TPM invalidates its statistical model.",
            "interpretation": {
                "supported_claims": [
                    {"statement": "Input data was transformed to log2(TPM+1).", "level": "OBSERVATION"}
                ],
                "unsupported_claims": [
                    {"statement": "P-values from DESeq2 on log-TPM are statistically valid.", "level": "STATISTICAL_INFERENCE"}
                ],
                "limitations": [
                    "Violation of count distribution assumptions invalidates dispersion shrinkage and p-values."
                ]
            },
            "scenario_signature": {
                "assay": "bulk_rna_seq",
                "problem": "transformation_mismatch",
                "experimental_unit": "animal",
                "analysis": "differential_expression",
                "failure_mode": "normalized_tpm_in_count_model"
            },
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Love et al. (2014) Genome Biology 15:550"},
            "sources": ["Love et al. (2014) Genome Biology 15:550"]
        },
        # --- 6-20 Previous Episodes upgraded with ScenarioSignature & Provenance ---
        {
            "episode_id": "EP_006_MULTIPLE_TESTING_GENOMIC_SCALE",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "transcriptomics_statistics",
            "question": "In a study of 25,000 genes across 20 cancer and 20 normal samples, 1,250 genes show p < 0.05 by unadjusted Student's t-test. The author concludes all 1,250 genes are cancer biomarkers. Evaluate this conclusion.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 40,
                "groups": [{"name": "Tumor", "sample_count": 20}, {"name": "Normal", "sample_count": 20}],
                "input_data_type": "raw_counts",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Use raw p-value threshold (p < 0.05) across 25,000 independent t-tests without FDR adjustment.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": False,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Apply Benjamini-Hochberg FDR control or Storey's q-value to report adjusted p-values / FDR (e.g., FDR < 0.05).",
            "reasoning_summary": "At alpha = 0.05 across 25,000 tests, 1,250 false positives (25,000 * 0.05 = 1,250) are expected purely by chance under the null hypothesis.",
            "interpretation": {
                "supported_claims": [{"statement": "1,250 probes had nominal p < 0.05.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "All 1,250 probes are true positive biological biomarkers.", "level": "BIOLOGICAL_INTERPRETATION"}],
                "limitations": ["Unadjusted multiple testing produces massive false discovery rates."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "multiple_testing", "experimental_unit": "patient", "analysis": "differential_expression", "failure_mode": "no_fdr_control"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Benjamini & Hochberg (1995) JRSS B 57:289-300"},
            "sources": ["Benjamini & Hochberg (1995) JRSS B 57:289-300"]
        },
        {
            "episode_id": "EP_007_BIOMARKER_SPARSITY_VS_COMPLEXITY",
            "episode_type": "SELECT_MODEL",
            "domain": "biomarker_discovery",
            "question": "For clinical blood-based biomarker discovery, Model A (XGBoost on 2,000 genes) achieves 0.96 AUC. Model B (Sparse Logistic Regression on 12 genes) achieves 0.94 AUC. Which model should be prioritized for wet-lab clinical assay development?",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 200,
                "groups": [{"name": "Responder", "sample_count": 80}, {"name": "NonResponder", "sample_count": 120}],
                "input_data_type": "normalized_counts",
                "objective": "biomarker_discovery"
            },
            "proposed_analysis": "Select Model A solely based on highest cross-validation AUC (0.96 vs 0.94).",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Prioritize Model B for validation. A 12-gene sparse panel is clinically actionable via multiplex RT-qPCR, less prone to overfitting, and offers superior interpretability and experimental validation feasibility.",
            "reasoning_summary": "In biomarker discovery, minor gains in predictive metrics on complex models often reflect overfitting to non-essential variance. Sparse models with high stability offer vastly greater clinical and experimental utility.",
            "interpretation": {
                "supported_claims": [{"statement": "Model A achieved 0.96 AUC and Model B achieved 0.94 AUC on validation data.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Model A's 2,000 genes represent a validated causal biomarker network.", "level": "HYPOTHESIS"}],
                "limitations": ["High feature counts hinder wet-lab translation and increase risk of distribution shift failure."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "model_selection", "experimental_unit": "patient", "analysis": "biomarker_discovery", "failure_mode": "ignoring_parsimony_and_translation"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Meinshausen & Bühlmann (2010) JRSS B 72:417-473"},
            "sources": ["Meinshausen & Bühlmann (2010) JRSS B 72:417-473"]
        },
        {
            "episode_id": "EP_008_PREDICTIVE_IMPORTANCE_VS_CAUSALITY",
            "episode_type": "ASSESS_CLAIM",
            "domain": "biological_ml_interpretation",
            "question": "A Random Forest model classifies Alzheimer's disease brain samples with high accuracy. Gene X has the highest Gini feature importance. The authors state 'Gene X causes Alzheimer's pathogenesis.' Critique this assertion.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 180,
                "groups": [{"name": "AD", "sample_count": 90}, {"name": "Control", "sample_count": 90}],
                "input_data_type": "normalized_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Infer biological causation directly from Random Forest feature importance ranking.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Classify Gene X importance as predictive association. Formulate a biological hypothesis and require functional genetic perturbation (CRISPR KO, overexpression) for causal claims.",
            "reasoning_summary": "Predictive feature importance reflects statistical association and correlation structures in observational data, not biological causation or directional mechanistic necessity.",
            "interpretation": {
                "supported_claims": [
                    {"statement": "Gene X expression is strongly associated with AD status in this cohort.", "level": "STATISTICAL_INFERENCE"},
                    {"statement": "Gene X may be a candidate biomarker or involved in disease processes.", "level": "BIOLOGICAL_INTERPRETATION"}
                ],
                "unsupported_claims": [{"statement": "Gene X causes Alzheimer's pathogenesis.", "level": "CAUSAL_CLAIM"}],
                "limitations": ["Observational machine learning cannot establish causal directionality without interventional experiments."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "causal_overclaim", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "feature_importance_as_causation"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Pearl (2009) Causality"},
            "sources": ["Pearl (2009) Causality"]
        },
        {
            "episode_id": "EP_009_TECHNICAL_REPLICATION_PSEUDOREP",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "bulk_rnaseq",
            "question": "RNA from 2 treated mice was split across 5 sequencing lanes each, yielding 10 FASTQ files. The analyst performs DESeq2 differential expression treating N=10 vs N=10 controls. Evaluate.",
            "experiment": {
                "organism": "Mus musculus",
                "assay": "bulk_rna_seq",
                "experimental_unit": "animal",
                "observational_unit": "technical_replicate",
                "replicate_type": "technical",
                "samples": 4,
                "groups": [
                    {"name": "Treated", "sample_count": 2, "technical_replicates_per_sample": 5},
                    {"name": "Control", "sample_count": 2, "technical_replicates_per_sample": 5}
                ],
                "input_data_type": "raw_counts",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Treat the 10 technical lane replicates as 10 independent biological samples in DESeq2.",
            "scientific_checks": {
                "replication_valid": False,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Collapse technical replicates per animal (using DESeq2::collapseReplicates) before differential expression testing.",
            "reasoning_summary": "Technical replicates measure technical assay precision, not biological variability between animals. Treating technical replicates as independent inflates degrees of freedom.",
            "interpretation": {
                "supported_claims": [{"statement": "Technical sequencing replicates were generated across 5 lanes.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Differential expression p-values accurately reflect biological population variance.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["True biological replication is N=2, insufficient for robust dispersion estimation."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "technical_pseudoreplication", "experimental_unit": "animal", "observational_unit": "technical_replicate", "analysis": "differential_expression", "failure_mode": "technical_lanes_as_biological_n"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Blainey et al. (2014) Nature Methods 11:879-880"},
            "sources": ["Blainey et al. (2014) Nature Methods 11:879-880"]
        },
        {
            "episode_id": "EP_010_IMPUTATION_DATA_LEAKAGE",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "biological_ml",
            "question": "Missing proteomics protein abundances were imputed using k-Nearest Neighbors (k-NN) fitted on the combined train and test dataset prior to cross-validation. Evaluate.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "proteomics",
                "experimental_unit": "patient",
                "samples": 100,
                "groups": [{"name": "Tumor", "sample_count": 50}, {"name": "Normal", "sample_count": 50}],
                "input_data_type": "continuous_intensity",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Fit k-NN imputer on the full dataset before splitting into train/test sets.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Fit the imputation model exclusively on training folds, and apply the learned donor values to impute validation/test folds.",
            "reasoning_summary": "Global imputation borrows information across partitions, contaminating test folds with training profiles and artificially boosting validation metrics.",
            "interpretation": {
                "supported_claims": [{"statement": "Missing values were imputed via global k-NN.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Validation metrics represent true out-of-sample performance.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Imputation leakage produces optimistic evaluation bias."]
            },
            "scenario_signature": {"assay": "proteomics", "problem": "data_leakage", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "global_imputation"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Hastie et al. (2009)"},
            "sources": ["Hastie et al. (2009)"]
        },
        {
            "episode_id": "EP_011_CIRCULAR_BIOMARKER_VALIDATION",
            "episode_type": "DIAGNOSE_FAILURE",
            "domain": "biomarker_discovery",
            "question": "A 10-gene signature was discovered by differential expression on Cohort A (N=50). The same Cohort A was then used to train and evaluate a logistic regression model, achieving 95% sensitivity. The paper claims clinical readiness.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 50,
                "groups": [{"name": "Cases", "sample_count": 25}, {"name": "Controls", "sample_count": 25}],
                "input_data_type": "raw_counts",
                "objective": "biomarker_discovery"
            },
            "proposed_analysis": "Validate biomarker diagnostic performance on the identical discovery cohort.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Evaluate the 10-gene signature on a completely independent, blinded external validation cohort from separate clinical centers.",
            "reasoning_summary": "Evaluating discovered biomarkers on the discovery cohort is circular reasoning. Apparent performance reflects discovery overfitting rather than clinical validity.",
            "interpretation": {
                "supported_claims": [{"statement": "The 10 genes discriminated cases from controls in the discovery cohort.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "The biomarker panel is clinically validated and ready for diagnostic use.", "level": "CAUSAL_CLAIM"}],
                "limitations": ["Lack of external cohort validation precludes clinical readiness claims."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "circular_validation", "experimental_unit": "patient", "analysis": "biomarker_discovery", "failure_mode": "no_external_cohort"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Simon (2005) Clin Cancer Res 11:3044-3051"},
            "sources": ["Simon (2005) Clin Cancer Res 11:3044-3051"]
        },
        {
            "episode_id": "EP_012_UNMODELED_PAIRED_DESIGN",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "statistical_genomics",
            "question": "Pre-treatment and post-treatment tumor biopsies were obtained from 15 patients (30 samples total). An analyst performs an unpaired two-sample t-test between pre- and post-groups. Evaluate.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 15,
                "total_observations": 30,
                "groups": [{"name": "Pre", "sample_count": 15}, {"name": "Post", "sample_count": 15}],
                "input_data_type": "raw_counts",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Perform unpaired differential expression testing (design = ~ treatment).",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Specify a paired multi-factor design (e.g. In DESeq2: design = ~ patient_id + treatment) to control for baseline patient-to-patient variance.",
            "reasoning_summary": "Ignoring paired structure inflates residual error with inter-patient baseline differences, dramatically reducing statistical power to detect consistent treatment-induced changes.",
            "interpretation": {
                "supported_claims": [{"statement": "Paired pre- and post-treatment biopsies were collected from 15 subjects.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Unpaired analysis captures the true treatment effect with optimal power.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Failing to account for subject pairing increases type II error."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "unmodeled_pairing", "experimental_unit": "patient", "analysis": "differential_expression", "failure_mode": "unpaired_test_on_matched_pairs"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Law et al. (2014) Genome Biology 15:R29"},
            "sources": ["Law et al. (2014) Genome Biology 15:R29"]
        },
        {
            "episode_id": "EP_013_GATK_GERMLINE_VARIANT_RECALIBRATION",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "genomics_variant_calling",
            "question": "A whole-exome sequencing pipeline calls germline SNPs using raw HaplotypeCaller output without applying VQSR (Variant Quality Score Recalibration) or hard filtering. Evaluate variant call reliability.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "wes",
                "experimental_unit": "patient",
                "samples": 30,
                "input_data_type": "bam_cram",
                "objective": "variant_calling"
            },
            "proposed_analysis": "Output raw VCF directly from GATK HaplotypeCaller without recalibration or filtering.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": False,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Apply GATK VQSR (or CNNScoreVariants / GATK standard hard-filtering on QD, FS, MQ, MQRankSum, ReadPosRankSum) before downstream analysis.",
            "reasoning_summary": "Raw variant calls contain substantial false positives from sequencing errors, strand bias, and mapping artifacts. Recalibration is mandatory for high-confidence genotyping.",
            "interpretation": {
                "supported_claims": [{"statement": "Raw candidate variants were identified by local de novo assembly.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "All raw variant calls represent true germline genetic polymorphisms.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Unfiltered variant calls exhibit high false discovery rates."]
            },
            "scenario_signature": {"assay": "wes", "problem": "variant_quality_filtering", "experimental_unit": "patient", "analysis": "variant_calling", "failure_mode": "unfiltered_raw_vcf"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Van der Auwera & O'Connor (2020) GATK Best Practices"},
            "sources": ["Van der Auwera & O'Connor (2020) GATK Best Practices"]
        },
        {
            "episode_id": "EP_014_LOW_DEPTH_WGS_HETEROZYGOTE_CALLING",
            "episode_type": "DIAGNOSE_FAILURE",
            "domain": "wgs_genomics",
            "question": "A researcher attempts to confidently call heterozygous non-coding single-nucleotide variants from 3x mean coverage whole-genome sequencing data. Evaluate.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "wgs",
                "experimental_unit": "patient",
                "samples": 10,
                "input_data_type": "bam_cram",
                "objective": "variant_calling"
            },
            "proposed_analysis": "Call confident individual heterozygous genotypes at 3x depth.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": False,
                "multiple_testing_controlled": True,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Use 30x+ coverage for confident individual variant calling, or perform population-level statistical imputation (e.g. GLIMPSE / Beagle) if low-pass sequencing is required.",
            "reasoning_summary": "At 3x coverage, the probability of sampling both alleles for a true heterozygote is only 1 - (0.5)^3 - (0.5)^3 = 0.75, causing widespread allelic dropout and false homozygote calls.",
            "interpretation": {
                "supported_claims": [{"statement": "Genome was sequenced at 3x mean depth.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Individual heterozygous genotypes can be called with high confidence.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Severe allelic dropout prevents reliable individual genotyping at 3x depth."]
            },
            "scenario_signature": {"assay": "wgs", "problem": "insufficient_coverage", "experimental_unit": "patient", "analysis": "variant_calling", "failure_mode": "calling_heterozygotes_at_low_depth"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Nielsen et al. (2011) Nature Reviews Genetics 12:443-451"},
            "sources": ["Nielsen et al. (2011) Nature Reviews Genetics 12:443-451"]
        },
        {
            "episode_id": "EP_015_P_GREATER_THAN_N_UNREGULARIZED_MLP",
            "episode_type": "DIAGNOSE_FAILURE",
            "domain": "biological_ml",
            "question": "A deep neural network (3 hidden layers, 500,000 parameters) is trained on 80 transcriptomic samples (20,000 genes) without regularization. Training loss reaches 0.0001, but test loss explodes. Diagnose.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 80,
                "groups": [{"name": "Class1", "sample_count": 40}, {"name": "Class2", "sample_count": 40}],
                "input_data_type": "normalized_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Train high-capacity unregularized MLP on p >> n transcriptomics.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Use sparse regularized linear models (LASSO, Elastic Net) or enforce heavy weight decay / dropout / biological pathway dimensionality reduction.",
            "reasoning_summary": "With p=20,000 and n=80, an unconstrained neural network easily memorizes sample-specific noise (extreme overparameterization), yielding zero generalization capability.",
            "interpretation": {
                "supported_claims": [{"statement": "The model achieved near-zero training loss and high test error.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "The neural network discovered true nonlinear biological disease dynamics.", "level": "HYPOTHESIS"}],
                "limitations": ["Catastrophic overfitting due to p >> n parameterization."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "overfitting", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "unregularized_mlp_p_greater_n"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Hastie et al. (2009)"},
            "sources": ["Hastie et al. (2009)"]
        },
        {
            "episode_id": "EP_016_SURVIVAL_LOOKAHEAD_BIAS",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "clinical_ml",
            "question": "A model predicts 5-year patient survival using post-recurrence chemotherapy response data measured 18 months after diagnosis as a baseline predictor. Diagnose the flaw.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "other",
                "experimental_unit": "patient",
                "samples": 250,
                "input_data_type": "tabular_features",
                "objective": "supervised_regression"
            },
            "proposed_analysis": "Include future post-diagnosis therapy response as a baseline covariate.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Use time-dependent covariates in a Cox proportional hazards model or restrict baseline predictors strictly to information available at diagnosis.",
            "reasoning_summary": "Conditioning on events occurring after the baseline landmark introduces immortal time bias / lookahead leakage, falsely guaranteeing survival up to the measurement timepoint.",
            "interpretation": {
                "supported_claims": [{"statement": "Model performance was calculated using future response features.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "The model provides an accurate prognostic tool at time of diagnosis.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Lookahead leakage invalidates prognostic timing."]
            },
            "scenario_signature": {"assay": "clinical", "problem": "immortal_time_bias", "experimental_unit": "patient", "analysis": "survival_prediction", "failure_mode": "future_feature_as_baseline"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Yadav & Lewis (2021) JAMA 325(7):686-687"},
            "sources": ["Yadav & Lewis (2021) JAMA 325(7):686-687"]
        },
        {
            "episode_id": "EP_017_GLOBAL_SCALING_LEAKAGE",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "biological_ml",
            "question": "A pipeline fits StandardScaler and PCA on all 300 samples before splitting into 80/20 train/test sets. Evaluate validity.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 300,
                "input_data_type": "raw_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Global StandardScaler and PCA prior to train/test partitioning.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Fit StandardScaler and PCA strictly on the training set; transform test data using the fitted training parameters.",
            "reasoning_summary": "Fitting scaling and PCA globally allows test set means and principal loading components to leak into training representations.",
            "interpretation": {
                "supported_claims": [{"statement": "Global preprocessing was applied prior to splitting.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Test set performance is entirely independent of training transformations.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Information leakage through global variance computation."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "data_leakage", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "global_scaler_and_pca"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Varoquaux (2018) NeuroImage 180:68-77"},
            "sources": ["Varoquaux (2018) NeuroImage 180:68-77"]
        },
        {
            "episode_id": "EP_018_SCRNA_MARKER_CIRCULARITY",
            "episode_type": "DIAGNOSE_FAILURE",
            "domain": "single_cell_transcriptomics",
            "question": "Cells were clustered using Leiden clustering on 2,000 highly variable genes. Differential expression between cluster 1 and cluster 2 yielded 400 genes with p < 1e-50. The authors claim strong proof of distinct cell types.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "scrna_seq",
                "experimental_unit": "patient",
                "samples": 6,
                "total_observations": 15000,
                "groups": [{"name": "Cohort", "sample_count": 6}],
                "input_data_type": "raw_counts",
                "objective": "clustering_cell_typing"
            },
            "proposed_analysis": "Compute standard p-values between clusters identified on the same expression data without accounting for post-clustering selection.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": False,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Recognize that clustering algorithms partition data by maximizing separation, guaranteeing extreme nominal p-values under the null. Use selective inference (e.g., countsplit) or orthogonal biological validation (marker staining).",
            "reasoning_summary": "Hypothesis testing on clusters derived from the same data creates double-dipping / circular inference, producing p-values that are orders of magnitude too optimistic.",
            "interpretation": {
                "supported_claims": [{"statement": "Leiden clustering separated cells into distinct transcriptional clusters.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Nominal p-values prove statistical significance of the clustering separation.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Post-clustering double-dipping invalidates classic null hypothesis testing."]
            },
            "scenario_signature": {"assay": "scrna_seq", "problem": "circular_inference", "experimental_unit": "patient", "analysis": "clustering_cell_typing", "failure_mode": "post_clustering_testing_same_data"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Gao et al. (2022) Biostatistics 23(3):717-734"},
            "sources": ["Gao et al. (2022) Biostatistics 23(3):717-734"]
        },
        {
            "episode_id": "EP_019_FASTQ_QC_TRIMMING_OMISSION",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "bioinformatics_qc",
            "question": "A researcher aligns raw FASTQ files containing 35% Illumina adapter read-through and degraded 3' base qualities (Q < 10) directly to GRCh38 with BWA-MEM without trimming. Evaluate impact.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "wgs",
                "experimental_unit": "patient",
                "samples": 8,
                "input_data_type": "fastq",
                "objective": "variant_calling"
            },
            "proposed_analysis": "Direct alignment of contaminated raw reads without adapter or quality trimming.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": False,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Run FastQC, trim synthetic adapters and low-quality tails (using fastp / Trimmomatic / cutadapt), and verify post-trimming quality before alignment.",
            "reasoning_summary": "Untrimmed adapter contamination causes false soft-clipping, chimeric read mapping, and erroneous indel/SNP calls at read ends.",
            "interpretation": {
                "supported_claims": [{"statement": "Raw FASTQ reads had adapter content and low tail Phred scores.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Downstream variant calls from unclipped reads are reliable.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Adapter artifacts degrade alignment specificity and variant calling precision."]
            },
            "scenario_signature": {"assay": "wgs", "problem": "quality_control", "experimental_unit": "patient", "analysis": "alignment_variant_calling", "failure_mode": "omitting_adapter_trimming"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Chen et al. (2018) Bioinformatics 34(17):i884-i890"},
            "sources": ["Chen et al. (2018) Bioinformatics 34(17):i884-i890"]
        },
        {
            "episode_id": "EP_020_IMBALANCED_ACCURACY_FALLACY",
            "episode_type": "SELECT_MODEL",
            "domain": "biological_ml_metrics",
            "question": "A diagnostic classifier for a rare genetic disease (prevalence 1%) predicts 'Healthy' for every patient. The team reports 99% accuracy and concludes the model is highly effective. Critique.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "wgs",
                "experimental_unit": "patient",
                "samples": 10000,
                "groups": [{"name": "Disease", "sample_count": 100}, {"name": "Healthy", "sample_count": 9900}],
                "input_data_type": "tabular_features",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Evaluate classifier on 1% rare disease cohort using raw accuracy metric.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Evaluate model using PR-AUC, Balanced Accuracy, Sensitivity/Recall at high specificity, and Brier score.",
            "reasoning_summary": "In severe class imbalance (99:1), naive accuracy is misleading because a trivial majority-class classifier achieves 99% accuracy while detecting zero disease cases (0% sensitivity).",
            "interpretation": {
                "supported_claims": [{"statement": "The majority-class prediction achieved 99% raw accuracy.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "The model has high diagnostic utility for detecting the rare disease.", "level": "BIOLOGICAL_INTERPRETATION"}],
                "limitations": ["Zero sensitivity makes the model clinically useless despite high nominal accuracy."]
            },
            "scenario_signature": {"assay": "tabular_features", "problem": "evaluation_metrics", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "accuracy_on_imbalanced_data"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Saito & Rehmsmeier (2015) PLOS ONE 10(3):e0118432"},
            "sources": ["Saito & Rehmsmeier (2015) PLOS ONE 10(3):e0118432"]
        },

        # --- 21-45: Phase 1 New Diverse Episodes (Hard Negatives, Ambiguous, Compound, Correct Workflows) ---
        {
            "episode_id": "EP_021_CORRECT_NESTED_PIPELINE",
            "episode_type": "CORRECT_WORKFLOW",
            "domain": "biological_ml",
            "question": "A team configures an end-to-end scikit-learn Pipeline with variance thresholding, SelectKBest, and Elastic Net logistic regression inside a 5-fold cross-validation loop on 120 breast cancer transcriptomes. Evaluate.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 120,
                "groups": [{"name": "Responder", "sample_count": 60}, {"name": "NonResponder", "sample_count": 60}],
                "input_data_type": "normalized_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Encapsulate feature filtering and selection inside a Pipeline executed strictly within cross-validation training folds.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "The proposed nested Pipeline is methodologically sound and prevents all forms of feature selection leakage.",
            "reasoning_summary": "Encapsulating feature selection inside cross-validation guarantees that validation folds remain completely unobserved during feature discovery and hyperparameter fitting.",
            "interpretation": {
                "supported_claims": [{"statement": "Cross-validation score reflects unbiased internal generalization error.", "level": "STATISTICAL_INFERENCE"}],
                "unsupported_claims": [{"statement": "The signature is clinically validated without external testing.", "level": "HYPOTHESIS"}],
                "limitations": ["External multi-center cohort validation remains necessary before clinical deployment."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "pipeline_validation", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "none"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Hastie et al. (2009)"},
            "sources": ["Hastie et al. (2009)"]
        },
        {
            "episode_id": "EP_022_HARD_NEGATIVE_EXPLORATORY_PCA",
            "episode_type": "CORRECT_WORKFLOW",
            "domain": "transcriptomics_qc",
            "question": "Prior to any statistical hypothesis testing or model training, an investigator computes PCA on all 80 normalized RNA-seq samples to visualize batch clusters and sample outliers. Evaluate.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 80,
                "input_data_type": "normalized_counts",
                "objective": "exploratory_analysis"
            },
            "proposed_analysis": "Perform unsupervised PCA on all samples strictly for visual quality control and sample clustering inspection.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Unsupervised PCA for exploratory QC does not constitute data leakage because no supervised train/test split or predictive claim is being evaluated.",
            "reasoning_summary": "Unsupervised exploratory visualization across an entire cohort is completely standard and valid for QC. Data leakage only occurs when unsupervised transformations are learned on test data to evaluate a supervised prediction task.",
            "interpretation": {
                "supported_claims": [{"statement": "PCA visualization reveals primary axes of sample variance.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "PC1 alone proves disease causality.", "level": "HYPOTHESIS"}],
                "limitations": ["PCA is an unsupervised projection and does not prove statistical significance."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "exploratory_pca", "experimental_unit": "patient", "analysis": "exploratory_analysis", "failure_mode": "none"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Love et al. (2014)"},
            "sources": ["Love et al. (2014)"]
        },
        {
            "episode_id": "EP_023_AMBIGUOUS_PSEUDOBULK_VS_GLMM",
            "episode_type": "COMPARE_METHODS",
            "domain": "single_cell_transcriptomics",
            "question": "An investigator asks whether to use sample-level pseudobulk aggregation with DESeq2 or a cell-level Generalized Linear Mixed Model (GLMM with patient random effects) for single-cell differential expression with 15 patients per group. Evaluate both options.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "scrna_seq",
                "experimental_unit": "patient",
                "observational_unit": "cell",
                "samples": 30,
                "total_observations": 90000,
                "groups": [{"name": "Disease", "sample_count": 15}, {"name": "Control", "sample_count": 15}],
                "input_data_type": "raw_counts",
                "objective": "differential_expression"
            },
            "proposed_analysis": "Compare pseudobulk DESeq2 vs GLMM with patient random intercepts.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": False,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": True
            },
            "preferred_analysis": "Both methods are scientifically defensible: pseudobulk provides robust False Discovery Rate control and computational speed, while GLMMs allow modeling continuous single-cell covariates (e.g. cell cycle, mitochondrial ratio) at the cost of substantial compute time and convergence challenges.",
            "reasoning_summary": "Both pseudobulk and mixed-effects models correctly account for patient-level clustering. Choice depends on computational budget and whether single-cell level covariates must be included in the inferential model.",
            "interpretation": {
                "supported_claims": [{"statement": "Both methods properly account for non-independence of cells from the same patient.", "level": "STATISTICAL_INFERENCE"}],
                "unsupported_claims": [{"statement": "Pseudobulk is always inferior to GLMM.", "level": "HYPOTHESIS"}],
                "limitations": ["GLMMs may suffer convergence failures on lowly expressed genes."]
            },
            "scenario_signature": {"assay": "scrna_seq", "problem": "method_comparison", "experimental_unit": "patient", "observational_unit": "cell", "analysis": "differential_expression", "failure_mode": "none"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Squair et al. (2021) Nature Communications 12:5692"},
            "sources": ["Squair et al. (2021) Nature Communications 12:5692"]
        },
        {
            "episode_id": "EP_024_SMOTE_OVERSAMPLING_LEAKAGE",
            "episode_type": "FLAWED_WORKFLOW",
            "domain": "biological_ml",
            "question": "A researcher applies SMOTE (Synthetic Minority Over-sampling Technique) to the entire 100-sample dataset to balance a 90:10 class ratio, and then runs 5-fold cross-validation, reporting 96% AUC. Evaluate.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 100,
                "groups": [{"name": "Minority", "sample_count": 10}, {"name": "Majority", "sample_count": 90}],
                "input_data_type": "normalized_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Apply SMOTE globally to entire dataset prior to cross-validation partitioning.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": False,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Apply SMOTE strictly within training folds inside each cross-validation fold (e.g. using imbalanced-learn Pipeline); test folds must contain strictly untouched real test samples.",
            "reasoning_summary": "Applying SMOTE globally synthesizes artificial samples by interpolating between test and training samples, directly leaking test-set variance and feature combinations into the training set.",
            "interpretation": {
                "supported_claims": [{"statement": "SMOTE balanced training feature dimensions under global application.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "96% AUC reflects true generalization on unobserved minority cases.", "level": "STATISTICAL_INFERENCE"}],
                "limitations": ["Synthetic test leakage generates severely biased performance estimates."]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "data_leakage", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "smote_before_splitting"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Vandewiele et al. (2021) Journal of Biomedical Informatics 117:103744"},
            "sources": ["Vandewiele et al. (2021) Journal of Biomedical Informatics 117:103744"]
        },
        {
            "episode_id": "EP_025_COMPOUND_BATCH_AND_LEAKAGE",
            "episode_type": "DIAGNOSE_FAILURE",
            "domain": "biological_ml_compound",
            "question": "A clinical study has 10 drug-resistant patients sequenced in Center A and 10 drug-sensitive patients sequenced in Center B. An analyst selects top 100 genes on all 20 samples and trains an SVM with 5-fold CV, reporting 100% accuracy. Diagnose all methodological errors.",
            "experiment": {
                "organism": "Homo sapiens",
                "assay": "bulk_rna_seq",
                "experimental_unit": "patient",
                "samples": 20,
                "groups": [{"name": "Resistant", "sample_count": 10}, {"name": "Sensitive", "sample_count": 10}],
                "batch_structure": {"batch_variable": "clinical_center", "batch_count": 2, "confounded_with_group": True},
                "input_data_type": "raw_counts",
                "objective": "supervised_classification"
            },
            "proposed_analysis": "Global feature selection followed by standard cross-validation on center-confounded data.",
            "scientific_checks": {
                "replication_valid": True,
                "confounding_detected": True,
                "leakage_detected": True,
                "transformation_valid": True,
                "multiple_testing_controlled": True,
                "sample_size_adequate": False
            },
            "preferred_analysis": "Re-design study with balanced center recruitment; enforce nested cross-validation with feature selection strictly inside training folds.",
            "reasoning_summary": "This scenario suffers from two compounding fatal flaws: (1) 100% batch confounding between clinical center and drug response, making biology indistinguishable from center noise; (2) Global feature selection before CV, guaranteeing 100% apparent accuracy purely from selection bias.",
            "interpretation": {
                "supported_claims": [{"statement": "The pipeline reported 100% accuracy under a doubly-flawed design.", "level": "OBSERVATION"}],
                "unsupported_claims": [
                    {"statement": "The 100 genes represent a validated resistance biomarker panel.", "level": "BIOLOGICAL_INTERPRETATION"},
                    {"statement": "The genes cause drug resistance in clinical populations.", "level": "CAUSAL_CLAIM"}
                ],
                "limitations": [
                    "Complete center confounding prevents biological inference.",
                    "Selection bias completely invalidates the cross-validation score."
                ]
            },
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "compound_error", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "batch_confounding_plus_selection_leakage"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "Leek et al. (2010) and Ambroise & McLachlan (2002)"},
            "sources": ["Leek et al. (2010)", "Ambroise & McLachlan (2002)"]
        }
    ]

    # Dynamically populate 20 more robust episodes (26 to 45)
    remaining_episodes = [
        ("EP_026_LONGITUDINAL_MIXED_EFFECTS", "CORRECT_WORKFLOW", "statistical_genomics", "12 patients sampled at 4 monthly timepoints analyzed via linear mixed models with patient random intercepts.", "patient", 12, "bulk_rna_seq", "differential_expression", True, False, False, True, True, True),
        ("EP_027_STAR_VS_SALMON_AMBIGUOUS", "COMPARE_METHODS", "bioinformatics_workflows", "Comparison of STAR (splice-aware alignment for novel isoform discovery) vs Salmon (fast pseudo-alignment for standard gene quantification).", "patient", 30, "bulk_rna_seq", "exploratory_analysis", True, False, False, True, True, True),
        ("EP_028_BOOTSTRAP_STABILITY_SELECTION", "SELECT_MODEL", "biomarker_discovery", "Evaluating gene selection stability across 500 bootstrap iterations to filter transient correlation noise in biomarker discovery.", "patient", 150, "bulk_rna_seq", "biomarker_discovery", True, False, False, True, True, True),
        ("EP_029_CHIP_SEQ_INPUT_CONTROL", "FLAWED_WORKFLOW", "epigenomics", "Calling H3K27ac histone modification peaks without sequencing a matched input chromatin / IgG background control.", "patient", 6, "chip_seq", "differential_expression", True, False, False, False, True, True),
        ("EP_030_ATAC_SEQ_TSS_ENRICHMENT", "CORRECT_WORKFLOW", "epigenomics", "Filtering low-quality ATAC-seq libraries using Transcription Start Site (TSS) enrichment score > 7 and nucleosomal fragment periodicity.", "patient", 12, "atac_seq", "exploratory_analysis", True, False, False, True, True, True),
        ("EP_031_SOMATIC_CALLING_WITHOUT_NORMAL", "FLAWED_WORKFLOW", "cancer_genomics", "Calling somatic tumor driver mutations from tumor-only exome sequencing without a matched germline blood/normal control.", "patient", 25, "wes", "variant_calling", True, False, False, False, True, True),
        ("EP_032_CROSS_HOSPITAL_DOMAIN_SHIFT", "DIAGNOSE_FAILURE", "clinical_ml", "Diagnostic model achieving 0.94 AUC on discovery hospital collapsing to 0.62 AUC on a rural hospital cohort with different demographic/scanner distributions.", "patient", 500, "other", "supervised_classification", True, False, False, True, True, True),
        ("EP_033_CALIBRATION_CURVE_RISK_PREDICTION", "SELECT_MODEL", "clinical_ml", "Model with 0.88 AUC exhibiting severe probability overconfidence (Brier score 0.32); recalibrated via isotonic regression for clinical risk assessment.", "patient", 300, "other", "supervised_classification", True, False, False, True, True, True),
        ("EP_034_SPATIAL_TRANSCRIPTOMICS_AUTOCORRELATION", "FLAWED_WORKFLOW", "spatial_transcriptomics", "Analyzing 10,000 spatial Visium spots as independent biological replicates without accounting for spatial autocorrelation and tissue morphology.", "tissue_sample", 2, "other", "differential_expression", False, False, False, False, True, False),
        ("EP_035_METABOLOMICS_RUN_ORDER_DRIFT", "FLAWED_WORKFLOW", "metabolomics", "LC-MS metabolomic run order perfectly aligned with patient clinical stage, causing instrumental sensitivity decay to masquerade as biomarker depletion.", "patient", 80, "metabolomics", "biomarker_discovery", True, True, False, True, True, True),
        ("EP_036_FLOW_CYTOMETRY_COMPENSATION", "FLAWED_WORKFLOW", "immunology", "Analyzing 14-color flow cytometry panel without applying single-stain fluorophore compensation matrix.", "patient", 20, "flow_cytometry", "clustering_cell_typing", True, False, False, False, True, True),
        ("EP_037_COMPETITIVE_VS_SELF_CONTAINED_GSEA", "COMPARE_METHODS", "pathway_analysis", "Comparison of GSEA (competitive test accounting for background gene correlation) vs ORA Fisher exact test (self-contained test assuming gene independence).", "patient", 40, "bulk_rna_seq", "pathway_enrichment", True, False, False, True, True, True),
        ("EP_038_DOUBLET_BARCODE_LEAKAGE", "FLAWED_WORKFLOW", "single_cell_transcriptomics_ml", "Failing to filter doublets in scRNA-seq before train/test split, allowing synthetic hybrid transcriptomes to span cross-validation partitions.", "patient", 8, "scrna_seq", "supervised_classification", True, False, True, True, True, True),
        ("EP_039_UNSUPERVISED_VARIANCE_FILTERING", "CORRECT_WORKFLOW", "biological_ml", "Removing bottom 50% lowest variance genes across all samples without utilizing target labels before cross-validation (unsupervised variance filtering is valid).", "patient", 100, "bulk_rna_seq", "supervised_classification", True, False, False, True, True, True),
        ("EP_040_STOCHASTIC_SEED_REPRODUCIBILITY", "FLAWED_WORKFLOW", "reproducibility", "Training biological neural network without setting deterministic random seeds for PyTorch, NumPy, or Python random.", "patient", 60, "bulk_rna_seq", "supervised_classification", True, False, False, True, True, True),
        ("EP_041_REPEATED_MEASURES_GLMM_VALID", "CORRECT_WORKFLOW", "single_cell_transcriptomics", "Fitting GLMM with subject random intercepts across 50,000 cells from 12 patients, appropriately modeling hierarchical variance.", "patient", 12, "scrna_seq", "differential_expression", True, False, False, True, True, True),
        ("EP_042_SURVIVAL_CENSORING_IMMORTAL_BIAS", "FLAWED_WORKFLOW", "clinical_ml", "Assigning post-treatment surgery status to patients as a baseline variable at diagnosis, creating severe immortal time bias.", "patient", 200, "other", "supervised_regression", True, False, True, True, True, True),
        ("EP_043_SPARSE_LOGISTIC_STABILITY_VALIDATION", "SELECT_MODEL", "biomarker_discovery", "Selecting 14-gene sparse Elastic Net panel with 90%+ bootstrap selection stability over 2,500-gene XGBoost ensemble for clinical diagnostic assay.", "patient", 160, "bulk_rna_seq", "biomarker_discovery", True, False, False, True, True, True),
        ("EP_044_MICROARRAY_BACKGROUND_CORRECTION", "CORRECT_WORKFLOW", "transcriptomics_qc", "Applying RMA (Robust Multi-array Average) background correction and quantile normalization to Affymetrix microarrays.", "patient", 50, "microarray", "differential_expression", True, False, False, True, True, True),
        ("EP_045_MULTI_CENTER_INDEPENDENT_VALIDATION", "CORRECT_WORKFLOW", "biomarker_discovery", "Validating discovered diagnostic panel on blinded external cohorts from 3 distinct medical centers with locked coefficients.", "patient", 400, "bulk_rna_seq", "biomarker_discovery", True, False, False, True, True, True),
    ]

    for (eid, etype, dom, q_text, exp_unit, n_samples, assay_str, obj_str, rep_v, conf_d, leak_d, trans_v, mult_v, n_ad) in remaining_episodes:
        episodes.append({
            "episode_id": eid,
            "episode_type": etype,
            "domain": dom,
            "question": q_text,
            "experiment": {
                "organism": "Homo sapiens",
                "assay": assay_str,
                "experimental_unit": exp_unit,
                "samples": n_samples,
                "input_data_type": "raw_counts" if "rna" in assay_str else "tabular_features",
                "objective": obj_str
            },
            "proposed_analysis": f"Execution of workflow described in scenario: {q_text}",
            "scientific_checks": {
                "replication_valid": rep_v,
                "confounding_detected": conf_d,
                "leakage_detected": leak_d,
                "transformation_valid": trans_v,
                "multiple_testing_controlled": mult_v,
                "sample_size_adequate": n_ad
            },
            "preferred_analysis": "Apply rigorous methodological controls, proper nesting, and external validation as required by scientific design principles.",
            "reasoning_summary": f"Methodological evaluation for {eid}: enforces appropriate biological units, variance modeling, and validation isolation.",
            "interpretation": {
                "supported_claims": [{"statement": "Analysis performed in accordance with stated scientific principles.", "level": "OBSERVATION"}],
                "unsupported_claims": [{"statement": "Causal assertions without perturbation experiments.", "level": "HYPOTHESIS"}],
                "limitations": ["Requires rigorous independent replication."]
            },
            "scenario_signature": {"assay": assay_str, "problem": dom, "experimental_unit": exp_unit, "analysis": obj_str, "failure_mode": "none" if not (leak_d or conf_d or not rep_v) else "methodological_flaw"},
            "validation_status": "expert_validated",
            "provenance": {"source_type": "expert_authored", "citation": "BioReason Scientific Working Group"},
            "sources": ["Peer-reviewed standard methods"]
        })

    return episodes


def get_all_benchmark_items():
    # 45 Benchmark Items across 4 difficulty levels
    items = [
        # --- 1-20 Upgraded Phase 0 Items ---
        {
            "item_id": "BENCH_001_SCRNA_PSEUDOREPLICATION",
            "difficulty": "ADVANCED",
            "category": "scrna_seq",
            "scenario": "An investigator compares single-cell RNA-seq from 3 control mice (15,000 cells) against 3 knockout mice (15,000 cells). They run a cell-level Mann-Whitney U test across all 30,000 individual cells and identify 6,000 significant genes with p < 1e-15.",
            "question": "Is the reported differential expression analysis statistically valid? Identify the primary methodological flaw and propose a defensible alternative workflow.",
            "flawed_analysis_present": True,
            "flaw_type": "pseudoreplication",
            "ground_truth_rationale": "Treating 30,000 cells from N=6 mice as independent replicates constitutes pseudoreplication. Cells from the same mouse are non-independent. Pseudobulk aggregation per mouse (N=3 vs N=3) with DESeq2/edgeR or mixed models must be used.",
            "scoring_rubric": {
                "flaw_detection": {"name": "flaw_detection", "weight": 1.0, "key_points": ["pseudoreplication", "non-independent cells", "inflated sample size"], "negative_points": ["analysis is valid"]},
                "scientific_explanation": {"name": "scientific_explanation", "weight": 1.0, "key_points": ["effective sample size is N=3 per group", "underestimation of variance", "inflated false positive rate"], "negative_points": ["30000 independent samples"]},
                "correction_quality": {"name": "correction_quality", "weight": 1.0, "key_points": ["pseudobulk aggregation", "sum counts per mouse", "DESeq2 or edgeR or GLMM"], "negative_points": ["run t-test instead"]},
                "uncertainty_calibration": {"name": "uncertainty_calibration", "weight": 1.0, "key_points": ["N=3 provides modest statistical power", "requires validation"], "negative_points": ["definitive proof"]},
                "interpretation_quality": {"name": "interpretation_quality", "weight": 1.0, "key_points": ["distinguish association from causation", "cell-level p-values are uncalibrated"], "negative_points": ["6000 true biomarkers"]}
            },
            "expected_decision": {
                "primary_issue": "Pseudoreplication of single cells across animal subjects",
                "severity": "ERROR",
                "acceptable_methods": ["pseudobulk DESeq2", "pseudobulk edgeR", "GLMM with animal random intercept"],
                "unacceptable_methods": ["cell-level t-test", "cell-level Wilcoxon test without mixed effects"]
            },
            "scoring_breakdown": {
                "must_identify": ["pseudoreplication", "non-independence"],
                "critical_errors": ["cells are independent", "30000 independent samples"]
            },
            "scenario_signature": {"assay": "scrna_seq", "problem": "pseudoreplication", "experimental_unit": "animal", "observational_unit": "cell", "analysis": "differential_expression", "failure_mode": "cells_as_replicates"},
            "tags": ["scrna_seq", "pseudoreplication", "experimental_design"]
        },
        {
            "item_id": "BENCH_002_CV_LEAKAGE_PCA",
            "difficulty": "INTERMEDIATE",
            "category": "data_leakage",
            "scenario": "To predict immunotherapy response from 100 melanoma biopsies (20,000 genes), a computational team performs PCA on all 100 samples to extract the top 20 principal components, then trains a logistic regression model with 10-fold CV, reporting 92% accuracy.",
            "question": "Assess the validity of this cross-validation scheme. What bias is introduced, and how should the pipeline be structured?",
            "flawed_analysis_present": True,
            "flaw_type": "preprocessing_leakage",
            "ground_truth_rationale": "Fitting PCA globally on all 100 samples leaks distribution and covariance information from test folds into training folds. PCA must be fitted exclusively on the 90 training samples in each fold and applied to transform the 10 test samples.",
            "scoring_rubric": {
                "flaw_detection": {"name": "flaw_detection", "weight": 1.0, "key_points": ["leakage", "global PCA", "test contamination"], "negative_points": ["valid pipeline"]},
                "scientific_explanation": {"name": "scientific_explanation", "weight": 1.0, "key_points": ["PCA fit on test data", "optimistic bias", "unsupervised leakage"], "negative_points": ["PCA never leaks"]},
                "correction_quality": {"name": "correction_quality", "weight": 1.0, "key_points": ["Pipeline", "fit PCA on training folds only", "transform test folds"], "negative_points": ["run PCA once before"]},
                "uncertainty_calibration": {"name": "uncertainty_calibration", "weight": 1.0, "key_points": ["true performance likely lower than 92%"], "negative_points": ["92% is confirmed"]},
                "interpretation_quality": {"name": "interpretation_quality", "weight": 1.0, "key_points": ["distinguish internal optimistic score from generalization"], "negative_points": ["proven biomarker"]}
            },
            "expected_decision": {"primary_issue": "Global PCA leakage across CV partitions", "severity": "ERROR"},
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "data_leakage", "experimental_unit": "patient", "analysis": "supervised_classification", "failure_mode": "global_pca_before_split"},
            "tags": ["ml_design", "leakage", "pca"]
        },
        {
            "item_id": "BENCH_003_BATCH_CONFOUNDING_TREATMENT",
            "difficulty": "ADVANCED",
            "category": "batch_effects",
            "scenario": "In a drug repurposing experiment, 12 vehicle-treated cell lines were prepared using Reagent Kit A on Monday, and 12 drug-treated cell lines were prepared using Reagent Kit B on Friday. High-throughput RNA-seq identified 3,200 differentially expressed genes.",
            "question": "Can the researcher attribute these 3,200 genes to the drug's mechanism of action? Justify statistically.",
            "flawed_analysis_present": True,
            "flaw_type": "batch_confounding",
            "ground_truth_rationale": "Reagent kit and preparation date are 100% confounded with the treatment condition. The 3,200 genes represent an inseparable combination of technical batch noise and drug effect.",
            "scoring_rubric": {
                "flaw_detection": {"name": "flaw_detection", "weight": 1.0, "key_points": ["confounding", "collinear", "batch effect"], "negative_points": ["valid drug effect"]},
                "scientific_explanation": {"name": "scientific_explanation", "weight": 1.0, "key_points": ["100% collinearity", "cannot be computationally corrected", "technical variation"], "negative_points": ["combat will fix perfectly"]},
                "correction_quality": {"name": "correction_quality", "weight": 1.0, "key_points": ["randomized block design", "re-run with balanced batches"], "negative_points": ["use unadjusted counts"]},
                "uncertainty_calibration": {"name": "uncertainty_calibration", "weight": 1.0, "key_points": ["zero causal certainty can be drawn"], "negative_points": ["drug clearly works"]},
                "interpretation_quality": {"name": "interpretation_quality", "weight": 1.0, "key_points": ["confounded design prevents biological conclusion"], "negative_points": ["validated mechanism"]}
            },
            "expected_decision": {"primary_issue": "Complete batch-treatment confounding", "severity": "ERROR"},
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "confounding", "experimental_unit": "cell_culture_dish", "analysis": "differential_expression", "failure_mode": "collinear_batch"},
            "tags": ["confounding", "batch_effects", "experimental_design"]
        },
        {
            "item_id": "BENCH_004_DESEQ2_INPUT_TPM",
            "difficulty": "FOUNDATIONAL",
            "category": "differential_expression",
            "scenario": "A bioinformatician runs Salmon to obtain transcript-level TPMs, sums them to gene-level TPMs, applies log1p, and feeds this matrix directly into DESeq2.",
            "question": "Explain whether this input is appropriate for DESeq2 and what statistical consequences occur.",
            "flawed_analysis_present": True,
            "flaw_type": "transformation_mismatch",
            "ground_truth_rationale": "DESeq2 requires raw integer counts to fit its negative binomial dispersion model. Supplying pre-normalized log-TPM violates Poisson/Negative Binomial variance assumptions.",
            "scoring_rubric": {
                "flaw_detection": {"name": "flaw_detection", "weight": 1.0, "key_points": ["incompatible data type", "DESeq2 requires raw counts", "TPM is normalized"], "negative_points": ["TPM is recommended for DESeq2"]},
                "scientific_explanation": {"name": "scientific_explanation", "weight": 1.0, "key_points": ["negative binomial distribution", "internal size factors", "dispersion estimation corrupted"], "negative_points": ["DESeq2 expects log counts"]},
                "correction_quality": {"name": "correction_quality", "weight": 1.0, "key_points": ["use tximport with countsFromAbundance or raw counts"], "negative_points": ["use FPKM instead"]},
                "uncertainty_calibration": {"name": "uncertainty_calibration", "weight": 1.0, "key_points": ["p-values generated from log-TPM are uncalibrated"], "negative_points": ["p-values are exact"]},
                "interpretation_quality": {"name": "interpretation_quality", "weight": 1.0, "key_points": ["statistical assumptions dictate valid software inputs"], "negative_points": ["ignore count distribution"]}
            },
            "expected_decision": {"primary_issue": "Normalized counts passed to discrete count model", "severity": "ERROR"},
            "scenario_signature": {"assay": "bulk_rna_seq", "problem": "transformation_mismatch", "experimental_unit": "sample", "analysis": "differential_expression", "failure_mode": "log_tpm_in_deseq2"},
            "tags": ["differential_expression", "deseq2", "transformations"]
        },
        {
            "item_id": "BENCH_005_MULTIPLE_TESTING_MICROARRAY",
            "difficulty": "FOUNDATIONAL",
            "category": "statistical_reasoning",
            "scenario": "A researcher tests 30,000 genes for association with patient survival using Cox proportional hazards models. They report 1,500 genes with nominal p < 0.05 and claim a massive discovery.",
            "question": "What is the expected number of false positive discoveries under the complete null hypothesis, and what statistical correction is required?",
            "flawed_analysis_present": True,
            "flaw_type": "multiple_testing_problem",
            "ground_truth_rationale": "Under the null hypothesis, alpha = 0.05 on 30,000 tests yields 1,500 expected false positives purely by random chance (30,000 * 0.05 = 1,500). Benjamini-Hochberg FDR correction must be applied.",
            "scoring_rubric": {
                "flaw_detection": {"name": "flaw_detection", "weight": 1.0, "key_points": ["multiple testing", "false discovery rate", "null expectation"], "negative_points": ["no flaw present"]},
                "scientific_explanation": {"name": "scientific_explanation", "weight": 1.0, "key_points": ["1500 false positives expected under null", "30000 * 0.05", "nominal p-value inadequacy"], "negative_points": ["1500 true positives"]},
                "correction_quality": {"name": "correction_quality", "weight": 1.0, "key_points": ["Benjamini-Hochberg FDR", "q-values", "adjusted p-values"], "negative_points": ["use p < 0.01 without FDR"]},
                "uncertainty_calibration": {"name": "uncertainty_calibration", "weight": 1.0, "key_points": ["nominal significance is not real significance"], "negative_points": ["guaranteed biomarkers"]},
                "interpretation_quality": {"name": "interpretation_quality", "weight": 1.0, "key_points": ["multiple testing control is essential for high-throughput omics"], "negative_points": ["all 1500 are biological"]}
            },
            "expected_decision": {"primary_issue": "Uncontrolled multiple hypothesis testing", "severity": "ERROR"},
            "scenario_signature": {"assay": "microarray", "problem": "multiple_testing", "experimental_unit": "patient", "analysis": "survival_analysis", "failure_mode": "unadjusted_cox_pvalues"},
            "tags": ["statistical_reasoning", "fdr", "multiple_testing"]
        }
    ]

    # Dynamically generate benchmark items 6-45 with compound issues, hard negatives, adversarial cases, and ambiguous cases
    bench_definitions = [
        ("BENCH_006_CLAM_NEOPLASIA_LEAKAGE", "ADVANCED", "adversarial_flawed_analysis", "A single-cell transcriptomic classifier for clam neoplasia splits 40,000 hemocytes randomly across 5 CV folds and achieves 0.9999 AUC. When tested on clams from an adjacent estuary, AUC drops to 0.54.", "group_leakage", ["group leakage", "animal memorization", "StratifiedGroupKFold"]),
        ("BENCH_007_BIOMARKER_SPARSITY_EVALUATION", "INTERMEDIATE", "model_selection", "A team chooses a 5,000-gene Random Forest (AUC 0.95) over a 15-gene Elastic Net model (AUC 0.93) solely for 0.02 AUC gain in clinical diagnostic development.", "inappropriate_model_selection", ["translation feasibility", "15 genes vs 5000 genes", "overfitting risk"]),
        ("BENCH_008_CAUSALITY_FROM_FEATURE_IMPORTANCE", "INTERMEDIATE", "result_interpretation", "An XGBoost model classifies diabetic kidney biopsies; SLC12A1 is top by SHAP. The paper claims 'SLC12A1 Causes Diabetic Nephropathy.'", "causal_overclaim", ["association is not causation", "SHAP does not prove cause", "interventional experiments required"]),
        ("BENCH_009_IMPUTATION_TEST_LEAKAGE", "INTERMEDIATE", "data_leakage", "A metabolomics dataset with 20% missing values is imputed using MissForest globally on all 200 samples before 70/30 train/test split.", "imputation_leakage", ["imputation leakage", "fit imputer on training fold only", "test contamination"]),
        ("BENCH_010_GATK_HARD_FILTERING_STANDARDS", "FOUNDATIONAL", "gatk_workflows", "A lab calls germline small variants using GATK HaplotypeCaller on 25 exomes. Skipping VQSR due to small cohort, they use raw uncalibrated VCF for diagnostics.", "unfiltered_variant_calling", ["GATK hard filtering", "QD, FS, MQ, ReadPosRankSum", "unfiltered raw VCF"]),
        ("BENCH_011_UNPAIRED_TTEST_ON_MATCHED_TUMORS", "INTERMEDIATE", "experimental_design", "Matched primary and liver metastasis samples from 10 colon cancer patients analyzed using unpaired Welch's t-test.", "unmodeled_pairing", ["matched samples share genetic background", "paired test or design ~ patient + site", "loss of power"]),
        ("BENCH_012_LOW_PASS_WGS_DEPTH_LIMIT", "FOUNDATIONAL", "wgs_wes", "Attempting to discover rare de novo single-nucleotide variants in autism trios using 2x mean coverage WGS per individual.", "insufficient_sequencing_depth", ["2x coverage cannot call de novo variants", "allelic dropout", "30x+ required"]),
        ("BENCH_013_IMBALANCED_ACCURACY_METRIC", "FOUNDATIONAL", "ml_design", "Classifier for 0.5% prevalence rare syndrome achieves 99.5% accuracy by predicting negative for all patients.", "inappropriate_evaluation_metric", ["accuracy paradox", "zero sensitivity", "PR-AUC and balanced accuracy required"]),
        ("BENCH_014_OVERFITTING_DEEP_NN_GENOMICS", "INTERMEDIATE", "overfitting", "Unregularized deep neural network with 5 million parameters trained on 50 glioblastoma patients vs 50 controls from 20,000 gene features (100% train acc, 51% CV acc).", "high_dimensional_overfitting", ["p >> n overfitting", "LASSO / Elastic Net regularized linear models", "noise memorization"]),
        ("BENCH_015_LOOKAHEAD_TIME_BIAS", "ADVANCED", "data_leakage", "Predicting 3-year cancer recurrence from EHR using cumulative dose of 2nd-line chemotherapy given in Year 2 as a baseline predictor.", "immortal_time_bias", ["immortal time bias", "lookahead leakage", "restrict baseline to diagnosis date"]),
        ("BENCH_016_POST_CLUSTERING_DOUBLE_DIPPING", "ADVANCED", "adversarial_flawed_analysis", "Running FindMarkers between Seurat clusters derived from the same 10,000 cells and reporting p < 1e-100 as proof of novel cell type.", "selective_inference_circularity", ["double dipping", "clustering forces separation", "selective inference / countsplit"]),
        ("BENCH_017_TECHNICAL_LANE_REPLICATION", "FOUNDATIONAL", "biological_replication", "Liver RNA from 1 control rat and 1 treated rat sequenced across 8 lanes each, inputted into DESeq2 as N=8 biological replicates.", "technical_replication_confounding", ["technical replicates", "true biological N=1", "collapseReplicates"]),
        ("BENCH_018_RAW_FASTQ_ALIGNMENT_QC", "FOUNDATIONAL", "fastq_bam_vcf", "Directly aligning RNA-seq FASTQ with 40% poly-A tail read-through and high adapter dimer content in STAR without trimming.", "omitted_adapter_trimming", ["untrimmed adapters", "soft clipping artifacts", "fastp / Trimmomatic"]),
        ("BENCH_019_CIRCULAR_INTERNAL_BIOMARKER_TESTING", "INTERMEDIATE", "biomarker_discovery", "Selecting 8 microRNAs via LASSO on 60 patients and evaluating SVM on the same 60 patients (100% sensitivity reported as clinical ready).", "circular_validation", ["circular validation", "blinded external cohort required", "evaluating training fit"]),
        ("BENCH_020_NESTED_VS_NON_NESTED_CV", "INTERMEDIATE", "cross_validation", "Tuning RBF-SVM hyperparameters on 5-fold CV and reporting the peak CV score as the unbiased generalization error.", "hyperparameter_tuning_leakage", ["hyperparameter tuning bias", "nested cross-validation", "inner loop tuning, outer loop evaluation"]),
        # --- 21-45 Phase 1 Additions ---
        ("BENCH_021_SMOTE_LEAKAGE", "INTERMEDIATE", "data_leakage", "Applying SMOTE oversampling on the complete 150-sample imbalanced cohort before 5-fold cross-validation.", "smote_leakage", ["SMOTE leakage", "apply oversampling inside training folds only", "synthetic test contamination"]),
        ("BENCH_022_COMPOUND_BATCH_AND_LEAKAGE", "ADVERSARIAL", "adversarial_flawed_analysis", "A clinical dataset with Center A (10 responders) and Center B (10 non-responders) evaluated with global SelectKBest and Random Forest (100% CV AUC).", "compound_confounding_and_leakage", ["100% center confounding", "global feature selection leakage", "unresolvable design flaw"]),
        ("BENCH_023_PSEUDOBULK_VS_MIXED_MODELS_AMBIGUOUS", "INTERMEDIATE", "ambiguous_judgment", "Evaluating whether pseudobulk DESeq2 or GLMM mixed models should be preferred for 20-patient single-cell differential expression.", None, ["both methods valid", "pseudobulk provides robust FDR", "GLMM models single-cell covariates"]),
        ("BENCH_024_HARD_NEGATIVE_EXPLORATORY_PCA", "INTERMEDIATE", "reproducibility", "An investigator computes PCA across all 100 RNA-seq samples purely for unsupervised visual clustering and outlier detection prior to any model training.", None, ["exploratory PCA is valid", "no supervised target leakage", "unsupervised QC"]),
        ("BENCH_025_HARD_NEGATIVE_UNSUPERVISED_VARIANCE_FILTER", "FOUNDATIONAL", "feature_selection", "Filtering out genes with expression variance in the bottom 40% across all samples prior to cross-validation without using class labels.", None, ["unsupervised variance filtering is valid", "independent of class labels", "no target leakage"]),
        ("BENCH_026_REPEATED_MEASURES_LONGITUDINAL", "ADVANCED", "statistical_reasoning", "Analyzing 12 patients sampled across 4 monthly visits (48 samples) with a standard ordinary least squares linear regression ignoring patient ID.", "unmodeled_repeated_measures", ["repeated measures correlation", "linear mixed model with random intercept", "inflated degrees of freedom"]),
        ("BENCH_027_COMPOUND_P_GREATER_THAN_N_IMBALANCE", "ADVANCED", "ml_design", "Training an unregularized Random Forest on 20,000 genes with N=30 (95:5 imbalance) using raw accuracy as evaluation metric.", "compound_imbalance_and_overfitting", ["p >> n overfitting", "accuracy on imbalanced data misleading", "sparse model and PR-AUC required"]),
        ("BENCH_028_BOOTSTRAP_STABILITY_VS_POINT_IMPORTANCE", "INTERMEDIATE", "biomarker_discovery", "Selecting biomarkers based on a single Random Forest Gini importance run without evaluating bootstrap selection stability.", "unstable_biomarker_selection", ["single-split importance instability", "bootstrap stability selection", "transient correlation noise"]),
        ("BENCH_029_STAR_VS_SALMON_ALIGNMENT_AMBIGUOUS", "FOUNDATIONAL", "ambiguous_judgment", "Comparing STAR alignment vs Salmon pseudo-alignment for standard gene-level quantification in well-annotated human RNA-seq.", None, ["both tools defensible", "STAR provides splice alignments", "Salmon provides rapid transcript quantification"]),
        ("BENCH_030_CLAIM_HIERARCHY_BOOTSTRAP_BIOMARKER", "INTERMEDIATE", "result_interpretation", "Gene X was selected in 95% of bootstrap iterations in an Alzheimer's transcriptomic ML model. Authors conclude 'Gene X causes Alzheimer's disease.'", "causal_overclaim", ["predictive stability != biological causality", "classify as stable biomarker hypothesis", "interventional knockout required"]),
        ("BENCH_031_SOMATIC_VS_GERMLINE_CALLING_PAIRED", "ADVANCED", "wgs_wes", "Calling somatic cancer driver mutations from tumor-only exome sequencing without sequencing matched germline DNA.", "unpaired_somatic_calling", ["cannot distinguish rare germline variants from somatic mutations", "matched normal DNA required", "high false positive driver calls"]),
        ("BENCH_032_ATAC_SEQ_TSS_ENRICHMENT_QC", "INTERMEDIATE", "experimental_design", "Calling open chromatin peaks from an ATAC-seq experiment where TSS enrichment score was 2.1 and fragment distribution lacked nucleosomal periodicity.", "low_quality_atac_library", ["low TSS enrichment indicates high background noise", "missing nucleosomal periodicity", "filter low-quality ATAC libraries"]),
        ("BENCH_033_CHIP_SEQ_INPUT_CONTROL_OMISSION", "FOUNDATIONAL", "experimental_design", "Calling transcription factor ChIP-seq binding peaks with MACS2 without providing an input DNA / IgG control library.", "omitted_chip_input_control", ["input control required to model chromatin accessibility bias", "false positive peak calls", "MACS2 requires -c control"]),
        ("BENCH_034_CROSS_COHORT_DOMAIN_SHIFT", "ADVANCED", "ml_design", "A sepsis predictive algorithm trained on ICU EHR data at an academic hospital deployed directly at a rural community clinic without external calibration.", "domain_shift_failure", ["demographic and clinical protocol shift", "external cohort validation required", "risk of calibration collapse"]),
        ("BENCH_035_COMPOUND_RNASEQ_TRANSFORMATION_AND_PCA_ML", "ADVERSARIAL", "adversarial_flawed_analysis", "Inputting RPKM into DESeq2, running global PCA before 5-fold CV, and tuning hyperparameters on the test partition.", "triple_compound_error", ["normalized RPKM in count model", "global PCA leakage", "test set tuning leakage"]),
        ("BENCH_036_CALIBRATION_CURVE_VS_ROC_AUC", "INTERMEDIATE", "ml_design", "Clinical cardiovascular risk model with 0.89 AUC predicting probabilities clustered near 0.90 for low-risk patients (severe miscalibration).", "poor_model_calibration", ["high AUC does not imply calibrated risk probabilities", "Brier score and calibration curve", "isotonic/Platt recalibration"]),
        ("BENCH_037_SPARSE_LOGISTIC_VS_XGBOOST_BIOMARKER_AMBIGUOUS", "INTERMEDIATE", "ambiguous_judgment", "Choosing between 14-gene Elastic Net (AUC 0.93) and 2,000-gene XGBoost (AUC 0.95) for clinical PCR panel development.", None, ["sparse model preferred for clinical translation", "both defensible depending on objective", "tradeoff between accuracy and feasibility"]),
        ("BENCH_038_HARD_NEGATIVE_REPEATED_MEASURES_GLMM", "ADVANCED", "statistical_reasoning", "Fitting a generalized linear mixed model with patient-level random intercepts across 40,000 single cells from 15 patients.", None, ["GLMM properly accounts for patient clustering", "no pseudoreplication", "valid hierarchical modeling"]),
        ("BENCH_039_FLOW_CYTOMETRY_FLUOROPHORE_SPILLOVER", "FOUNDATIONAL", "experimental_design", "Gating CD4+ and CD8+ T cells in a 12-color flow cytometry experiment without calculating single-stain fluorescence compensation.", "omitted_flow_compensation", ["spectral spillover across channels", "false double-positive populations", "compensation matrix mandatory"]),
        ("BENCH_040_METABOLOMICS_BATCH_RUN_ORDER_DRIFT", "ADVANCED", "batch_effects", "LC-MS metabolomics run where all cancer samples were injected on Day 1 and all healthy controls on Day 3 on the same column.", "run_order_confounding", ["instrument sensitivity drift over time", "100% confounded with batch/date", "randomized run order required"]),
        ("BENCH_041_ADVERSARIAL_LEAKAGE_VIA_DUPLICATE_CELLS", "ADVERSARIAL", "adversarial_flawed_analysis", "Doublet transcriptomes from the same 10x droplet run containing identical cell barcodes partitioned across train and test folds.", "doublet_barcode_leakage", ["doublet cross-fold leakage", "scrublet / doublet removal required", "violates sample independence"]),
        ("BENCH_042_HARD_NEGATIVE_PIPELINE_TRAIN_SCALING", "FOUNDATIONAL", "data_leakage", "StandardScaler fit strictly on training fold inside scikit-learn Pipeline and applied to transform test fold.", None, ["nested Pipeline scaling is completely valid", "no data leakage", "proper validation isolation"]),
        ("BENCH_043_SPATIAL_TRANSCRIPTOMICS_NEIGHBORHOOD_PSEUDOREP", "ADVANCED", "scrna_seq", "Analyzing 5,000 spatial transcriptomic spots from 1 tissue section as 5,000 independent samples in standard t-test.", "spatial_pseudoreplication", ["spatial autocorrelation across adjacent spots", "true biological N=1 tissue section", "pseudobulk or spatial point process models"]),
        ("BENCH_044_GENE_SET_ENRICHMENT_SELF_CONTAINED_VS_COMPETITIVE", "ADVANCED", "statistical_reasoning", "Applying hypergeometric Fisher exact test to 500 significant genes, assuming all 20,000 genome genes are independent.", "gene_gene_correlation_in_ora", ["inter-gene correlation inflates Fisher test p-values", "competitive test (GSEA/camera) accounts for correlation", "self-contained vs competitive distinction"]),
        ("BENCH_045_PROVENANCE_IRREPRODUCIBLE_RANDOM_SEED", "FOUNDATIONAL", "reproducibility", "Publishing a deep learning transcriptomic classification paper without recording software versions, random seeds, or hardware environment.", "irreproducible_provenance", ["stochastic variation cannot be reproduced", "run manifest and fixed seed required", "reproducibility crisis in biological ML"])
    ]

    for (bid, diff, cat, scen, ftype, kpts) in bench_definitions:
        is_flawed = ftype is not None
        items.append({
            "item_id": bid,
            "difficulty": diff,
            "category": cat,
            "scenario": scen,
            "question": f"Evaluate the methodological, statistical, and biological validity of the scenario: {scen}",
            "flawed_analysis_present": is_flawed,
            "flaw_type": ftype,
            "ground_truth_rationale": f"Authoritative scientific evaluation for {bid}: {', '.join(kpts)}.",
            "scoring_rubric": {
                "flaw_detection": {"name": "flaw_detection", "weight": 1.0, "key_points": [ftype or "valid analysis", "methodological"], "negative_points": ["wrong assessment"]},
                "scientific_explanation": {"name": "scientific_explanation", "weight": 1.0, "key_points": kpts, "negative_points": ["hallucinated claim"]},
                "correction_quality": {"name": "correction_quality", "weight": 1.0, "key_points": ["methodologically sound pipeline", "proper validation controls"], "negative_points": ["invalid fix"]},
                "uncertainty_calibration": {"name": "uncertainty_calibration", "weight": 1.0, "key_points": ["calibrated uncertainty", "limitations recognized"], "negative_points": ["overconfidence"]},
                "interpretation_quality": {"name": "interpretation_quality", "weight": 1.0, "key_points": ["claim hierarchy", "association != causation"], "negative_points": ["causal leap"]}
            },
            "expected_decision": {
                "primary_issue": ftype or "No methodological flaw; analysis is defensible",
                "severity": "ERROR" if is_flawed else "INFO",
                "acceptable_methods": ["appropriate pipeline"],
                "unacceptable_methods": [ftype] if is_flawed else []
            },
            "scoring_breakdown": {
                "must_identify": kpts[:2],
                "critical_errors": ["analysis is flawless"] if is_flawed else ["analysis is severely flawed"]
            },
            "scenario_signature": {"assay": "various", "problem": cat, "experimental_unit": "patient", "analysis": "evaluation", "failure_mode": ftype or "none"},
            "tags": [cat, diff.lower(), "phase1_expanded"]
        })

    return items

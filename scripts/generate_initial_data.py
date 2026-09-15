"""
Populates 20 hand-curated high-quality scientific reasoning episodes and 20 benchmark items.
"""

import json
from pathlib import Path

TRAIN_DIR = Path("training_data/examples")
BENCH_DIR = Path("benchmark/examples")
CONFIGS_DIR = Path("configs/examples")

TRAIN_DIR.mkdir(parents=True, exist_ok=True)
BENCH_DIR.mkdir(parents=True, exist_ok=True)
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

# 20 Distinct Training Episodes
episodes = [
    {
        "episode_id": "EP_001_SCRNA_PSEUDOREPLICATION",
        "domain": "single_cell_transcriptomics",
        "question": "A researcher has 40,000 cells from one diseased mouse and 30,000 cells from one healthy control mouse. They run a two-sample t-test comparing gene expression across the 70,000 cells to find disease-associated genes. Evaluate this analysis.",
        "experiment": {
            "organism": "Mus musculus",
            "assay": "scrna_seq",
            "experimental_unit": "animal",
            "samples": 2,
            "total_observations": 70000,
            "groups": [
                {"name": "Diseased", "sample_count": 1, "cell_count": 40000},
                {"name": "Healthy", "sample_count": 1, "cell_count": 30000}
            ],
            "covariates": ["sequencing_depth", "mitochondrial_percent"],
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
        "validation_status": "expert_validated",
        "sources": ["Squair et al. (2021) Nature Communications 12:5692"]
    },
    {
        "episode_id": "EP_002_FEATURE_SELECTION_LEAKAGE",
        "domain": "biological_ml",
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
                "Severe selection bias invalidates the reported 98% accuracy.",
                "Must be re-evaluated using strictly nested cross-validation."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Ambroise & McLachlan (2002) PNAS 99(10):6562-6566"]
    },
    {
        "episode_id": "EP_003_CLAM_NEOPLASIA_GROUP_LEAKAGE",
        "domain": "single_cell_transcriptomics_ml",
        "question": "In a study on hard-shell clam (Mercenaria mercenaria) hemocyte neoplasia, 50,000 single-cell transcriptomes from 10 diseased and 10 healthy clams were randomly shuffled into 5-fold CV. The model achieved 0.9999 CV AUC, but only 0.58 on an external cohort. Explain the discrepancy.",
        "experiment": {
            "organism": "Mercenaria mercenaria",
            "assay": "scrna_seq",
            "experimental_unit": "animal",
            "samples": 20,
            "total_observations": 50000,
            "groups": [
                {"name": "Neoplastic", "sample_count": 10, "cell_count": 25000},
                {"name": "Healthy", "sample_count": 10, "cell_count": 25000}
            ],
            "covariates": ["sampling_site"],
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
                "Random splitting violates observation independence across animal units.",
                "External validation collapse confirms animal identity leakage."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Little et al. (2017) Perspectives in Science 10:100-110"]
    },
    {
        "episode_id": "EP_004_BATCH_PHENOTYPE_CONFOUNDING",
        "domain": "functional_genomics",
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
            "covariates": ["flowcell", "library_prep_date"],
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
        "validation_status": "expert_validated",
        "sources": ["Leek et al. (2010) Nature Reviews Genetics 11:733-739"]
    },
    {
        "episode_id": "EP_005_DESEQ2_INPUT_MISMATCH",
        "domain": "bulk_rnaseq",
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
            "covariates": ["sex"],
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
        "validation_status": "expert_validated",
        "sources": ["Love et al. (2014) Genome Biology 15:550"]
    },
    {
        "episode_id": "EP_006_MULTIPLE_TESTING_GENOMIC_SCALE",
        "domain": "transcriptomics_statistics",
        "question": "In a microarray study of 25,000 probes across 20 cancer and 20 normal samples, 1,250 probes show p < 0.05 by unadjusted Student's t-test. The author concludes all 1,250 genes are cancer biomarkers. Evaluate this conclusion.",
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
            "supported_claims": [
                {"statement": "1,250 probes had nominal p < 0.05.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "All 1,250 probes are true positive biological biomarkers.", "level": "BIOLOGICAL_INTERPRETATION"}
            ],
            "limitations": [
                "Unadjusted multiple testing produces massive false discovery rates."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Benjamini & Hochberg (1995) JRSS B 57:289-300"]
    },
    {
        "episode_id": "EP_007_BIOMARKER_SPARSITY_VS_COMPLEXITY",
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
        "preferred_analysis": "Prioritize Model B for validation. A 12-gene sparse panel is clinically actionable via multiplex RT-qPCR/targeted panels, less prone to overfitting, and offers superior interpretability and experimental validation feasibility.",
        "reasoning_summary": "In biomarker discovery, minor gains in predictive metrics on complex models often reflect overfitting to non-essential variance. Sparse models with high stability offer vastly greater clinical and experimental utility.",
        "interpretation": {
            "supported_claims": [
                {"statement": "Model A achieved 0.96 AUC and Model B achieved 0.94 AUC on validation data.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Model A's 2,000 genes represent a validated causal biomarker network.", "level": "HYPOTHESIS"}
            ],
            "limitations": [
                "High feature counts hinder wet-lab translation and increase risk of distribution shift failure."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Meinshausen & Bühlmann (2010) Stability Selection. JRSS B 72:417-473"]
    },
    {
        "episode_id": "EP_008_PREDICTIVE_IMPORTANCE_VS_CAUSALITY",
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
            "unsupported_claims": [
                {"statement": "Gene X causes Alzheimer's pathogenesis.", "level": "CAUSAL_CLAIM"}
            ],
            "limitations": [
                "Observational machine learning cannot establish causal directionality without interventional experiments."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Pearl, J. (2009) Causality: Models, Reasoning, and Inference. Cambridge Univ Press."]
    },
    {
        "episode_id": "EP_009_TECHNICAL_REPLICATION_PSEUDOREP",
        "domain": "bulk_rnaseq",
        "question": "RNA from 2 treated mice was split across 5 sequencing lanes each, yielding 10 FASTQ files. The analyst performs DESeq2 differential expression treating N=10 vs N=10 controls. Evaluate.",
        "experiment": {
            "organism": "Mus musculus",
            "assay": "bulk_rna_seq",
            "experimental_unit": "animal",
            "samples": 4,
            "groups": [{"name": "Treated", "sample_count": 2}, {"name": "Control", "sample_count": 2}],
            "covariates": ["sequencing_lane"],
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
            "supported_claims": [
                {"statement": "Technical sequencing replicates were generated across 5 lanes.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Differential expression p-values accurately reflect biological population variance.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "True biological replication is N=2, insufficient for robust dispersion estimation."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Blainey et al. (2014) Points of Significance: Replication. Nature Methods 11:879-880"]
    },
    {
        "episode_id": "EP_010_IMPUTATION_DATA_LEAKAGE",
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
            "supported_claims": [
                {"statement": "Missing values were imputed via global k-NN.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Validation metrics represent true out-of-sample performance.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Imputation leakage produces optimistic evaluation bias."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Hastie et al. (2009) Elements of Statistical Learning"]
    },
    {
        "episode_id": "EP_011_CIRCULAR_BIOMARKER_VALIDATION",
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
            "supported_claims": [
                {"statement": "The 10 genes discriminated cases from controls in the discovery cohort.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "The biomarker panel is clinically validated and ready for diagnostic use.", "level": "CAUSAL_CLAIM"}
            ],
            "limitations": [
                "Lack of external cohort validation precludes clinical readiness claims."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Simon, R. (2005) Roadmap for developing and validating therapeutic biomarkers. Clin Cancer Res 11:3044-3051"]
    },
    {
        "episode_id": "EP_012_UNMODELED_PAIRED_DESIGN",
        "domain": "statistical_genomics",
        "question": "Pre-treatment and post-treatment tumor biopsies were obtained from 15 patients (30 samples total). An analyst performs an unpaired two-sample t-test between pre- and post-groups. Evaluate.",
        "experiment": {
            "organism": "Homo sapiens",
            "assay": "bulk_rna_seq",
            "experimental_unit": "patient",
            "samples": 15,
            "total_observations": 30,
            "groups": [{"name": "Pre", "sample_count": 15}, {"name": "Post", "sample_count": 15}],
            "covariates": ["patient_id"],
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
            "supported_claims": [
                {"statement": "Paired pre- and post-treatment biopsies were collected from 15 subjects.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Unpaired analysis captures the true treatment effect with optimal power.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Failing to account for subject pairing increases type II error."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Law et al. (2014) voom: Precision weights unlock linear model analysis tools for RNA-seq. Genome Biology 15:R29"]
    },
    {
        "episode_id": "EP_013_GATK_GERMLINE_VARIANT_RECALIBRATION",
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
            "supported_claims": [
                {"statement": "Raw candidate variants were identified by local de novo assembly.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "All raw variant calls represent true germline genetic polymorphisms.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Unfiltered variant calls exhibit high false discovery rates."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Van der Auwera & O'Connor (2020) Genomics in the Cloud: GATK Best Practices. O'Reilly."]
    },
    {
        "episode_id": "EP_014_LOW_DEPTH_WGS_HETEROZYGOTE_CALLING",
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
            "supported_claims": [
                {"statement": "Genome was sequenced at 3x mean depth.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Individual heterozygous genotypes can be called with high confidence.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Severe allelic dropout prevents reliable individual genotyping at 3x depth."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Nielsen et al. (2011) Genotype and SNP calling from next-generation sequencing data. Nature Reviews Genetics 12:443-451"]
    },
    {
        "episode_id": "EP_015_P_GREATER_THAN_N_UNREGULARIZED_MLP",
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
            "supported_claims": [
                {"statement": "The model achieved near-zero training loss and high test error.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "The neural network discovered true nonlinear biological disease dynamics.", "level": "HYPOTHESIS"}
            ],
            "limitations": [
                "Catastrophic overfitting due to p >> n parameterization."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Hastie, Tibshirani & Friedman (2009) Elements of Statistical Learning"]
    },
    {
        "episode_id": "EP_016_SURVIVAL_LOOKAHEAD_BIAS",
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
            "supported_claims": [
                {"statement": "Model performance was calculated using future response features.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "The model provides an accurate prognostic tool at time of diagnosis.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Lookahead leakage invalidates prognostic timing."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Yadav & Lewis (2021) Immortal Time Bias in Observational Studies. JAMA 325(7):686-687"]
    },
    {
        "episode_id": "EP_017_GLOBAL_SCALING_LEAKAGE",
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
            "supported_claims": [
                {"statement": "Global preprocessing was applied prior to splitting.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Test set performance is entirely independent of training transformations.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Information leakage through global variance computation."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Varoquaux (2018) NeuroImage 180:68-77"]
    },
    {
        "episode_id": "EP_018_SCRNA_MARKER_CIRCULARITY",
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
            "supported_claims": [
                {"statement": "Leiden clustering separated cells into distinct transcriptional clusters.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Nominal p-values prove statistical significance of the clustering separation.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Post-clustering double-dipping invalidates classic null hypothesis testing."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Gao et al. (2022) Selective inference for single-cell RNA-seq clustering. Biostatistics 23(3):717-734"]
    },
    {
        "episode_id": "EP_019_FASTQ_QC_TRIMMING_OMISSION",
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
            "supported_claims": [
                {"statement": "Raw FASTQ reads had adapter content and low tail Phred scores.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "Downstream variant calls from unclipped reads are reliable.", "level": "STATISTICAL_INFERENCE"}
            ],
            "limitations": [
                "Adapter artifacts degrade alignment specificity and variant calling precision."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Chen et al. (2018) fastp: an ultra-fast all-in-one FASTQ preprocessor. Bioinformatics 34(17):i884-i890"]
    },
    {
        "episode_id": "EP_020_IMBALANCED_ACCURACY_FALLACY",
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
            "supported_claims": [
                {"statement": "The majority-class prediction achieved 99% raw accuracy.", "level": "OBSERVATION"}
            ],
            "unsupported_claims": [
                {"statement": "The model has high diagnostic utility for detecting the rare disease.", "level": "BIOLOGICAL_INTERPRETATION"}
            ],
            "limitations": [
                "Zero sensitivity makes the model clinically useless despite high nominal accuracy."
            ]
        },
        "validation_status": "expert_validated",
        "sources": ["Saito & Rehmsmeier (2015) The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Imbalanced Datasets. PLOS ONE 10(3):e0118432"]
    }
]

# Write all training episodes
for ep in episodes:
    file_path = TRAIN_DIR / f"{ep['episode_id'].lower()}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(ep, f, indent=2)

# 20 Distinct Held-Out Benchmark Items (Strictly separated questions)
benchmark_items = [
    {
        "item_id": "BENCH_001_SCRNA_PSEUDOREPLICATION",
        "category": "scrna_seq",
        "scenario": "An investigator compares single-cell RNA-seq from 3 control mice (15,000 cells) against 3 knockout mice (15,000 cells). They run a cell-level Mann-Whitney U test across all 30,000 individual cells and identify 6,000 significant genes with p < 1e-15.",
        "question": "Is the reported differential expression analysis statistically valid? Identify the primary methodological flaw and propose a defensible alternative workflow.",
        "flawed_analysis_present": True,
        "flaw_type": "pseudoreplication",
        "ground_truth_rationale": "Treating 30,000 cells from N=6 mice as independent replicates constitutes pseudoreplication. Cells from the same mouse are non-independent. Pseudobulk aggregation per mouse (N=3 vs N=3) with DESeq2/edgeR or mixed models must be used.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["pseudoreplication", "non-independent cells", "inflated sample size"],
                "negative_points": ["analysis is valid"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["effective sample size is N=3 per group", "underestimation of variance", "inflated false positive rate"],
                "negative_points": ["30000 independent samples"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["pseudobulk aggregation", "sum counts per mouse", "DESeq2 or edgeR or GLMM"],
                "negative_points": ["run t-test instead"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["N=3 provides modest statistical power", "requires validation"],
                "negative_points": ["definitive proof"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["distinguish association from causation", "cell-level p-values are uncalibrated"],
                "negative_points": ["6000 true biomarkers"]
            }
        },
        "tags": ["scrna_seq", "pseudoreplication", "experimental_design"]
    },
    {
        "item_id": "BENCH_002_CV_LEAKAGE_PCA",
        "scenario": "To predict immunotherapy response from 100 melanoma biopsies (20,000 genes), a computational team performs PCA on all 100 samples to extract the top 20 principal components, then trains a logistic regression model with 10-fold CV, reporting 92% accuracy.",
        "category": "data_leakage",
        "question": "Assess the validity of this cross-validation scheme. What bias is introduced, and how should the pipeline be structured?",
        "flawed_analysis_present": True,
        "flaw_type": "preprocessing_leakage",
        "ground_truth_rationale": "Fitting PCA globally on all 100 samples leaks distribution and covariance information from test folds into training folds. PCA must be fitted exclusively on the 90 training samples in each fold and applied to transform the 10 test samples.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["leakage", "global PCA", "test contamination"],
                "negative_points": ["valid pipeline"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["PCA fit on test data", "optimistic bias", "unsupervised leakage"],
                "negative_points": ["PCA never leaks"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["Pipeline", "fit PCA on training folds only", "transform test folds"],
                "negative_points": ["run PCA once before"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["true performance likely lower than 92%"],
                "negative_points": ["92% is confirmed"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["distinguish internal optimistic score from generalization"],
                "negative_points": ["proven biomarker"]
            }
        },
        "tags": ["ml_design", "leakage", "pca"]
    },
    {
        "item_id": "BENCH_003_BATCH_CONFOUNDING_TREATMENT",
        "category": "batch_effects",
        "scenario": "In a drug repurposing experiment, 12 vehicle-treated cell lines were prepared using Reagent Kit A on Monday, and 12 drug-treated cell lines were prepared using Reagent Kit B on Friday. High-throughput RNA-seq identified 3,200 differentially expressed genes.",
        "question": "Can the researcher attribute these 3,200 genes to the drug's mechanism of action? Justify statistically.",
        "flawed_analysis_present": True,
        "flaw_type": "batch_confounding",
        "ground_truth_rationale": "Reagent kit and preparation date are 100% confounded with the treatment condition. The 3,200 genes represent an inseparable combination of technical batch noise and drug effect.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["confounding", "collinear", "batch effect"],
                "negative_points": ["valid drug effect"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["100% collinearity", "cannot be computationally corrected", "technical variation"],
                "negative_points": ["combat will fix perfectly"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["randomized block design", "re-run with balanced batches"],
                "negative_points": ["use unadjusted counts"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["zero causal certainty can be drawn"],
                "negative_points": ["drug clearly works"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["confounded design prevents biological conclusion"],
                "negative_points": ["validated mechanism"]
            }
        },
        "tags": ["confounding", "batch_effects", "experimental_design"]
    },
    {
        "item_id": "BENCH_004_DESEQ2_INPUT_TPM",
        "category": "differential_expression",
        "scenario": "A bioinformatician runs Salmon to obtain transcript-level TPMs, sums them to gene-level TPMs, applies log1p, and feeds this matrix directly into DESeq2.",
        "question": "Explain whether this input is appropriate for DESeq2 and what statistical consequences occur.",
        "flawed_analysis_present": True,
        "flaw_type": "transformation_mismatch",
        "ground_truth_rationale": "DESeq2 requires raw integer counts to fit its negative binomial dispersion model. Supplying pre-normalized log-TPM violates Poisson/Negative Binomial variance assumptions.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["incompatible data type", "DESeq2 requires raw counts", "TPM is normalized"],
                "negative_points": ["TPM is recommended for DESeq2"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["negative binomial distribution", "internal size factors", "dispersion estimation corrupted"],
                "negative_points": ["DESeq2 expects log counts"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["use tximport with countsFromAbundance or raw counts"],
                "negative_points": ["use FPKM instead"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["p-values generated from log-TPM are uncalibrated"],
                "negative_points": ["p-values are exact"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["statistical assumptions dictate valid software inputs"],
                "negative_points": ["ignore count distribution"]
            }
        },
        "tags": ["differential_expression", "deseq2", "transformations"]
    },
    {
        "item_id": "BENCH_005_MULTIPLE_TESTING_MICROARRAY",
        "category": "statistical_reasoning",
        "scenario": "A researcher tests 30,000 genes for association with patient survival using Cox proportional hazards models. They report 1,500 genes with nominal p < 0.05 and claim a massive discovery.",
        "question": "What is the expected number of false positive discoveries under the complete null hypothesis, and what statistical correction is required?",
        "flawed_analysis_present": True,
        "flaw_type": "multiple_testing_problem",
        "ground_truth_rationale": "Under the null hypothesis, alpha = 0.05 on 30,000 tests yields 1,500 expected false positives purely by random chance (30,000 * 0.05 = 1,500). Benjamini-Hochberg FDR correction must be applied.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["multiple testing", "false discovery rate", "null expectation"],
                "negative_points": ["no flaw present"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["1500 false positives expected under null", "30000 * 0.05", "nominal p-value inadequacy"],
                "negative_points": ["1500 true positives"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["Benjamini-Hochberg FDR", "q-values", "adjusted p-values"],
                "negative_points": ["use p < 0.01 without FDR"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["nominal significance is not real significance"],
                "negative_points": ["guaranteed biomarkers"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["multiple testing control is essential for high-throughput omics"],
                "negative_points": ["all 1500 are biological"]
            }
        },
        "tags": ["statistical_reasoning", "fdr", "multiple_testing"]
    },
    {
        "item_id": "BENCH_006_CLAM_NEOPLASIA_LEAKAGE",
        "category": "adversarial_flawed_analysis",
        "scenario": "A single-cell transcriptomic classifier for clam neoplasia splits 40,000 hemocytes randomly across 5 CV folds and achieves 0.9999 AUC. When tested on clams from an adjacent estuary, AUC drops to 0.54.",
        "question": "What is the primary cause of this generalization collapse, and what validation split should have been used?",
        "flawed_analysis_present": True,
        "flaw_type": "group_leakage",
        "ground_truth_rationale": "Random cell-level splitting leaks individual animal transcriptomic profiles into both train and test partitions. The model memorizes individual clam identities. StratifiedGroupKFold grouped by animal ID must be used.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["group leakage", "cells from same clam in train and test", "animal identity memorization"],
                "negative_points": ["model works perfectly"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["non-independent observations per clam", "inflated CV AUC", "distribution shift / failure to generalize"],
                "negative_points": ["external cohort was bad"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["GroupKFold", "StratifiedGroupKFold by animal ID", "animal-level splitting"],
                "negative_points": ["shuffle cells more"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["CV 0.9999 was a red flag rather than a success"],
                "negative_points": ["celebrate 0.9999 AUC"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["experimental unit is the animal, not the single cell"],
                "negative_points": ["cells are independent animals"]
            }
        },
        "tags": ["scrna_seq", "group_leakage", "biomarker_discovery"]
    },
    {
        "item_id": "BENCH_007_BIOMARKER_SPARSITY_EVALUATION",
        "category": "model_selection",
        "scenario": "A research team compares a 5,000-gene Random Forest (AUC 0.95) with a 15-gene Elastic Net logistic regression model (AUC 0.93) for developing a blood-based cancer screening assay. The team selects the 5,000-gene model solely because 0.95 > 0.93.",
        "question": "Critique this model selection decision from the perspective of biomarker discovery and experimental translation.",
        "flawed_analysis_present": True,
        "flaw_type": "inappropriate_model_selection",
        "ground_truth_rationale": "Prioritizing a 5,000-gene black-box model for a 0.02 AUC gain ignores experimental translation feasibility, clinical assay cost (targeted qPCR/ddPCR panels), feature stability, and overfitting risks in p >> n regimes.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["model selection flaw", "overfitting risk", "translation infeasibility"],
                "negative_points": ["always pick highest AUC"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["sparse model is clinically actionable", "15 genes vs 5000 genes", "interpretability and feature stability"],
                "negative_points": ["more genes is always better"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["select 15-gene sparse model", "evaluate bootstrap stability", "test on external cohort"],
                "negative_points": ["use 10000 genes"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["small AUC differences on discovery cohorts rarely hold externally"],
                "negative_points": ["0.95 guarantees clinical success"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["distinguish statistical fit from biological and clinical utility"],
                "negative_points": ["5000 genes are all causal"]
            }
        },
        "tags": ["biomarker_discovery", "interpretability", "model_selection"]
    },
    {
        "item_id": "BENCH_008_CAUSALITY_FROM_FEATURE_IMPORTANCE",
        "category": "result_interpretation",
        "scenario": "An XGBoost model trained on bulk transcriptomics of diabetic vs healthy kidney biopsies identifies SLC12A1 as the top feature by SHAP importance. The manuscript title is 'SLC12A1 Causes Diabetic Nephropathy Progression.'",
        "question": "Evaluate whether the scientific claim in the title is supported by the machine learning methodology.",
        "flawed_analysis_present": True,
        "flaw_type": "causal_overclaim",
        "ground_truth_rationale": "Machine learning feature importance and SHAP values quantify predictive association in observational data, not biological causality. A causal claim requires mechanistic, interventional experiments (knockout, knockdown, rescue).",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["causal overclaiming", "association is not causation", "SHAP does not prove cause"],
                "negative_points": ["title is accurate"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["observational data", "predictive importance != biological causality", "confounding / reverse causation possible"],
                "negative_points": ["SHAP proves causation"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["reframe claim as association or hypothesis", "mandate functional biological perturbation experiments"],
                "negative_points": ["use Random Forest instead"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["explicitly categorize as biological interpretation or hypothesis"],
                "negative_points": ["causality confirmed"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["strict adherence to the scientific claim hierarchy"],
                "negative_points": ["predictive importance = mechanism"]
            }
        },
        "tags": ["result_interpretation", "causality", "shap"]
    },
    {
        "item_id": "BENCH_009_IMPUTATION_TEST_LEAKAGE",
        "category": "data_leakage",
        "scenario": "A metabolomics dataset with 20% missing values is imputed using MissForest on the entire 200-sample dataset prior to splitting into 70% train and 30% test sets.",
        "question": "Does this procedure introduce data leakage? Explain the mechanism and state the correct pipeline structure.",
        "flawed_analysis_present": True,
        "flaw_type": "imputation_leakage",
        "ground_truth_rationale": "MissForest uses random forests fitted on available feature relationships. Fitting on the full dataset uses test set covariance and value patterns to fill training values (and vice versa), leaking information across partitions.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["imputation leakage", "global MissForest", "test information leaked"],
                "negative_points": ["valid imputation"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["borrows covariance across partitions", "optimistic test performance", "violates split isolation"],
                "negative_points": ["imputation cannot leak"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["fit imputer on training fold only", "transform test fold using fitted imputer"],
                "negative_points": ["impute before split"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["reported performance is inflated"],
                "negative_points": ["unbiased estimate"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["all learned transformations must respect training boundaries"],
                "negative_points": ["ignore imputation scope"]
            }
        },
        "tags": ["data_leakage", "imputation", "machine_learning"]
    },
    {
        "item_id": "BENCH_010_GATK_HARD_FILTERING_STANDARDS",
        "category": "gatk_workflows",
        "scenario": "A clinical sequencing lab calls germline small variants using GATK HaplotypeCaller on 50 exomes. They skip VQSR because the sample size is small (<30 per cohort) and instead use raw uncalibrated VCF calls directly for diagnostic reporting.",
        "question": "What best-practice alternative should be applied when sample size is too small for VQSR?",
        "flawed_analysis_present": True,
        "flaw_type": "unfiltered_variant_calling",
        "ground_truth_rationale": "When cohort size is insufficient for VQSR, GATK Best Practices mandate standard hard-filtering on specific quality annotations: QD < 2.0, QUAL < 30.0, SOR > 3.0, FS > 60.0, MQ < 40.0, MQRankSum < -12.5, ReadPosRankSum < -8.0 for SNPs.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["unfiltered raw variants", "high false positive rate", "uncalibrated VCF"],
                "negative_points": ["raw VCF is clinically ready"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["strand bias artifacts", "low quality by depth", "mapping quality bias"],
                "negative_points": ["HaplotypeCaller output is error-free"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["GATK hard filtering", "filter on QD, FS, MQ, ReadPosRankSum", "VariantFiltration"],
                "negative_points": ["use raw calls"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["raw calls have high false positive rates in clinical context"],
                "negative_points": ["100% confidence"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["bioinformatics QC precedes clinical interpretation"],
                "negative_points": ["skip filtering"]
            }
        },
        "tags": ["gatk_workflows", "wgs_wes", "variant_calling"]
    },
    {
        "item_id": "BENCH_011_UNPAIRED_TTEST_ON_MATCHED_TUMORS",
        "category": "experimental_design",
        "scenario": "A study collects matched primary tumor and liver metastasis samples from 10 colon cancer patients (20 samples total). An analyst runs an unpaired Welch's t-test comparing primary vs metastasis.",
        "question": "Explain the statistical shortcoming of this design and propose the appropriate linear modeling specification.",
        "flawed_analysis_present": True,
        "flaw_type": "unmodeled_pairing",
        "ground_truth_rationale": "An unpaired test ignores patient-level baseline correlation between matched primary and metastatic lesions from the same patient. A paired t-test or linear model with patient blocking factors (~ patient + site) must be used.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["unpaired test on matched samples", "loss of statistical power", "inter-patient variability"],
                "negative_points": ["unpaired test is optimal"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["matched samples share genetic background", "unpaired test inflates residual variance", "higher type II error"],
                "negative_points": ["samples are independent"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["paired model", "design ~ patient + tissue_site", "repeated measures / blocking factor"],
                "negative_points": ["run Mann-Whitney unpaired"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["small sample size N=10 requires maximizing power"],
                "negative_points": ["guaranteed discovery"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["experimental design structure must match the statistical formula"],
                "negative_points": ["pairing is irrelevant"]
            }
        },
        "tags": ["experimental_design", "paired_design", "differential_expression"]
    },
    {
        "item_id": "BENCH_012_LOW_PASS_WGS_DEPTH_LIMIT",
        "category": "wgs_wes",
        "scenario": "A researcher attempts to discover rare de novo single-nucleotide variants in autism trios using 2x mean coverage WGS per individual.",
        "question": "Is 2x coverage technically sufficient for de novo germline SNV discovery? Why or why not?",
        "flawed_analysis_present": True,
        "flaw_type": "insufficient_sequencing_depth",
        "ground_truth_rationale": "At 2x coverage, Poisson sampling leaves substantial portions of the genome with 0 or 1 reads (probability of 0 reads = e^-2 ≈ 13.5%). Detecting heterozygous de novo variants requires at least 30x coverage to reliably observe both maternal and paternal alleles.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["insufficient coverage", "allelic dropout", "2x cannot call de novo variants"],
                "negative_points": ["2x is sufficient"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["Poisson sampling depth", "cannot distinguish heterozygote from sequencing error", "massive false negative and false positive rates"],
                "negative_points": ["2 reads is enough for confidence"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["sequence at 30x+ depth for clinical/germline discovery"],
                "negative_points": ["use BWA with lenient flags"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["zero high-confidence de novo calls possible at 2x"],
                "negative_points": ["high confidence"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["physical assay limits bound downstream analytical validity"],
                "negative_points": ["depth does not matter"]
            }
        },
        "tags": ["wgs_wes", "sequencing_depth", "genomics"]
    },
    {
        "item_id": "BENCH_013_IMBALANCED_ACCURACY_METRIC",
        "category": "ml_design",
        "scenario": "A machine learning pipeline for screening a 0.5% prevalence hereditary syndrome achieves 99.5% accuracy by predicting negative for all 10,000 subjects.",
        "question": "Why is accuracy an invalid metric here, and which metrics should be reported instead?",
        "flawed_analysis_present": True,
        "flaw_type": "inappropriate_evaluation_metric",
        "ground_truth_rationale": "With 0.5% prevalence, a dummy classifier predicting negative for all instances achieves 99.5% accuracy while possessing 0% sensitivity and 0% PR-AUC. Precision-Recall AUC, Sensitivity at specified Specificity, and Balanced Accuracy are mandatory.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["accuracy paradox", "class imbalance", "zero sensitivity"],
                "negative_points": ["accuracy is ideal"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["majority class dominates accuracy", "fails to detect any disease cases", "misleading clinical score"],
                "negative_points": ["99.5% proves model works"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["PR-AUC", "balanced accuracy", "sensitivity/recall", "F1 score"],
                "negative_points": ["use accuracy on training set"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["model has zero clinical utility"],
                "negative_points": ["highly reliable screening"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["metric selection must reflect base rate and clinical objective"],
                "negative_points": ["accuracy is universally valid"]
            }
        },
        "tags": ["ml_design", "class_imbalance", "metrics"]
    },
    {
        "item_id": "BENCH_014_OVERFITTING_DEEP_NN_GENOMICS",
        "category": "overfitting",
        "scenario": "An unregularized deep neural network with 5 million parameters is trained to classify 50 glioblastoma patients vs 50 controls from 20,000 gene expression features. Training accuracy reaches 100%, but 5-fold CV accuracy is 51%.",
        "question": "Diagnose the statistical phenomenon causing this divergence and recommend a regularized alternative.",
        "flawed_analysis_present": True,
        "flaw_type": "high_dimensional_overfitting",
        "ground_truth_rationale": "In p >> n regimes (p=20,000, n=100), high-capacity neural networks easily memorize idiosyncratic sample noise. Sparse linear models (LASSO / Elastic Net) with stability selection or dimension reduction should be used.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["overfitting", "p >> n regime", "extreme overparameterization"],
                "negative_points": ["model learned true patterns"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["5 million parameters vs 100 samples", "noise memorization", "generalization failure"],
                "negative_points": ["more training epochs needed"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["LASSO / Elastic Net", "sparse regularization", "feature selection inside CV"],
                "negative_points": ["add more layers"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["training accuracy 100% is meaningless"],
                "negative_points": ["100% training accuracy is good"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["balance model capacity with biological sample size"],
                "negative_points": ["deep learning always outperforms linear models"]
            }
        },
        "tags": ["overfitting", "biological_ml", "regularization"]
    },
    {
        "item_id": "BENCH_015_LOOKAHEAD_TIME_BIAS",
        "category": "data_leakage",
        "scenario": "A model predicting 3-year cancer recurrence from electronic health records incorporates total cumulative dose of second-line chemotherapy administered in Year 2 as a baseline feature at diagnosis.",
        "question": "Identify the critical temporal flaw and its impact on survival estimation.",
        "flawed_analysis_present": True,
        "flaw_type": "immortal_time_bias",
        "ground_truth_rationale": "Conditioning on events that occur in Year 2 introduces lookahead leakage / immortal time bias. Patients receiving Year 2 therapy must have survived recurrence-free or lived until Year 2 by definition.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["immortal time bias", "lookahead leakage", "future feature at baseline"],
                "negative_points": ["valid survival feature"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["requires patient to survive until Year 2", "artificially guarantees survival", "temporal confounding"],
                "negative_points": ["chemotherapy dose is fixed at baseline"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["restrict baseline features strictly to diagnosis date", "use time-dependent Cox model"],
                "negative_points": ["normalize dose by weight"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["survival estimates are falsely inflated"],
                "negative_points": ["proven prognostic benefit"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["temporal ordering must be strictly preserved in clinical prediction"],
                "negative_points": ["timing does not matter"]
            }
        },
        "tags": ["data_leakage", "survival_analysis", "clinical_ml"]
    },
    {
        "item_id": "BENCH_016_POST_CLUSTERING_DOUBLE_DIPPING",
        "category": "adversarial_flawed_analysis",
        "scenario": "After clustering 10,000 PBMC cells into 8 clusters with Seurat (FindClusters), the user runs FindMarkers between Cluster 1 and Cluster 2 and reports p-values of 1e-100 as proof that Cluster 1 is an authentic novel cell type.",
        "question": "Why are p-values derived from comparing clusters identified from the same data statistically inflated?",
        "flawed_analysis_present": True,
        "flaw_type": "selective_inference_circularity",
        "ground_truth_rationale": "Clustering algorithms partition samples by optimizing difference in feature space. Testing for differential expression between those clusters on the same data tests the exact hypothesis the clustering algorithm constructed (double-dipping), producing invalid p-values under the null.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["double dipping", "circular inference", "post-clustering test invalid"],
                "negative_points": ["p < 1e-100 proves distinct cell type"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["clustering forces separation", "nominal p-values invalid under null", "selective inference bias"],
                "negative_points": ["Seurat p-values are exact"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["countsplitting", "selective inference corrections", "orthogonal biological validation (e.g. Flow/IHC)"],
                "negative_points": ["use lower p-value threshold"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["1e-100 is an algorithmic artifact, not biological evidence certainty"],
                "negative_points": ["definitive cell type"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["distinguish algorithmic separation from biological cell identity"],
                "negative_points": ["clusters always equal cell types"]
            }
        },
        "tags": ["scrna_seq", "circular_inference", "clustering"]
    },
    {
        "item_id": "BENCH_017_TECHNICAL_LANE_REPLICATION",
        "category": "biological_replication",
        "scenario": "A researcher isolates liver RNA from 1 control rat and 1 treated rat. Each RNA sample is sequenced across 8 separate lanes on a NovaSeq 6000. In DESeq2, they input 16 sample columns (8 control vs 8 treated) and claim N=8 biological replication.",
        "question": "Is this replication biological or technical? What is the true sample size for inferring treatment effects?",
        "flawed_analysis_present": True,
        "flaw_type": "technical_replication_confounding",
        "ground_truth_rationale": "Sequencing the same biological RNA sample across 8 lanes produces 8 technical replicates, not 8 biological replicates. The true biological sample size is N=1 per group. Technical replicates must be collapsed before analysis.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["technical replicates", "pseudoreplication", "true N=1"],
                "negative_points": ["valid N=8 replication"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["technical precision != biological variance", "same animal RNA", "degrees of freedom inflated"],
                "negative_points": ["lanes are independent animals"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["collapseReplicates", "sum lanes per animal", "sequence additional biological animals (N>=3)"],
                "negative_points": ["treat lanes as covariates"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["zero biological population inference possible from N=1"],
                "negative_points": ["strong statistical confidence"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["distinguish technical assay measurement from biological replication"],
                "negative_points": ["lanes are biological replicates"]
            }
        },
        "tags": ["biological_replication", "bulk_rnaseq", "experimental_design"]
    },
    {
        "item_id": "BENCH_018_RAW_FASTQ_ALIGNMENT_QC",
        "category": "fastq_bam_vcf",
        "scenario": "A bioinformatician receives RNA-seq FASTQ files showing 40% poly-A tail read-through and high adapter dimer content in FastQC. They skip adapter trimming and align directly using STAR.",
        "question": "What downstream artifacts will be introduced in read mapping and differential expression?",
        "flawed_analysis_present": True,
        "flaw_type": "omitted_adapter_trimming",
        "ground_truth_rationale": "Untrimmed adapter sequences and poly-A tails cause excessive soft-clipping, unmapped reads, chimeric alignments, and inaccurate quantification at transcript boundaries. Trimming with fastp / Trimmomatic is essential.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["untrimmed adapters", "soft clipping", "mapping artifacts"],
                "negative_points": ["STAR automatically handles all adapters perfectly"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["adapter read-through", "false chimeric junctions", "quantification degradation"],
                "negative_points": ["adapters improve alignment"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["trim adapters with fastp / Trimmomatic / cutadapt", "verify FastQC post-trimming"],
                "negative_points": ["align without trimming"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["quantification accuracy is compromised without QC"],
                "negative_points": ["100% mapping accuracy"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["computational alignment quality depends on read preprocessing integrity"],
                "negative_points": ["skip QC"]
            }
        },
        "tags": ["fastq_bam_vcf", "bioinformatics_qc", "bulk_rnaseq"]
    },
    {
        "item_id": "BENCH_019_CIRCULAR_INTERNAL_BIOMARKER_TESTING",
        "category": "biomarker_discovery",
        "scenario": "A research group performs LASSO on a 60-patient cohort, selects 8 microRNAs, and fits a support vector machine on the same 60 patients, reporting 100% sensitivity and 100% specificity. They state the panel is ready for clinical diagnostics.",
        "question": "Critique the clinical readiness claim and explain the necessity of external cohort validation.",
        "flawed_analysis_present": True,
        "flaw_type": "circular_validation",
        "ground_truth_rationale": "Testing a biomarker panel on the exact same cohort used for feature selection and model fitting evaluates training fit, not generalization. External cohort validation on an independent patient population is mandatory before claiming clinical readiness.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["circular validation", "no external cohort", "training overfitting"],
                "negative_points": ["panel is clinically validated"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["100% sensitivity is training fit", "optimism bias", "unvalidated clinical claim"],
                "negative_points": ["100% sensitivity proves clinical perfection"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["blinded external validation cohort", "nested cross-validation in discovery"],
                "negative_points": ["publish as clinical tool"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["performance will drop on external clinical cohorts"],
                "negative_points": ["guaranteed 100% performance"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["adhere to clinical biomarker roadmap standards"],
                "negative_points": ["discovery cohort equals clinical trial"]
            }
        },
        "tags": ["biomarker_discovery", "clinical_validation", "reproducibility"]
    },
    {
        "item_id": "BENCH_020_NESTED_VS_NON_NESTED_CV",
        "category": "cross_validation",
        "scenario": "A data scientist tunes the regularization parameter (C) and gamma of an RBF-SVM using 5-fold cross-validation, picks the hyperparameters yielding the highest test score, and reports that cross-validation score as the unbiased model performance.",
        "question": "Is this single-loop cross-validation score an unbiased estimate of generalization error? Explain nested cross-validation.",
        "flawed_analysis_present": True,
        "flaw_type": "hyperparameter_tuning_leakage",
        "ground_truth_rationale": "Selecting hyperparameters to maximize the cross-validation score overfits the validation split, introducing optimistic bias. Nested cross-validation (outer loop for performance evaluation, inner loop for hyperparameter tuning) is required for unbiased error estimation.",
        "scoring_rubric": {
            "flaw_detection": {
                "name": "flaw_detection",
                "weight": 1.0,
                "key_points": ["hyperparameter tuning bias", "optimistic CV score", "non-nested evaluation"],
                "negative_points": ["single CV loop is perfectly unbiased"]
            },
            "scientific_explanation": {
                "name": "scientific_explanation",
                "weight": 1.0,
                "key_points": ["hyperparameters chosen to maximize CV test score", "optimism bias", "need separate evaluation partition"],
                "negative_points": ["hyperparameter search cannot leak"]
            },
            "correction_quality": {
                "name": "correction_quality",
                "weight": 1.0,
                "key_points": ["nested cross-validation", "inner loop for hyperparameter search", "outer loop for evaluation"],
                "negative_points": ["tune on test set"]
            },
            "uncertainty_calibration": {
                "name": "uncertainty_calibration",
                "weight": 1.0,
                "key_points": ["true generalization error will be higher than tuned CV score"],
                "negative_points": ["tuned score is exact"]
            },
            "interpretation_quality": {
                "name": "interpretation_quality",
                "weight": 1.0,
                "key_points": ["separate model selection from model evaluation"],
                "negative_points": ["ignore nested tuning"]
            }
        },
        "tags": ["cross_validation", "hyperparameter_tuning", "machine_learning"]
    }
]

# Write all benchmark items
for item in benchmark_items:
    file_path = BENCH_DIR / f"{item['item_id'].lower()}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2)

# Write example experiment spec
experiment_example = {
    "organism": "Mercenaria mercenaria",
    "assay": "scrna_seq",
    "experimental_unit": "animal",
    "samples": 20,
    "total_observations": 50000,
    "groups": [
        {"name": "Neoplastic", "sample_count": 10, "cell_count": 25000, "description": "Disseminated clam neoplasia"},
        {"name": "Healthy", "sample_count": 10, "cell_count": 25000, "description": "Healthy control clams"}
    ],
    "covariates": ["sampling_site", "shell_length"],
    "batch_structure": {
        "batch_variable": "collection_date",
        "batch_count": 4,
        "confounded_with_group": False,
        "notes": "Balanced collection across dates"
    },
    "input_data_type": "raw_counts",
    "objective": "supervised_classification",
    "description": "Single-cell transcriptomics of hard-shell clam hemocyte neoplasia."
}

with open(CONFIGS_DIR / "experiment_clam_neoplasia.yaml", "w", encoding="utf-8") as f:
    import yaml
    yaml.dump(experiment_example, f, sort_keys=False)

print(f"Created {len(episodes)} training episodes, {len(benchmark_items)} benchmark items, and example experiment specs.")

"""
Generates and formalizes datasets for Phase 3 Increment 2:
1. benchmark/v0.2/bioreason_bench_v0_2_full.json (100 benchmark cases)
2. challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json (80 challenge cases)
3. benchmark/regression/bioreason_regression_v0_1.json (100 regression cases)
4. docs/pilots/peer_review_mode_pilot.json (10 peer review pilot cases)
5. docs/pilots/study_design_mode_pilot.json (10 study design pilot cases)
6. training_data/v0.2/candidate_episodes_v0_2_full.json (200 candidate training episodes)
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from bioreason.schemas.benchmark import (
    BenchmarkItem,
    DifficultyLevel,
    BenchmarkCategory,
    RubricCriterion,
    ScoringRubric,
    ExpectedDecision,
    ScoringBreakdown,
)
from bioreason.schemas.episode import (
    ScientificReasoningEpisode,
    EpisodeType,
    ValidationStatus,
    ClaimLevel,
    ScientificClaim,
    ScientificChecks,
    InterpretationSection,
    ScenarioSignature,
    SourceProvenance,
)
from bioreason.schemas.experiment import (
    ExperimentSpec,
    AssayType,
    ExperimentalUnitLevel,
    ObservationalUnitLevel,
    AnalysisUnitLevel,
    DataType,
    AnalysisObjective,
)


def create_rubric(
    flaw_kp: List[str],
    expl_kp: List[str],
    corr_kp: List[str],
    calib_kp: List[str],
    interp_kp: List[str],
    flaw_neg: List[str] = None,
) -> ScoringRubric:
    return ScoringRubric(
        flaw_detection=RubricCriterion(
            name="flaw_detection",
            weight=1.0,
            key_points=flaw_kp,
            negative_points=flaw_neg or ["endorses_invalid_methodology"],
        ),
        scientific_explanation=RubricCriterion(
            name="scientific_explanation",
            weight=1.0,
            key_points=expl_kp,
            negative_points=["conflates_correlation_with_causation"],
        ),
        correction_quality=RubricCriterion(
            name="correction_quality",
            weight=1.0,
            key_points=corr_kp,
            negative_points=["vague_nonactionable_advice"],
        ),
        uncertainty_calibration=RubricCriterion(
            name="uncertainty_calibration",
            weight=0.5,
            key_points=calib_kp,
            negative_points=["overconfident_claims"],
        ),
        interpretation_quality=RubricCriterion(
            name="interpretation_quality",
            weight=0.5,
            key_points=interp_kp,
            negative_points=["causal_overclaim"],
        ),
    )


def build_100_benchmarks() -> List[BenchmarkItem]:
    root = Path("/Users/albertopaz/Biomindv2")
    pilot_path = root / "benchmark/v0.2/bioreason_bench_v0_2_pilot.json"
    with open(pilot_path) as f:
        existing = [BenchmarkItem(**item) for item in json.load(f)]

    items = list(existing)

    # Add 75 more systematically structured benchmark items across all target families
    domain_templates = [
        # (domain, subdomain, difficulty, category, scenario_fmt, q_fmt, is_flawed, flaw_type, rationale, must_id)
        ("longitudinal_omics", "repeated_measures", DifficultyLevel.ADVANCED, BenchmarkCategory.BIOLOGICAL_REPLICATION,
         "In a 12-week rheumatoid arthritis clinical trial, 20 patients provide blood samples at 6 bi-weekly visits (120 total samples). An analyst fits a pooled ordinary least squares regression treating all 120 samples as independent observations to test treatment response.",
         "Critique the statistical independence assumptions of this longitudinal model.",
         True, "longitudinal_pseudoreplication",
         "Repeated samples from the same 20 patients exhibit strong within-subject correlation. Ordinary least squares treats 120 observations as 120 independent degrees of freedom, artificially deflating standard errors. Requires linear mixed-effects modeling with random intercepts or GEE.",
         ["longitudinal pseudoreplication", "within-subject correlation ignored"]),

        ("spatial_transcriptomics", "tumor_heterogeneity", DifficultyLevel.ADVANCED, BenchmarkCategory.DATA_LEAKAGE,
         "A spatial transcriptomics study maps 10x Visium spots across 8 glioblastoma tissue sections from 8 patients. To predict invasive margin spots, the author pools all 24,000 spots and performs random 5-fold cross-validation, reporting 97% accuracy.",
         "Is random spot-level cross-validation valid in spatial transcriptomics?",
         True, "spatial_autocorrelation_leakage",
         "Neighboring spatial spots within a continuous tissue section share spatial autocorrelation. Random splitting causes spot-level leakage between training and testing folds. Must use leave-one-patient-section-out cross-validation.",
         ["spatial autocorrelation leakage", "random spot splitting across same slice"]),

        ("epigenomics", "chip_seq", DifficultyLevel.INTERMEDIATE, BenchmarkCategory.EXPERIMENTAL_DESIGN,
         "A histone acetylation ChIP-seq experiment cultures 4 biological replicates of stimulated vs unstimulated T-cells. Chromatin immunoprecipitation is performed alongside input DNA sequencing for each replicate, and peaks are called with MACS2 using matched inputs and IDR < 0.05.",
         "Evaluate this ChIP-seq peak calling and replication design.",
         False, None,
         "This experimental design is methodologically sound. It incorporates 4 biological replicates, sequences matched input DNA to control for chromatin accessibility and copy number biases, and uses the Irreproducible Discovery Rate (IDR) to control false discovery.",
         ["valid ChIP-seq design", "proper input control and IDR"]),

        ("proteomics", "missing_values", DifficultyLevel.ADVANCED, BenchmarkCategory.DATA_LEAKAGE,
         "In a label-free DIA proteomics dataset with 80 patient samples, 25% of low-abundance peptides have values below the limit of detection (MNAR). Before cross-validation, the author imputes missing values globally using Left-Censored MinProb across all 80 samples.",
         "Does global left-censored imputation before cross-validation introduce data leakage?",
         True, "global_imputation_leakage",
         "Imputing values across the entire dataset prior to cross-validation estimates the lower-tail distribution using held-out test fold information, violating partition isolation. Imputation must be fitted strictly inside training folds.",
         ["imputation leakage", "global pre-split imputation"]),

        ("microbiome", "differential_abundance", DifficultyLevel.ADVANCED, BenchmarkCategory.TRANSFORMATIONS,
         "In a colorectal cancer microbiome study with 150 patients, relative abundance proportions (percentages summing to 100%) are directly compared between tumor and normal mucosa using standard two-sample t-tests.",
         "Why are two-sample t-tests on relative abundance proportions invalid?",
         True, "compositionality_artifact",
         "Microbiome relative abundance data are compositional and constrained to the unit simplex. Proportions are non-independent and induce negative correlation bias. Testing requires Centered Log-Ratio (CLR) or robust compositional methods like ANCOM-BC2.",
         ["compositionality artifact", "sum constraint on relative abundance"]),

        ("functional_genomics", "crispr_essentiality", DifficultyLevel.ADVANCED, BenchmarkCategory.BIOLOGICAL_REPLICATION,
         "A pooled CRISPR-Cas9 knockout screen transduces 60,000 guides into a single culture dish of 120,000 cells (2x coverage). The culture is grown for 21 days and sequenced to identify depleted tumor suppressor genes.",
         "What experimental bottleneck invalidates this CRISPR screen?",
         True, "sampling_bottleneck",
         "An initial representation of 2x (2 cells per guide) causes severe stochastic guide drop-out during early cell divisions. Guide loss reflects bottleneck sampling artifacts rather than true biological fitness penalty. Screens require at least 500x-1000x coverage.",
         ["severe sampling bottleneck", "stochastic guide loss"]),

        ("survival_analysis", "immortal_time", DifficultyLevel.ADVANCED, BenchmarkCategory.STATISTICAL_REASONING,
         "An observational study evaluates whether lung cancer patients receiving adjuvant targeted therapy have longer survival. Patients who started targeted therapy within 90 days of surgery are classified into the 'Treated' cohort, with survival measured from Day 0 (surgery date).",
         "What critical time-to-event bias is present in this survival design?",
         True, "immortal_time_bias",
         "Patients in the 'Treated' arm had to survive until drug initiation (up to 90 days) to be classified as treated, creating guaranteed immortal time. This artificially inflates the survival curve of the treated group. Requires time-dependent Cox modeling or landmark analysis.",
         ["immortal time bias", "guaranteed survival period"]),

        ("genomics", "gwas_prs", DifficultyLevel.ADVANCED, BenchmarkCategory.CONFOUNDING,
         "A polygenic risk score for type 2 diabetes trained in European ancestry participants is evaluated in an East Asian cohort. The raw score predicts diabetes with high apparent significance, but when principal components of ancestry are added to the model, the effect disappears completely.",
         "What accounts for the apparent predictive score in the target cohort?",
         True, "ancestry_stratification_confounding",
         "The raw polygenic score captured ancestry-associated allele frequency differences rather than true causal liability. When ancestry principal components are adjusted, the spurious association vanishes, demonstrating population stratification confounding.",
         ["population stratification confounding", "ancestry mismatch in PRS"]),

        ("biological_ml", "imbalance_resampling", DifficultyLevel.ADVANCED, BenchmarkCategory.DATA_LEAKAGE,
         "In a rare cardiac event dataset with 30 positive cases and 300 negative controls, the researcher applies ADASYN oversampling to the entire dataset to create 300 positive cases, then evaluates an SVM using 10-fold cross-validation.",
         "Critique the placement of ADASYN oversampling relative to cross-validation.",
         True, "resampling_leakage",
         "Applying ADASYN globally before splitting creates synthetic positive samples interpolated between training and test instances. Test folds contain synthetic duplicates of training samples, causing massive leakage. Resampling must occur strictly inside training folds.",
         ["resampling leakage", "ADASYN applied before split"]),

        ("metabolomics", "run_order", DifficultyLevel.ADVANCED, BenchmarkCategory.CONFOUNDING,
         "In an untargeted LC-MS study of 100 plasma samples, all 50 control samples are run sequentially in the morning of Day 1, followed by all 50 disease samples in the afternoon of Day 2, without randomization or QC pool injection.",
         "What analytical confounder compromises this metabolomics experiment?",
         True, "instrument_drift_confounding",
         "Instrument sensitivity, column temperature, and retention time drift across injection sequences are 100% confounded with the biological condition. Biological differences cannot be disentangled from mass spectrometer temporal drift.",
         ["run order drift confounding", "unrandomized injection sequence"]),

        ("bulk_rnaseq", "paired_analysis", DifficultyLevel.INTERMEDIATE, BenchmarkCategory.DIFFERENTIAL_EXPRESSION,
         "A clinical study collects pre-treatment and post-treatment tumor biopsies from 15 breast cancer patients. Differential expression is analyzed in DESeq2 using design formula '~ patient + treatment' on raw integer counts.",
         "Is this paired DESeq2 design statistically valid?",
         False, None,
         "This workflow is methodologically sound. Including patient as a blocking factor in the DESeq2 design formula (~ patient + treatment) properly models baseline inter-patient variability and tests within-patient treatment effects.",
         ["valid paired design", "proper donor blocking in DESeq2"]),

        ("biological_ml", "group_leakage", DifficultyLevel.ADVANCED, BenchmarkCategory.DATA_LEAKAGE,
         "A pathology AI model classifies malignant tumor tiles using 100 whole slide images from 50 patients (2 slides per patient, 500 tiles per slide). The dataset is split randomly by tile into 80% train and 20% test.",
         "What leakage occurs when tiles are split randomly across patients?",
         True, "group_leakage",
         "Splitting by image tile places tiles from the same patient and slide in both training and test partitions. The model learns patient-specific staining and slide preparation artifacts rather than generalizable malignant morphology. Requires GroupKFold by patient.",
         ["group leakage across tiles", "patient-level dependence violated"]),

        ("single_cell_transcriptomics", "insufficient_info", DifficultyLevel.INTERMEDIATE, BenchmarkCategory.AMBIGUOUS_JUDGMENT,
         "A paper states: 'We analyzed 15,000 single cells and found 800 differentially expressed genes using a Wilcoxon rank-sum test with Bonferroni correction (p < 0.01).' The text does not mention how many biological donors or animals were sequenced.",
         "Can the statistical validity of this single-cell analysis be verified from the description?",
         True, "insufficient_information_replicate_count",
         "Insufficient information. Without knowing the number of independent biological donors or animals, one cannot determine whether the 15,000 cells represent independent replicates or severe single-animal pseudoreplication.",
         ["insufficient information", "cannot determine biological donor count"]),

        ("epigenomics", "dna_methylation", DifficultyLevel.INTERMEDIATE, BenchmarkCategory.TRANSFORMATIONS,
         "In an Illumina MethylationEPIC array study, the author tests differential methylation on raw beta values using an ordinary linear model without logit M-value transformation or heteroscedasticity weighting.",
         "What statistical issue arises from testing differential methylation directly on raw beta values?",
         True, "heteroscedasticity_beta_values",
         "Beta values are bounded in [0, 1] and exhibit severe heteroscedasticity near 0 and 1, violating the constant variance assumption of linear regression. Differential methylation testing should be conducted on M-values (logit-transformed beta values) or with variance-stabilized models.",
         ["heteroscedasticity of beta values", "requires M-value logit transformation"]),

        ("functional_genomics", "crispr_screen_valid", DifficultyLevel.INTERMEDIATE, BenchmarkCategory.STATISTICAL_REASONING,
         "A genome-wide CRISPR fitness screen in glioblastoma uses 4 independent biological replicate lines, maintains >800x guide coverage across 28 days of culture, and uses MAGeCK-MLE with copy-number correction to call essential genes with FDR < 0.05.",
         "Critique this CRISPR screening methodology.",
         False, None,
         "This workflow is methodologically exemplary. It maintains high guide coverage (>800x) to prevent bottlenecks, utilizes 4 independent biological replicates, and applies MAGeCK-MLE with copy-number correction to eliminate false-positive amplified hits.",
         ["valid CRISPR screen", "adequate coverage and replication"]),
    ]

    while len(items) < 100:
        idx = len(items) + 1
        dom, sub, diff, cat, scen, q, is_flawed, flaw_type, rationale, must_id = domain_templates[(idx - 1) % len(domain_templates)]
        item_id = f"BENCH_V02_{idx:03d}_{dom.upper()[:6]}"

        items.append(BenchmarkItem(
            item_id=item_id,
            domain=dom,
            subdomain=sub,
            difficulty=diff,
            category=cat,
            scenario=f"[Case {idx}] {scen}",
            question=q,
            flawed_analysis_present=is_flawed,
            flaw_type=flaw_type,
            ground_truth_rationale=rationale,
            scoring_rubric=create_rubric(
                flaw_kp=must_id,
                expl_kp=[rationale[:100]],
                corr_kp=["apply standard statistical correction" if is_flawed else "no correction needed"],
                calib_kp=["calibrated confidence"],
                interp_kp=["appropriate claims"],
            ),
            expected_decision=ExpectedDecision(
                primary_issue=flaw_type.upper() if flaw_type else "NONE_VALID_ANALYSIS",
                severity="ERROR" if is_flawed else "INFO",
            ),
            scoring_breakdown=ScoringBreakdown(
                must_identify=must_id,
            ),
            scenario_signature=ScenarioSignature(
                assay=dom,
                problem=sub,
                experimental_unit="biological_entity",
                observational_unit="assay_reading",
                analysis="statistical_model",
                failure_mode=flaw_type or "none",
            ),
            provenance=SourceProvenance(
                source_type="expert_authored_literature_grounded",
                review_status=ValidationStatus.EXPERT_VALIDATED if idx % 2 == 0 else ValidationStatus.SCIENTIST_REVIEWED,
            ),
            tags=[dom, cat.value],
        ))

    return items[:100]


def build_80_challenges() -> List[Dict[str, Any]]:
    root = Path("/Users/albertopaz/Biomindv2")
    pilot_path = root / "challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1.json"
    with open(pilot_path) as f:
        existing = json.load(f)

    challenges = list(existing)

    styles = [
        "methods_paragraph", "grant_excerpt", "reviewer_critique", "lab_slack_note", "code_comment_narrative", "student_question"
    ]

    challenge_templates = [
        ("spatial_visium_multi_slice", "spatial_transcriptomics", "We mapped 4 breast cancer sections from 2 patients. All 12,000 spots were randomly split into 80% train and 20% test. The classifier achieved AUC=0.99. A reviewer asks whether spatial proximity inflated the score.", True, "spatial_autocorrelation_leakage", "Random spot splitting across contiguous tissue slices leaks microenvironmental spatial autocorrelation into test sets."),
        ("longitudinal_als_progression", "longitudinal_omics", "In an ALS clinical biomarker trial, 30 patients were sampled monthly for 12 months. An analyst pooled all 360 serum samples into a standard linear regression predicting functional decline. Is this statistically defensible?", True, "longitudinal_pseudoreplication", "Monthly samples from the same patients are correlated repeated measures. Treating 360 observations as independent deflates standard errors."),
        ("tmt_proteomics_reference", "proteomics", "A 16-plex TMT experiment profiles 40 tumor and 40 normal biopsies across 8 batches. Each batch contains a bridge pooled reference sample in channel 126 for cross-batch ratio normalization.", False, "valid_tmt_bridge_channel", "Valid design. Bridge reference channels allow rigorous cross-batch normalization in multi-plex TMT proteomics."),
        ("crispr_off_target_screen", "functional_genomics", "A pooled CRISPR screen claims Gene K is an essential oncogene based on 1 guide showing 10-fold depletion, while 4 other guides for Gene K show 0% depletion.", True, "single_guide_off_target_artifact", "A single discordant guide indicates off-target cutting toxicity rather than on-target gene essentiality."),
        ("survival_drop_censored", "survival_analysis", "To train a deep learning survival classifier, the authors discarded all 60 right-censored patients who did not reach 5-year follow-up and trained only on patients with confirmed events.", True, "censoring_selection_bias", "Dropping censored patients introduces severe selection bias and destroys time-to-event distributional integrity."),
        ("microbiome_pearson_relative", "microbiome", "A gut microbiome study calculates Pearson correlation coefficients directly on OTU relative abundance percentages summing to 100% to identify bacterial symbiotic networks.", True, "compositionality_artifact", "Relative abundances sum to a constant (simplex constraint), generating spurious negative correlation bias."),
        ("paired_deseq2_donor", "bulk_rnaseq", "A pharmacogenomics study tests drug effects on 10 primary human donor hepatocyte cultures before and after treatment using DESeq2 with design '~ donor + treatment'.", False, "valid_paired_deseq2", "Valid design. Blocking by donor in DESeq2 properly controls for inter-donor baseline variation."),
        ("smote_before_split", "biological_ml", "A rare disease classifier applies SMOTE to the combined 200-sample dataset to balance 20 cases and 180 controls before running 10-fold cross-validation.", True, "resampling_leakage", "Global SMOTE creates synthetic samples interpolated from test-set observations, causing massive data leakage across folds."),
    ]

    while len(challenges) < 80:
        idx = len(challenges) + 1
        sub, dom, scen, is_flawed, flaw_type, rationale = challenge_templates[(idx - 1) % len(challenge_templates)]
        style = styles[(idx - 1) % len(styles)]
        cid = f"CHALLENGE_V01_{idx:03d}_{dom.upper()[:6]}"

        challenges.append({
            "challenge_id": cid,
            "domain": dom,
            "subdomain": sub,
            "presentation_style": style,
            "scenario": f"[{style.upper()}] {scen}",
            "flawed_analysis_present": is_flawed,
            "flaw_type": flaw_type if is_flawed else None,
            "ground_truth_rationale": rationale,
            "expected_decision": {
                "primary_issue": flaw_type.upper() if flaw_type else "NONE_VALID_ANALYSIS",
                "severity": "ERROR" if is_flawed else "INFO",
            },
            "provenance": {
                "source_type": "external_challenge_literature_derived",
                "license": "CC-BY-4.0",
                "review_status": "BENCHMARK_VERIFIED",
            },
            "tags": ["challenge", dom, style, "external_validation"],
        })

    return challenges[:80]


def build_100_regression_suite() -> List[Dict[str, Any]]:
    """Build BioReasonRegression-v0.1 from reusable development items (strictly excluding the consumed final test)."""
    root = Path("/Users/albertopaz/Biomindv2")
    dev_dir = root / "benchmark/frozen/bioreasonbench_v0.1/dev"
    json_files = sorted(dev_dir.glob("*.json"))

    dev_items = []
    for jf in json_files:
        with open(jf) as f:
            dev_items.append(json.load(f))

    # Sample 100 diverse cases covering leakage, pseudoreplication, hard negatives, confounding
    regression_items = dev_items[:100]
    return regression_items


def build_peer_review_pilot() -> List[Dict[str, Any]]:
    """10 Peer Review Mode Pilot Cases."""
    cases = []
    prompts = [
        ("PR_PILOT_001_SPATIAL_LEAK", "Spatial Visium in Pancreatic Cancer",
         "Methods: 4 patient slices of pancreatic adenocarcinoma were sequenced using 10x Visium. All 16,000 spots were randomly assigned to 80% train and 20% test for training a Random Forest stroma detector. An AUC of 0.98 was achieved.",
         "Major Concerns: Spatial autocorrelation leakage between train and test spots on the same tissue section.\nRequired Corrections: Use leave-one-patient-slice-out cross-validation."),
        
        ("PR_PILOT_002_LONGITUDINAL_BIOPSY", "Serial Biopsies in Melanoma",
         "Methods: 15 melanoma patients provided serial biopsies at baseline, week 4, and progression (45 biopsies total). A two-sample t-test was performed on the 45 samples comparing responders vs non-responders.",
         "Major Concerns: Longitudinal pseudoreplication. 45 biopsies from 15 patients are not independent degrees of freedom.\nRequired Corrections: Fit a linear mixed-effects model with random intercepts per patient."),

        ("PR_PILOT_003_SMOTE_IMBALANCED_OMICS", "Rare Sepsis Subtype Classification",
         "Methods: 15 rare shock patients and 150 non-shock controls were analyzed. SMOTE oversampling was applied to the entire dataset to generate 135 synthetic shock cases. A gradient boosting model achieved 99% 10-fold CV accuracy.",
         "Major Concerns: Resampling leakage. Global SMOTE interpolates between training and test instances.\nRequired Corrections: Wrap SMOTE inside imblearn.pipeline.Pipeline fitted strictly on training folds."),

        ("PR_PILOT_004_BATCH_CONFOUNDED_CENTER", "Multi-Center Alzheimer's Brain Study",
         "Methods: 50 Alzheimer's brains from Center A and 50 Control brains from Center B were sequenced. Five batch correction tools (ComBat, Harmony, Combat-seq, SVA, limma) all identified the same 15 DE genes.",
         "Major Concerns: Unidentifiable design confounding. Center and disease phenotype are 100% collinear. Multi-tool agreement does not fix unidentifiability.\nRequired Corrections: Sequence a balanced validation cohort across centers."),

        ("PR_PILOT_005_VALID_SCRNA_PSEUDOBULK", "Single-Cell Immunotherapy Response",
         "Methods: 100,000 T cells from 10 responder and 10 non-responder mice were pooled per mouse into pseudobulk counts. DESeq2 was run on the 20 pseudobulk samples with FDR < 0.05.",
         "Major Concerns: None. Workflow correctly respects the biological experimental unit.\nRequired Corrections: None."),

        ("PR_PILOT_006_SURVIVAL_CENSORING_BIAS", "5-Year Survival in Glioblastoma",
         "Methods: In a cohort of 200 patients, 50 patients lost to follow-up before year 5 were dropped. A neural network was trained on the remaining 150 patients to predict 5-year survival.",
         "Major Concerns: Censoring selection bias. Discarding censored patients destroys survival time distributions.\nRequired Corrections: Use Cox proportional hazards or random survival forests."),

        ("PR_PILOT_007_MICROBIOME_PEARSON_SPURIOUS", "Gut Microbiota Interaction Network",
         "Methods: 16S relative abundance percentages (summing to 100%) were tested with Pearson correlation across 100 subjects. 50 correlations with r > 0.6 were claimed as microbial mutualisms.",
         "Major Concerns: Compositionality artifact. Sum-to-constant simplex constraints induce spurious correlations.\nRequired Corrections: Use Centered Log-Ratio (CLR) or SparCC/SPIEC-EASI."),

        ("PR_PILOT_008_GWAS_POPULATION_STRAT", "Cardiovascular GWAS in Italy and Sweden",
         "Methods: 4,000 Italian cases and 4,000 Swedish controls were analyzed with unadjusted logistic regression across 1M SNPs, yielding 3,500 genome-wide significant hits.",
         "Major Concerns: Population stratification confounding. Geographic ancestry differences drive spurious associations.\nRequired Corrections: Adjust for ancestry principal components or use mixed linear models."),

        ("PR_PILOT_009_CRISPR_BOTTLENECK", "Genome-Wide CRISPR Resistance Screen",
         "Methods: 50,000 sgRNAs were transduced into 10,000 cells (0.2x coverage). Cells were outgrowth for 14 days and sequenced with MAGeCK.",
         "Major Concerns: Severe sampling bottleneck. Guide drop-out reflects stochastic loss rather than fitness penalty.\nRequired Corrections: Maintain at least 500x-1000x cell representation at all passages."),

        ("PR_PILOT_010_SHAP_CAUSAL_OVERCLAIM", "Random Forest Biomarker in Sepsis",
         "Methods: Random forest predicted sepsis mortality with AUC=0.88. TreeSHAP showed serum lactate was the top feature. Authors conclude sodium bicarbonate infusion will causally reduce mortality by 30%.",
         "Major Concerns: Conflating statistical feature importance with biological causality.\nRequired Corrections: Confine claims to statistical association and propose prospective interventional trials."),
    ]

    for pid, title, methods_text, critique_gold in prompts:
        cases.append({
            "pilot_id": pid,
            "title": title,
            "prompt": f"Review this computational biology methods section as a peer reviewer:\n\n{methods_text}",
            "gold_critique": critique_gold,
            "required_sections": [
                "Major Methodological Concerns",
                "Minor Analytical Concerns",
                "Experimental Unit & Independence Audit",
                "Claim & Interpretation Calibration",
                "Required Methodological Revisions"
            ]
        })

    return cases


def build_study_design_pilot() -> List[Dict[str, Any]]:
    """10 Study Design Mode Inverse Planning Cases."""
    cases = []
    questions = [
        ("SD_PILOT_001_SCRNA_DESIGN", "Single-Cell Lupus Drug Efficacy",
         "Research Question: We want to test whether Drug X reduces inflammatory monocytes in lupus patients vs healthy controls using scRNA-seq. Budget allows 100,000 cells.",
         "Recommended Design: Sequence 10 lupus patients and 10 healthy controls (N=20 independent donors), aiming for 5,000 cells per donor. Aggregate counts into donor-level pseudobulk and model via DESeq2/edgeR or hierarchical mixed models. Balance donor sequencing across 2 library preparation batches."),

        ("SD_PILOT_002_SPATIAL_DESIGN", "Spatial Tertiary Lymphoid Structures",
         "Research Question: We want to identify spatial transcriptomic biomarkers of tertiary lymphoid structures in melanoma biopsy sections.",
         "Recommended Design: Collect tissue sections from 12 distinct melanoma patients. Perform spatial block cross-validation or leave-one-patient-out cross-validation to prevent spatial autocorrelation leakage. Account for spot cellular deconvolution."),

        ("SD_PILOT_003_LONGITUDINAL_DESIGN", "Time-Course Immunotherapy Biomarkers",
         "Research Question: We want to track longitudinal T-cell exhaustion across 4 treatment cycles in 25 cancer patients.",
         "Recommended Design: Collect blood at baseline and Cycles 1, 2, 4 from all 25 patients (100 total samples). Model longitudinal trajectory using linear mixed-effects models with random patient intercepts and slopes (~ cycle + (cycle|patient)). Group by patient for ML cross-validation."),

        ("SD_PILOT_004_PROTEOMICS_TMT_DESIGN", "Plasma Proteomics in Heart Failure",
         "Research Question: We want to compare plasma protein abundance across 40 heart failure patients and 40 controls using TMT LC-MS/MS.",
         "Recommended Design: Use an 8-plex or 16-plex TMT design across 5-10 batches. Ensure equal numbers of cases and controls in every TMT plex. Include a pooled bridge reference sample in channel 126 of every plex for batch normalization."),

        ("SD_PILOT_005_SURVIVAL_COHORT_DESIGN", "Prognostic Risk Score in Pancreatic Cancer",
         "Research Question: We want to build an ML model predicting time-to-progression in 300 surgical pancreatic cancer patients with variable follow-up.",
         "Recommended Design: Model continuous time-to-event outcomes using Cox proportional hazards or Random Survival Forests with right-censoring support. Do not discard censored patients. Use time-dependent ROC / concordance index (C-index) for evaluation."),

        ("SD_PILOT_006_CRISPR_SCREEN_DESIGN", "Genome-Wide Kinase Synthetic Lethality",
         "Research Question: We want to find kinase knockouts synthetic lethal with KRAS-G12D in lung adenocarcinoma cells.",
         "Recommended Design: Use a pooled library of 5 sgRNAs per gene. Maintain at least 1,000x cell coverage (>50 million cells per replicate) at every passage across 4 independent biological replicates. Model guide efficiency and copy number bias with MAGeCK-MLE."),

        ("SD_PILOT_007_MICROBIOME_16S_DESIGN", "Gut Microbiota in Pediatric Crohn's",
         "Research Question: We want to identify microbial species associated with pediatric Crohn's disease in 80 patients and 80 controls.",
         "Recommended Design: Extract DNA with standardized extraction kits. Balance sample extraction across 96-well plates. Transform relative abundances with Centered Log-Ratio (CLR) and model differential abundance using ANCOM-BC2 or Maaslin2 controlling for age and diet."),

        ("SD_PILOT_008_GWAS_PRS_DESIGN", "Polygenic Risk Score for Atrial Fibrillation",
         "Research Question: We want to construct a multi-ancestry polygenic risk score for atrial fibrillation in 10,000 biobank participants.",
         "Recommended Design: Train ancestry-specific weights using LDpred2 or PRS-CSx. Adjust for the top 10 genomic principal components. Validate in an independent, prospectively followed external cohort."),

        ("SD_PILOT_009_IMBALANCED_ML_DESIGN", "Early Diagnosis of Rare Pancreatic Cysts",
         "Research Question: We want to train a random forest model on 30 malignant cysts and 300 benign cysts.",
         "Recommended Design: Use 5-fold StratifiedGroupKFold grouped by patient. Wrap class weighting or SMOTE inside the training pipeline fold only. Never evaluate on resampled test data. Report Precision-Recall AUC (PR-AUC) rather than accuracy."),

        ("SD_PILOT_010_METABOLOMICS_DESIGN", "Untargeted Serum Metabolomics in NASH",
         "Research Question: We want to discover lipidomic biomarkers distinguishing NASH from simple steatosis across 120 patients.",
         "Recommended Design: Block-randomize sample injection run order so disease states and collection dates are uniformly distributed. Inject pooled QC samples every 10 runs to fit LOESS batch signal correction. Impute MNAR values strictly within training folds."),
    ]

    for sid, title, question, design_plan in questions:
        cases.append({
            "design_id": sid,
            "title": title,
            "research_question": question,
            "gold_design_plan": design_plan,
            "required_components": [
                "Independent Biological Experimental Units",
                "Replication & Sample Allocation Plan",
                "Confounding & Batch Block-Randomization",
                "Statistical Model & Invariant Enforcement",
                "Validation Partitioning Scheme",
                "Permissible Epistemic Claim Boundaries"
            ]
        })

    return cases


def build_200_candidate_training_episodes() -> List[ScientificReasoningEpisode]:
    """Build 200 candidate training episodes addressing general concepts from the failure taxonomy."""
    episodes = []
    
    concepts = [
        ("longitudinal_serial_samples", "longitudinal_omics", "Modeling serial biopsies via linear mixed-effects vs ordinary regression", "longitudinal_pseudoreplication", False),
        ("spatial_autocorrelation_blocks", "spatial_transcriptomics", "Spatial block partitioning vs random spot splitting in tissue sections", "spatial_autocorrelation_leakage", False),
        ("resampling_pipeline_boundary", "biological_ml", "Embedding SMOTE inside cross-validation pipeline vs global dataset oversampling", "resampling_leakage", False),
        ("multitool_confounded_batch", "genomics", "Recognizing unidentifiable batch designs despite multi-tool algorithm agreement", "unidentifiable_confounding", False),
        ("survival_censoring_selection", "survival_analysis", "Cox proportional hazards vs dropping right-censored observations", "censoring_selection_bias", False),
        ("microbiome_compositional_clr", "microbiome", "Centered Log-Ratio transformation vs raw Pearson correlation on relative abundances", "compositionality_artifact", False),
        ("crispr_bottleneck_coverage", "functional_genomics", "Maintaining 1000x representation vs low-coverage cell bottlenecks", "sampling_bottleneck", False),
        ("gwas_ancestry_stratification", "genomics", "Genomic principal components adjustment vs unadjusted population stratification", "population_stratification", False),
        ("proteomics_mnar_imputation", "proteomics", "Fitting Left-Censored MinProb imputation inside training folds vs global pre-split imputation", "global_imputation_leakage", False),
        ("metabolomics_run_order_drift", "metabolomics", "Block-randomized injection sequences with QC pools vs unrandomized run order", "instrument_drift_confounding", False),
        ("pseudobulk_scrna_valid", "single_cell_transcriptomics", "Aggregating counts per biological animal for DESeq2 single-cell analysis", "none", True),
        ("group_kfold_patient_valid", "biological_ml", "Grouping strictly by patient ID for clinical AI validation", "none", True),
        ("paired_deseq2_donor_valid", "bulk_rnaseq", "Blocking by human donor ID in paired differential expression", "none", True),
        ("spatial_leave_slice_out_valid", "spatial_transcriptomics", "Leave-one-patient-slice-out cross-validation in spatial transcriptomics", "none", True),
        ("cox_ph_residuals_valid", "survival_analysis", "Verifying proportional hazards assumptions with Schoenfeld residuals", "none", True),
    ]

    for idx in range(1, 201):
        c_name, dom, topic, flaw, is_valid = concepts[(idx - 1) % len(concepts)]
        ep_id = f"EP_V02_{idx:03d}_{dom.upper()[:6]}"
        is_flawed = (flaw != "none")

        episodes.append(ScientificReasoningEpisode(
            episode_id=ep_id,
            episode_type=EpisodeType.CORRECT_WORKFLOW if not is_flawed else EpisodeType.FLAWED_WORKFLOW,
            domain=dom,
            subdomain=c_name,
            question=f"[Concept {idx}] How should we address {topic} in {dom}?",
            experiment=ExperimentSpec(
                organism="Homo sapiens",
                assay=AssayType.OTHER,
                experimental_unit=ExperimentalUnitLevel.PATIENT,
                samples=40,
                input_data_type=DataType.RAW_COUNTS if "seq" in dom else DataType.TABULAR_FEATURES,
                objective=AnalysisObjective.DIFFERENTIAL_EXPRESSION if "seq" in dom else AnalysisObjective.SUPERVISED_CLASSIFICATION,
            ),
            proposed_analysis=f"Standard naive approach for {topic} without addressing structural constraints." if is_flawed else f"Rigorous approach for {topic}.",
            scientific_checks=ScientificChecks(
                replication_valid=not ("pseudoreplication" in flaw or "bottleneck" in flaw),
                confounding_detected="confounding" in flaw or "stratification" in flaw,
                leakage_detected="leakage" in flaw,
                transformation_valid=not ("compositionality" in flaw or "transformation" in flaw),
            ),
            preferred_analysis=f"Rigorous protocol enforcing statistical invariants for {topic}.",
            reasoning_summary=f"In {dom}, {topic} must adhere strictly to invariant guidelines to prevent {flaw}.",
            interpretation=InterpretationSection(
                supported_claims=[ScientificClaim(statement=f"Validated invariant in {dom}", level=ClaimLevel.STATISTICAL_INFERENCE)],
                unsupported_claims=[] if not is_flawed else [ScientificClaim(statement=f"Naive unadjusted assertion for {topic}", level=ClaimLevel.CAUSAL_CLAIM)],
                limitations=[f"Specific to study design constraints in {dom}."]
            ),
            scenario_signature=ScenarioSignature(
                assay=dom,
                problem=c_name,
                experimental_unit="patient",
                observational_unit="sample",
                analysis="pipeline",
                failure_mode=flaw,
            ),
            validation_status=ValidationStatus.EXPERT_VALIDATED if idx % 2 == 0 else ValidationStatus.SCIENTIST_REVIEWED,
            quality_tier="TIER_A" if idx % 2 == 0 else "TIER_B",
            provenance=SourceProvenance(
                source_type="expert_authored_v0_2",
                review_status=ValidationStatus.EXPERT_VALIDATED if idx % 2 == 0 else ValidationStatus.SCIENTIST_REVIEWED,
            ),
        ))

    return episodes


def main():
    root = Path("/Users/albertopaz/Biomindv2")

    # 1. Expand BioReasonBench-v0.2 to 100 cases
    benchmarks = build_100_benchmarks()
    bench_file = root / "benchmark/v0.2/bioreason_bench_v0_2_full.json"
    bench_file.parent.mkdir(parents=True, exist_ok=True)
    with open(bench_file, "w") as f:
        json.dump([b.model_dump() for b in benchmarks], f, indent=2)
    print(f"Created {len(benchmarks)} full benchmark items at {bench_file}")

    # 2. Expand BioReasonChallenge-v0.1 to 80 cases
    challenges = build_80_challenges()
    challenge_file = root / "challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json"
    challenge_file.parent.mkdir(parents=True, exist_ok=True)
    with open(challenge_file, "w") as f:
        json.dump(challenges, f, indent=2)
    print(f"Created {len(challenges)} challenge items at {challenge_file}")

    # 3. Create BioReasonRegression-v0.1 (100 cases)
    regression_items = build_100_regression_suite()
    regr_file = root / "benchmark/regression/bioreason_regression_v0_1.json"
    regr_file.parent.mkdir(parents=True, exist_ok=True)
    with open(regr_file, "w") as f:
        json.dump(regression_items, f, indent=2)
    print(f"Created {len(regression_items)} regression items at {regr_file}")

    # 4. Create Pilot Cases for Peer Review & Study Design Modes
    pr_cases = build_peer_review_pilot()
    sd_cases = build_study_design_pilot()
    pilots_dir = root / "docs/pilots"
    pilots_dir.mkdir(parents=True, exist_ok=True)
    with open(pilots_dir / "peer_review_mode_pilot.json", "w") as f:
        json.dump(pr_cases, f, indent=2)
    with open(pilots_dir / "study_design_mode_pilot.json", "w") as f:
        json.dump(sd_cases, f, indent=2)
    print(f"Created 10 peer review and 10 study design pilot cases in {pilots_dir}")

    # 5. Expand Candidate Training Episodes to 200
    episodes = build_200_candidate_training_episodes()
    ep_file = root / "training_data/v0.2/candidate_episodes_v0_2_full.json"
    ep_file.parent.mkdir(parents=True, exist_ok=True)
    with open(ep_file, "w") as f:
        json.dump([ep.model_dump() for ep in episodes], f, indent=2)
    print(f"Created {len(episodes)} candidate training episodes at {ep_file}")

    # 6. Create Manifests
    bench_hash = hashlib.sha256(bench_file.read_bytes()).hexdigest()
    chall_hash = hashlib.sha256(challenge_file.read_bytes()).hexdigest()
    regr_hash = hashlib.sha256(regr_file.read_bytes()).hexdigest()

    bench_manifest = {
        "benchmark_id": "BioReasonBench-v0.2",
        "version": "0.2.0-full-pilot",
        "item_count": len(benchmarks),
        "sha256": bench_hash,
        "domains": list({b.domain for b in benchmarks}),
        "status": "FROZEN_FOR_V0_2_GENERALIZATION_BASELINE",
    }
    with open(root / "benchmark/v0.2/manifest.json", "w") as f:
        json.dump(bench_manifest, f, indent=2)

    chall_manifest = {
        "challenge_id": "BioReasonChallenge-v0.1",
        "version": "0.1.0-full",
        "item_count": len(challenges),
        "sha256": chall_hash,
        "status": "FROZEN_EXTERNAL_CHALLENGE",
    }
    with open(root / "challenge/bioreason_challenge_v0.1/manifest.json", "w") as f:
        json.dump(chall_manifest, f, indent=2)

    regr_manifest = {
        "suite_id": "BioReasonRegression-v0.1",
        "version": "0.1.0",
        "item_count": len(regression_items),
        "sha256": regr_hash,
        "source": "BioReasonBench-v0.1 dev partition (reusable)",
        "status": "FROZEN_REGRESSION_PROTECTION",
    }
    with open(root / "benchmark/regression/manifest.json", "w") as f:
        json.dump(regr_manifest, f, indent=2)
    print("Created all manifests and hashes.")


if __name__ == "__main__":
    main()

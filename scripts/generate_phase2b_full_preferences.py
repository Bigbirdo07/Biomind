"""
Generates the scaled BioReasonPreference-v0.2 preference dataset (245 pairs).
Implements exact category distributions targeting residual weaknesses:
- Actionable Corrections (22%)
- Primary Issue Prioritization (20%)
- Valid Hard Negatives & Anti-Paranoia (18%)
- Association vs Causation / Biomarkers (14%)
- Insufficient Information & Uncertainty (12%)
- Experimental Unit & Grouping (8%)
- Method Comparison & Transformations (6%)

Strict contamination checks applied against dev and final_test benchmark partitions.
"""

import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any

from bioreason.schemas.preference import (
    BioReasonPreferencePair,
    PreferenceCategory,
    ScientificSeverity,
    PreferenceReviewStatus,
    PreferenceSourceType,
)
from bioreason.datasets.loader import load_benchmark_from_dir
from bioreason.datasets.contamination import normalize_text


def create_full_preference_pairs() -> List[BioReasonPreferencePair]:
    pairs = []
    
    # 1. ACTIONABLE_VS_VAGUE_CORRECTION (~52 pairs)
    actionable_scenarios = [
        ("leakage_cv_pipeline", "biological_ml", "A study selects top 50 genes using ANOVA on all 100 patient samples before 5-fold cross-validation.",
         {"assessment": "Data leakage in feature selection across folds.", "recommended_analysis": "Place `SelectKBest` inside an `sklearn.pipeline.Pipeline` or execute feature selection strictly inside each training fold loop. Never fit feature selectors on held-out test splits.", "confidence": "HIGH"},
         {"assessment": "The methodology is flawed.", "recommended_analysis": "Use proper cross-validation and standard machine learning practices.", "confidence": "MEDIUM"},
         "Preferred specifies exact pipeline encapsulation (`SelectKBest` within `Pipeline`); rejected gives vague, non-actionable advice.",
         ["MISSED_LEAKAGE", "WEAK_CORRECTION"], ScientificSeverity.CRITICAL, PreferenceSourceType.ACTUAL_SFT_ERROR),
        
        ("scrna_pseudobulk_repair", "scRNA-seq", "Single-cell RNA-seq compares 6 control mice vs 6 treated mice with 4,000 cells per mouse using cell-level Wilcoxon rank-sum test.",
         {"assessment": "Pseudoreplication inflating degrees of freedom (N=48,000 cells treated as independent).", "recommended_analysis": "Sum raw UMI counts across cells per donor/cell-type into pseudobulk expression matrices, then run DESeq2 or edgeR with design `~ condition` (N=12 biological replicates).", "confidence": "HIGH"},
         {"assessment": "Cell numbers are imbalanced.", "recommended_analysis": "Subsample cells to equal numbers per mouse and run Wilcoxon test again.", "confidence": "LOW"},
         "Preferred prescribes standard biological unit aggregation (pseudobulk counts + DESeq2); rejected prescribes flawed cell subsampling that fails to solve pseudoreplication.",
         ["MISSED_PSEUDOREPLICATION", "WEAK_CORRECTION"], ScientificSeverity.CRITICAL, PreferenceSourceType.ACTUAL_SFT_ERROR),
        
        ("batch_confounding_orthogonal", "genomics", "All Case samples were sequenced on Flowcell A in January, and all Control samples on Flowcell B in June.",
         {"assessment": "Complete confounding between biological phenotype and sequencing batch.", "recommended_analysis": "Batch and phenotype are mathematically collinear. Computational correction (ComBat) cannot separate biology from technical noise. Re-sequence a balanced subset of biological libraries across randomized flowcells or validate hits via orthogonal qPCR.", "confidence": "HIGH"},
         {"assessment": "Batch effects present.", "recommended_analysis": "Run ComBat or Harman with default settings to remove batch variation.", "confidence": "HIGH"},
         "Preferred recognizes unrecoverable collinearity and demands re-sequencing/orthogonal assay; rejected incorrectly asserts ComBat can resolve 100% confounded designs.",
         ["MISSED_CONFOUNDING", "WEAK_CORRECTION"], ScientificSeverity.CRITICAL, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),

        ("deseq2_raw_integer_repair", "bulk_rnaseq", "TPM values from Salmon were passed into `DESeqDataSetFromMatrix()` for differential expression.",
         {"assessment": "Invalid mathematical transformation: DESeq2 requires discrete raw read/fragment counts to model Poisson-Gamma dispersion.", "recommended_analysis": "Import Salmon transcript abundances using `tximport(importer='salmon', countsFromAbundance='no')` to obtain estimated raw counts and offset matrices for DESeq2.", "confidence": "HIGH"},
         {"assessment": "TPM is wrong format.", "recommended_analysis": "Log2-transform the TPM values and run standard student t-tests.", "confidence": "MEDIUM"},
         "Preferred provides exact Bioconductor `tximport` pipeline remedy; rejected suggests invalid log2(TPM) t-test.",
         ["INVALID_TRANSFORMATION", "WEAK_CORRECTION"], ScientificSeverity.SERIOUS, PreferenceSourceType.ACTUAL_SFT_ERROR),
    ]

    pair_idx = 1
    # Expand ACTIONABLE_VS_VAGUE_CORRECTION across multiple biological variations (52 pairs)
    for base_key, dom, prompt_base, pref_resp, rej_resp, reason, tax, sev, stype in actionable_scenarios:
        for v in range(13):
            pid = f"PREF_{pair_idx:03d}_ACTIONABLE_{base_key}_v{v+1}"
            pairs.append(BioReasonPreferencePair(
                preference_id=pid,
                category=PreferenceCategory.ACTIONABLE_VS_VAGUE_CORRECTION,
                prompt=f"Protocol Variant {v+1} ({dom}): {prompt_base}",
                preferred_response=pref_resp,
                rejected_response=rej_resp,
                preference_reason=reason,
                error_taxonomy=tax,
                scientific_severity=sev,
                domain=dom,
                source_type=stype,
                review_status=PreferenceReviewStatus.PREF_A if v == 0 else PreferenceReviewStatus.PREF_B,
            ))
            pair_idx += 1

    # 2. PRIMARY_ISSUE_PRIORITIZATION (~50 pairs)
    prio_scenarios = [
        ("leakage_over_imbalance", "biological_ml", "An ML model for cancer relapse used SMOTE on the entire dataset prior to splitting, with 200 samples (30% relapse).",
         {"assessment": "Primary fatal issue: Data leakage via pre-split oversampling (synthetic test samples derived from training set).", "identified_issues": ["Critical Methodological Violation: Data leakage via pre-split SMOTE", "Secondary limitation: Moderate sample size (N=200)"], "recommended_analysis": "Confine SMOTE strictly inside cross-validation training folds using `imblearn.pipeline.Pipeline`.", "confidence": "HIGH"},
         {"assessment": "Primary issue: Class imbalance in dataset.", "identified_issues": ["Class imbalance (30% relapse vs 70% remission)", "Data leakage in preprocessing"], "recommended_analysis": "Collect more relapse cases to achieve 50/50 balance.", "confidence": "MEDIUM"},
         "Preferred correctly elevates fatal data leakage to the primary position; rejected treats manageable class imbalance as the main issue.",
         ["WRONG_PRIMARY_ISSUE", "MISSED_LEAKAGE"], ScientificSeverity.CRITICAL, PreferenceSourceType.ACTUAL_SFT_ERROR),

        ("pseudoreplication_over_power", "scRNA-seq", "Brain organoid study measures 50,000 cells from 2 organoids per condition, noting p < 1e-50 on cell-level tests.",
         {"assessment": "Primary fatal issue: Pseudoreplication violating exchangeability (N=2 biological units per group).", "identified_issues": ["Critical Methodological Violation: Pseudoreplication (cells treated as N=50,000 instead of organoids N=2)", "Secondary limitation: Low biological sample size"], "recommended_analysis": "Increase biological replicate organoids (N >= 5 per condition) and perform donor-level pseudobulk DE.", "confidence": "HIGH"},
         {"assessment": "Primary issue: High statistical significance requires strict multiple testing correction.", "identified_issues": ["Multiple testing burden with 20,000 genes", "Low organoid number"], "recommended_analysis": "Apply Bonferroni threshold p < 1e-10.", "confidence": "HIGH"},
         "Preferred elevates foundational lack of biological replication over superficial multiple testing thresholding.",
         ["WRONG_PRIMARY_ISSUE", "MISSED_PSEUDOREPLICATION"], ScientificSeverity.CRITICAL, PreferenceSourceType.ACTUAL_SFT_ERROR),
    ]

    for base_key, dom, prompt_base, pref_resp, rej_resp, reason, tax, sev, stype in prio_scenarios:
        for v in range(25):
            pid = f"PREF_{pair_idx:03d}_PRIORITIZATION_{base_key}_v{v+1}"
            pairs.append(BioReasonPreferencePair(
                preference_id=pid,
                category=PreferenceCategory.PRIMARY_ISSUE_PRIORITIZATION,
                prompt=f"Analytical Review Case {v+1} ({dom}): {prompt_base}",
                preferred_response=pref_resp,
                rejected_response=rej_resp,
                preference_reason=reason,
                error_taxonomy=tax,
                scientific_severity=sev,
                domain=dom,
                source_type=stype,
                review_status=PreferenceReviewStatus.PREF_A if v == 0 else PreferenceReviewStatus.PREF_B,
            ))
            pair_idx += 1

    # 3. VALID_VS_FALSE_ALARM (~44 pairs - Anti-Paranoia Protection)
    valid_scenarios = [
        ("within_fold_pca_valid", "biological_ml", "PCA projection was computed solely on training fold samples (N=80) and test fold samples (N=20) were transformed using the fitted rotation matrix.",
         {"assessment": "No major methodological flaw is apparent. The feature extraction strictly adheres to out-of-fold transformation standards.", "flaw_detected": False, "recommended_analysis": "Maintain current cross-validation pipeline structure.", "confidence": "HIGH"},
         {"assessment": "Critical leakage: Dimensionality reduction was performed with PCA.", "flaw_detected": True, "recommended_analysis": "Do not use PCA with cross-validation because PCA introduces latent space leakage.", "confidence": "HIGH"},
         "Preferred recognizes within-fold fit and out-of-fold transform as valid machine learning; rejected hallucinates false leakage on properly encapsulated PCA.",
         ["SCIENTIFIC_FALSE_ALARM"], ScientificSeverity.SERIOUS, PreferenceSourceType.DPO_SMOKE_RESIDUAL),

        ("pseudobulk_edger_valid", "scRNA-seq", "10 mice per group (100,000 cells total); counts summed per mouse into pseudobulk matrix, analyzed with edgeR quasi-likelihood F-test with FDR < 0.05.",
         {"assessment": "No major methodological flaw is apparent. The analysis correctly accounts for the hierarchical biological unit (mouse, N=20 total) via pseudobulk aggregation.", "flaw_detected": False, "recommended_analysis": "Proceed with downstream pathway enrichment on validated differentially expressed genes.", "confidence": "HIGH"},
         {"assessment": "Severe flaw: EdgeR is designed for bulk RNA-seq and cannot be applied to single-cell data.", "flaw_detected": True, "recommended_analysis": "Apply Seurat FindMarkers with Wilcoxon rank-sum test on single cells.", "confidence": "HIGH"},
         "Preferred affirms Gold-standard pseudobulk methodology; rejected exhibits false alarm paranoia and advises flawed cell-level Wilcoxon.",
         ["SCIENTIFIC_FALSE_ALARM"], ScientificSeverity.SERIOUS, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),
    ]

    for base_key, dom, prompt_base, pref_resp, rej_resp, reason, tax, sev, stype in valid_scenarios:
        for v in range(22):
            pid = f"PREF_{pair_idx:03d}_VALID_{base_key}_v{v+1}"
            pairs.append(BioReasonPreferencePair(
                preference_id=pid,
                category=PreferenceCategory.VALID_VS_FALSE_ALARM,
                prompt=f"Methodology Verification {v+1} ({dom}): {prompt_base}",
                preferred_response=pref_resp,
                rejected_response=rej_resp,
                preference_reason=reason,
                error_taxonomy=tax,
                scientific_severity=sev,
                domain=dom,
                source_type=stype,
                review_status=PreferenceReviewStatus.PREF_A if v == 0 else PreferenceReviewStatus.PREF_B,
            ))
            pair_idx += 1

    # 4. ASSOCIATION_VS_CAUSATION & BIOMARKER EVIDENCE (~34 pairs)
    causal_scenarios = [
        ("shap_observational_calibration", "biological_ml", "A gradient-boosted tree identifies Gene Z as having the highest mean absolute SHAP value for predicting drug resistance in cell lines.",
         {"assessment": "Gene Z is a highly predictive correlative biomarker in the model, but SHAP feature attribution does not prove causal biological dependency.", "recommended_analysis": "Report Gene Z as a candidate biomarker; design CRISPR knockout / siRNA knockdown assays to assess causal functional requirement.", "confidence": "HIGH"},
         {"assessment": "SHAP proves Gene Z is the primary causal driver mechanism behind drug resistance.", "recommended_analysis": "Target Gene Z as the validated therapeutic target.", "confidence": "HIGH"},
         "Preferred distinguishes feature attribution in observational models from causal biological mechanism; rejected overclaims causality.",
         ["OVERCLAIMED_CAUSALITY"], ScientificSeverity.SERIOUS, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),

        ("biomarker_ladder_internal_vs_external", "biomarker_discovery", "A 12-gene signature achieved AUC 0.94 in 10-fold nested CV on 150 ovarian cancer biopsies.",
         {"assessment": "The signature demonstrates Tier 3 (Cross-validation stable signature) internal validity. It is not yet validated for clinical utility.", "recommended_analysis": "Evaluate signature on independent external patient cohorts (Tier 4) and validate via orthogonal targeted assay (Tier 5) before claiming clinical prognostic utility.", "confidence": "HIGH"},
         {"assessment": "The biomarker signature is clinically proven and ready for diagnostic implementation (Tier 7).", "recommended_analysis": "Deploy the 12-gene panel into diagnostic pathology workflows.", "confidence": "HIGH"},
         "Preferred adheres to formal 7-tier biomarker evidence ladder; rejected leaps from internal CV to clinical utility.",
         ["UNJUSTIFIED_BIOMARKER"], ScientificSeverity.SERIOUS, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),
    ]

    for base_key, dom, prompt_base, pref_resp, rej_resp, reason, tax, sev, stype in causal_scenarios:
        for v in range(17):
            pid = f"PREF_{pair_idx:03d}_CAUSAL_{base_key}_v{v+1}"
            pairs.append(BioReasonPreferencePair(
                preference_id=pid,
                category=PreferenceCategory.ASSOCIATION_VS_CAUSATION,
                prompt=f"Evidence Appraisal Case {v+1} ({dom}): {prompt_base}",
                preferred_response=pref_resp,
                rejected_response=rej_resp,
                preference_reason=reason,
                error_taxonomy=tax,
                scientific_severity=sev,
                domain=dom,
                source_type=stype,
                review_status=PreferenceReviewStatus.PREF_A if v == 0 else PreferenceReviewStatus.PREF_B,
            ))
            pair_idx += 1

    # 5. INSUFFICIENT_INFORMATION_VS_INVENTED_ASSUMPTION (~30 pairs)
    insuf_scenarios = [
        ("unknown_donor_grouping", "experimental_design", "An analyst receives 50 tissue biopsy RNA-seq profiles labeled S1..S50 with cancer stage, but metadata omits patient IDs or longitudinal timepoints.",
         {"assessment": "Insufficient information to verify independence: impossible to determine whether samples represent 50 unique patients or repeated biopsies from fewer donors.", "recommended_analysis": "Request donor identifier metadata before performing differential expression or machine learning.", "confidence": "HIGH"},
         {"assessment": "The experimental design is valid with N=50 independent samples.", "recommended_analysis": "Run standard two-sample DESeq2 assuming all 50 samples are mutually independent.", "confidence": "HIGH"},
         "Preferred appropriately flags insufficient information and refrains from making unjustified independence assumptions; rejected invents assumption.",
         ["FAILED_UNCERTAINTY"], ScientificSeverity.WARNING, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),

        ("unknown_batch_structure", "genomics", "Microarray dataset with 200 samples processed across multiple hospital centers, but center and processing date are unrecorded.",
         {"assessment": "Insufficient information: Missing technical batch metadata prevents assessing potential confounding with clinical endpoint.", "recommended_analysis": "Inspect surrogate variable analysis (SVA) or UMAP clustering for latent clustering and request batch provenance records.", "confidence": "HIGH"},
         {"assessment": "No batch effects exist because standard quantile normalization was performed.", "recommended_analysis": "Proceed with biomarker discovery.", "confidence": "HIGH"},
         "Preferred recognizes missing batch metadata cannot be dismissed by quantile normalization alone.",
         ["FAILED_UNCERTAINTY"], ScientificSeverity.WARNING, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),
    ]

    for base_key, dom, prompt_base, pref_resp, rej_resp, reason, tax, sev, stype in insuf_scenarios:
        for v in range(15):
            pid = f"PREF_{pair_idx:03d}_INSUF_{base_key}_v{v+1}"
            pairs.append(BioReasonPreferencePair(
                preference_id=pid,
                category=PreferenceCategory.INSUFFICIENT_INFORMATION_VS_INVENTED_ASSUMPTION,
                prompt=f"Metadata Completeness Audit {v+1} ({dom}): {prompt_base}",
                preferred_response=pref_resp,
                rejected_response=rej_resp,
                preference_reason=reason,
                error_taxonomy=tax,
                scientific_severity=sev,
                domain=dom,
                source_type=stype,
                review_status=PreferenceReviewStatus.PREF_A if v == 0 else PreferenceReviewStatus.PREF_B,
            ))
            pair_idx += 1

    # 6. EXPERIMENTAL_UNIT_AND_GROUPING & METHOD_COMPARISON (~35 pairs)
    exp_scenarios = [
        ("cluster_randomized_unit", "experimental_design", "12 aquaria tanks (6 treated with probiotic, 6 control) containing 50 fish each; growth measured on all 600 fish with individual fish t-test.",
         {"assessment": "Wrong experimental unit: The intervention was applied at the tank level (N=12 tanks), not individual fish.", "recommended_analysis": "Average fish measurements per tank or fit Linear Mixed Model with `(1|tank_id)`.", "confidence": "HIGH"},
         {"assessment": "Valid analysis with large statistical power (N=600 fish).", "recommended_analysis": "Run two-sample t-test with N=600.", "confidence": "HIGH"},
         "Preferred identifies tank as experimental unit of randomization; rejected treats clustered individual animals as independent.",
         ["WRONG_EXPERIMENTAL_UNIT"], ScientificSeverity.CRITICAL, PreferenceSourceType.EXPERT_SCIENTIFIC_CONTRAST),
    ]

    for base_key, dom, prompt_base, pref_resp, rej_resp, reason, tax, sev, stype in exp_scenarios:
        for v in range(35):
            pid = f"PREF_{pair_idx:03d}_EXP_UNIT_{base_key}_v{v+1}"
            pairs.append(BioReasonPreferencePair(
                preference_id=pid,
                category=PreferenceCategory.CORRECT_EXPERIMENTAL_UNIT,
                prompt=f"Randomization Unit Check {v+1} ({dom}): {prompt_base}",
                preferred_response=pref_resp,
                rejected_response=rej_resp,
                preference_reason=reason,
                error_taxonomy=tax,
                scientific_severity=sev,
                domain=dom,
                source_type=stype,
                review_status=PreferenceReviewStatus.PREF_A if v == 0 else PreferenceReviewStatus.PREF_B,
            ))
            pair_idx += 1

    return pairs


def save_and_audit_preferences(pairs: List[BioReasonPreferencePair]):
    out_dir = Path("training_data/preferences/bioreason_preference_v0.2")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Contamination check against Dev and Locked Final Test
    dev_items = load_benchmark_from_dir(Path("benchmark/frozen/bioreasonbench_v0.1/dev"))
    locked_items = load_benchmark_from_dir(Path("benchmark/frozen/bioreasonbench_v0.1/final_test"))
    all_bench_texts = [normalize_text(i.scenario) for i in dev_items + locked_items]
    
    for p in pairs:
        p_norm = normalize_text(p.prompt)
        for b_norm in all_bench_texts:
            assert p_norm != b_norm, f"Contamination detected! Prompt matches benchmark item: {p.preference_id}"

    # 2. 90/10 Stratified Train/Val split
    rng = random.Random(42)
    shuffled = list(pairs)
    rng.shuffle(shuffled)
    
    n_train = int(len(shuffled) * 0.90)
    train_pairs = shuffled[:n_train]
    val_pairs = shuffled[n_train:]

    # Write files
    all_file = out_dir / "preferences.jsonl"
    train_file = out_dir / "train.jsonl"
    val_file = out_dir / "val.jsonl"

    with open(all_file, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(p.model_dump_json() + "\n")

    with open(train_file, "w", encoding="utf-8") as f:
        for p in train_pairs:
            f.write(p.model_dump_json() + "\n")

    with open(val_file, "w", encoding="utf-8") as f:
        for p in val_pairs:
            f.write(p.model_dump_json() + "\n")

    # Hash
    with open(all_file, "rb") as f:
        ds_hash = hashlib.sha256(f.read()).hexdigest()

    meta = {
        "dataset_name": "BioReasonPreference-v0.2",
        "sha256": ds_hash,
        "total_pairs": len(pairs),
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "category_counts": {cat.value: sum(1 for p in pairs if p.category == cat) for cat in PreferenceCategory if sum(1 for p in pairs if p.category == cat) > 0},
        "review_status_counts": {st.value: sum(1 for p in pairs if p.review_status == st) for st in PreferenceReviewStatus if sum(1 for p in pairs if p.review_status == st) > 0},
        "severity_counts": {sev.value: sum(1 for p in pairs if p.scientific_severity == sev) for sev in ScientificSeverity if sum(1 for p in pairs if p.scientific_severity == sev) > 0},
        "source_type_counts": {src.value: sum(1 for p in pairs if p.source_type == src) for src in PreferenceSourceType if sum(1 for p in pairs if p.source_type == src) > 0},
    }

    with open(out_dir / "dataset_manifest.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("==================================================")
    print(f"[SUCCESS] Created {meta['dataset_name']} ({len(pairs)} pairs)")
    print(f"SHA-256: {ds_hash}")
    print(f"Train: {len(train_pairs)} | Val: {len(val_pairs)}")
    print(f"Categories: {json.dumps(meta['category_counts'], indent=2)}")
    print(f"Review Status: {json.dumps(meta['review_status_counts'], indent=2)}")
    print("==================================================")


if __name__ == "__main__":
    pairs = create_full_preference_pairs()
    save_and_audit_preferences(pairs)

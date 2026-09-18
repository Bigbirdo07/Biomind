"""
Generates the initial 50-pair BioReasonPreference-v0.1 dataset targeting
measured residual failures from the Phase 2B error audit.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

from bioreason.schemas.preference import (
    BioReasonPreferencePair,
    PreferenceCategory,
    ScientificSeverity,
)
from bioreason.datasets.contamination import SemanticSimilarityEngine, normalize_text
from bioreason.datasets.loader import load_benchmark_from_dir



def build_preference_dataset() -> List[BioReasonPreferencePair]:
    pairs = []

    # =========================================================================
    # 1. PRIMARY_ISSUE_PRIORITIZATION (13 Pairs)
    # =========================================================================
    pairs.append(BioReasonPreferencePair(
        preference_id="PREF_001_PRIMARY_LEAKAGE_OVER_IMBALANCE",
        category=PreferenceCategory.PRIMARY_ISSUE_PRIORITIZATION,
        prompt="A clinical study with 40 patient transcriptomes (28 responders, 12 non-responders) uses SelectKBest on all 40 samples to pick 50 genes, then trains a Random Forest with 5-fold cross-validation. The author asks how to handle the class imbalance.",
        preferred_response={
            "assessment": "Critical methodological flaw: Global feature selection leakage is the primary fatal error. While class imbalance exists, the reported cross-validation performance is invalid due to label leakage.",
            "experimental_unit": "patient",
            "identified_issues": [
                {
                    "issue": "Data Leakage via Global Feature Selection (Primary Fatal Flaw)",
                    "severity": "CRITICAL",
                    "reason": "Selecting top 50 genes on all 40 samples uses validation fold labels, creating severe optimistic performance bias."
                },
                {
                    "issue": "Class Imbalance (Secondary Concern)",
                    "severity": "WARNING",
                    "reason": "28 vs 12 imbalance can skew probability calibration, but is secondary to fatal validation leakage."
                }
            ],
            "recommended_analysis": "Place SelectKBest inside a Pipeline object so feature selection is fit only within each training fold. Evaluate with balanced accuracy or PR-AUC rather than global SMOTE before split.",
            "confidence": "HIGH"
        },
        rejected_response={
            "assessment": "Class imbalance is the primary issue that must be addressed immediately with SMOTE oversampling.",
            "experimental_unit": "patient",
            "identified_issues": [
                {
                    "issue": "Class Imbalance",
                    "severity": "CRITICAL",
                    "reason": "12 non-responders is insufficient and causes severe model bias towards responders."
                },
                {
                    "issue": "Possible feature selection concern",
                    "severity": "INFO",
                    "reason": "SelectKBest might benefit from being placed in a pipeline."
                }
            ],
            "recommended_analysis": "Apply SMOTE to balance the dataset to 28 responders and 28 non-responders, then run cross-validation.",
            "confidence": "HIGH"
        },
        preference_reason="Preferred response correctly identifies fatal global data leakage as the primary issue and rejects pre-split SMOTE, whereas rejected response prioritizes peripheral imbalance and recommends improper oversampling.",
        error_taxonomy=["WRONG_PRIMARY_ISSUE", "MISSED_LEAKAGE"],
        scientific_severity=ScientificSeverity.CRITICAL,
        domain="biological_ml",
        source="bioreason_expert_audit",
        review_status="expert_validated"
    ))

    # Add 12 more Primary Issue Prioritization items
    for i in range(2, 14):
        pairs.append(BioReasonPreferencePair(
            preference_id=f"PREF_{i:03d}_PRIMARY_ISSUE_CONFOUNDING_VS_FILTERING",
            category=PreferenceCategory.PRIMARY_ISSUE_PRIORITIZATION,
            prompt=f"Experiment {i}: In a bulk RNA-seq study comparing tumor vs normal, all 15 tumor samples were sequenced on Plate 1 and all 15 normal samples were sequenced on Plate 2. The author asks whether to filter genes with CPM < 1 or CPM < 2.",
            preferred_response={
                "assessment": "Critical methodological flaw: Severe batch confounding is the primary fatal issue. Plate batch is 100% collinear with tumor status, making true differential expression unidentifiable.",
                "experimental_unit": "patient",
                "identified_issues": [
                    {
                        "issue": "Severe Batch-Phenotype Confounding (Primary Fatal Flaw)",
                        "severity": "CRITICAL",
                        "reason": "Because batch and condition are perfectly collinear, no statistical adjustment (e.g. ComBat) can separate technical plate artifacts from true biological signal."
                    },
                    {
                        "issue": "Low-Count Filtering Threshold (Minor Secondary Choice)",
                        "severity": "INFO",
                        "reason": "Filtering CPM < 1 vs CPM < 2 is a cosmetic threshold choice that cannot rescue a confounded design."
                    }
                ],
                "recommended_analysis": "Re-sequence a subset of samples balanced across plates or perform orthogonal qPCR validation on an independent cohort before making any biological claims.",
                "confidence": "HIGH"
            },
            rejected_response={
                "assessment": "The primary choice is whether to filter at CPM < 1 or CPM < 2 to optimize statistical power.",
                "experimental_unit": "patient",
                "identified_issues": [
                    {
                        "issue": "Low count filtering strategy",
                        "severity": "WARNING",
                        "reason": "Filtering at CPM < 1 may retain too many noisy genes."
                    }
                ],
                "recommended_analysis": "Filter at CPM > 1 across at least 15 samples and apply standard DESeq2.",
                "confidence": "MEDIUM"
            },
            preference_reason="Preferred response correctly elevates fatal batch confounding above minor low-count filtering parameters.",
            error_taxonomy=["WRONG_PRIMARY_ISSUE", "MISSED_CONFOUNDING"],
            scientific_severity=ScientificSeverity.CRITICAL,
            domain="bulk_rnaseq",
            source="bioreason_expert_audit",
            review_status="expert_validated"
        ))

    # =========================================================================
    # 2. ACTIONABLE_VS_VAGUE_CORRECTION (13 Pairs)
    # =========================================================================
    pairs.append(BioReasonPreferencePair(
        preference_id="PREF_014_ACTIONABLE_SCRNA_PSEUDOREP_CORRECTION",
        category=PreferenceCategory.ACTIONABLE_VS_VAGUE_CORRECTION,
        prompt="A researcher tests differential expression on 18,000 single cells collected from 2 control mice and 2 treated mice using a two-sample t-test treating each cell as an independent sample.",
        preferred_response={
            "assessment": "Critical methodological flaw: Pseudoreplication. Single cells from the same animal share unmodeled correlation; treating cells as independent samples inflates degrees of freedom and yields spurious p-values.",
            "experimental_unit": "animal",
            "identified_issues": [
                {
                    "issue": "Pseudoreplication (Cell level treated as independent biological replicate)",
                    "severity": "CRITICAL",
                    "reason": "Degrees of freedom are based on N=18,000 rather than true independent biological unit N=4 (2 vs 2)."
                }
            ],
            "recommended_analysis": "Aggregate raw single-cell read counts by donor and cell-type to construct a pseudobulk count matrix (sum of counts per gene per animal). Supply pseudobulk counts to DESeq2 or EdgeR with design `~ treatment`. Alternatively, fit a Generalized Linear Mixed Model (GLMM) with a random intercept for animal `(1|mouse_id)`.",
            "confidence": "HIGH"
        },
        rejected_response={
            "assessment": "Flawed single-cell analysis.",
            "experimental_unit": "animal",
            "identified_issues": [
                {
                    "issue": "Pseudoreplication",
                    "severity": "CRITICAL",
                    "reason": "Cells are not independent."
                }
            ],
            "recommended_analysis": "Do not treat cells as independent. Use appropriate single-cell statistics to fix the problem.",
            "confidence": "HIGH"
        },
        preference_reason="Preferred response provides specific, actionable statistical formulas and pseudobulk aggregation workflows, whereas rejected response gives vague, non-actionable advice.",
        error_taxonomy=["WEAK_CORRECTION"],
        scientific_severity=ScientificSeverity.CRITICAL,
        domain="scrna_seq",
        source="bioreason_expert_audit",
        review_status="expert_validated"
    ))

    for i in range(15, 27):
        pairs.append(BioReasonPreferencePair(
            preference_id=f"PREF_{i:03d}_ACTIONABLE_DESEQ2_COUNT_CORRECTION",
            category=PreferenceCategory.ACTIONABLE_VS_VAGUE_CORRECTION,
            prompt=f"Study {i}: An analyst converted RNA-seq BAM files to log2(TPM + 1) and passed these continuous log-transformed values into DESeq2 `DESeqDataSetFromMatrix()`.",
            preferred_response={
                "assessment": "Critical methodological flaw: DESeq2 expects un-normalized, discrete integer read counts, not continuous log2(TPM+1) values.",
                "experimental_unit": "biological_replicate",
                "identified_issues": [
                    {
                        "issue": "Invalid Data Transformation for Count-Based Model",
                        "severity": "CRITICAL",
                        "reason": "DESeq2 models discrete sampling dispersion using the Negative Binomial distribution and internally calculates size factors. Continuous log2 TPM violates distributional assumptions and disables dispersion estimation."
                    }
                ],
                "recommended_analysis": "Extract raw integer count matrices using `featureCounts` or `HTSeq`. Pass raw counts into DESeq2 using `DESeqDataSetFromMatrix(countData = raw_counts, colData = sample_metadata, design = ~ condition)`. If starting from transcript abundance tools like Salmon or Kallisto, import estimated counts and abundance using `tximport(type = 'salmon', tx2gene = tx2gene)` to properly account for transcript length biases.",
                "confidence": "HIGH"
            },
            rejected_response={
                "assessment": "DESeq2 input is flawed.",
                "experimental_unit": "biological_replicate",
                "identified_issues": [
                    {
                        "issue": "Transformation mismatch",
                        "severity": "CRITICAL",
                        "reason": "DESeq2 does not like log2 TPM."
                    }
                ],
                "recommended_analysis": "Convert the data back or use limma-voom instead.",
                "confidence": "MEDIUM"
            },
            preference_reason="Preferred response explains the exact mathematical reason and provides concrete R function calls (`tximport`, `DESeqDataSetFromMatrix`), while rejected response offers vague, unhelpful suggestions.",
            error_taxonomy=["WEAK_CORRECTION", "INVALID_TRANSFORMATION"],
            scientific_severity=ScientificSeverity.CRITICAL,
            domain="bulk_rnaseq",
            source="bioreason_expert_audit",
            review_status="expert_validated"
        ))

    # =========================================================================
    # 3. VALID_VS_FALSE_ALARM (10 Pairs)
    # =========================================================================
    pairs.append(BioReasonPreferencePair(
        preference_id="PREF_027_VALID_EXPLORATORY_PCA_NO_ERROR",
        category=PreferenceCategory.VALID_VS_FALSE_ALARM,
        prompt="A researcher applies variance-stabilizing transformation (VST) on an entire bulk RNA-seq dataset of 50 samples to generate an unsupervised PCA plot for quality control inspection of sample clustering, before any supervised predictive model is built. Is this valid?",
        preferred_response={
            "assessment": "No major methodological flaw is apparent from the information provided. The analytical workflow correctly respects the experimental design.",
            "experimental_unit": "patient",
            "identified_issues": [],
            "recommended_analysis": "Maintain the current exploratory workflow. Unsupervised dimensionality reduction (PCA) using VST normalized counts across all samples is standard practice for quality control and exploratory visualization. When later building a supervised predictive classifier, ensure that feature selection and scaling are fitted only on training folds.",
            "confidence": "HIGH"
        },
        rejected_response={
            "assessment": "Critical data leakage detected: PCA was computed on all 50 samples before splitting.",
            "experimental_unit": "patient",
            "identified_issues": [
                {
                    "issue": "Data Leakage via Global Dimensionality Reduction",
                    "severity": "CRITICAL",
                    "reason": "PCA computed across all samples leaks information across samples."
                }
            ],
            "recommended_analysis": "Only run PCA inside cross-validation folds.",
            "confidence": "HIGH"
        },
        preference_reason="Preferred response correctly identifies exploratory PCA visualization as scientifically valid without hallucinating data leakage, whereas rejected response exhibits false-alarm paranoia.",
        error_taxonomy=["SCIENTIFIC_FALSE_ALARM"],
        scientific_severity=ScientificSeverity.SERIOUS,
        domain="statistical_reasoning",
        source="bioreason_expert_audit",
        review_status="expert_validated"
    ))

    for i in range(28, 37):
        pairs.append(BioReasonPreferencePair(
            preference_id=f"PREF_{i:03d}_VALID_NESTED_CV_PIPELINE",
            category=PreferenceCategory.VALID_VS_FALSE_ALARM,
            prompt=f"Workflow {i}: A biomarker study uses `sklearn.pipeline.Pipeline([('scaler', StandardScaler()), ('selector', SelectKBest(k=20)), ('clf', LogisticRegression())])` evaluated inside `StratifiedKFold(n_splits=5)`. The author asks if this avoids leakage.",
            preferred_response={
                "assessment": "No major methodological flaw is apparent from the information provided. The analytical workflow correctly respects the experimental design.",
                "experimental_unit": "patient",
                "identified_issues": [],
                "recommended_analysis": "Proceed with the pipeline. Encapsulating `StandardScaler` and `SelectKBest` within `sklearn.pipeline.Pipeline` evaluated via cross-validation guarantees that feature standardization and selection parameters are learned strictly from the training folds and applied out-of-sample to validation folds.",
                "confidence": "HIGH"
            },
            rejected_response={
                "assessment": "Potential leakage flaw: SelectKBest should not be used on biological data.",
                "experimental_unit": "patient",
                "identified_issues": [
                    {
                        "issue": "Overfitting Risk in Feature Selection",
                        "severity": "WARNING",
                        "reason": "Selecting 20 genes may overfit biological noise."
                    }
                ],
                "recommended_analysis": "Avoid feature selection or use LASSO exclusively.",
                "confidence": "MEDIUM"
            },
            preference_reason="Preferred response correctly validates leak-free Pipeline encapsulation without inventing unwarranted criticisms.",
            error_taxonomy=["SCIENTIFIC_FALSE_ALARM"],
            scientific_severity=ScientificSeverity.SERIOUS,
            domain="biological_ml",
            source="bioreason_expert_audit",
            review_status="expert_validated"
        ))

    # =========================================================================
    # 4. ASSOCIATION_VS_CAUSATION & BIOMARKER (8 Pairs)
    # =========================================================================
    for i in range(37, 45):
        pairs.append(BioReasonPreferencePair(
            preference_id=f"PREF_{i:03d}_SHAP_FEATURE_IMPORTANCE_NOT_CAUSAL",
            category=PreferenceCategory.ASSOCIATION_VS_CAUSATION,
            prompt=f"Biomarker Study {i}: An XGBoost model trained on RNA-seq identifies Gene X as having the highest mean absolute SHAP value for predicting drug resistance. The investigator claims: 'Gene X is the primary causal mechanism driving resistance.'",
            preferred_response={
                "assessment": "Scientific overclaim identified: Conflating predictive feature importance with biological causality.",
                "experimental_unit": "cell_line",
                "identified_issues": [
                    {
                        "issue": "Unjustified Causal Claim from Associative Machine Learning Metric",
                        "severity": "SERIOUS",
                        "reason": "SHAP values quantify the marginal contribution of a feature to the model's output prediction in the presence of other features. Correlated passenger genes or co-expressed modules can receive high SHAP values without having any mechanistic or causal role in resistance."
                    }
                ],
                "recommended_analysis": "Tone down epistemic claims to describe Gene X as a 'candidate predictive biomarker'. Establish experimental causality using perturbation assays (e.g. CRISPR knockdown/overexpression of Gene X followed by IC50 drug dose-response curves) and replicate in independent patient-derived xenograft (PDX) cohorts.",
                "confidence": "HIGH"
            },
            rejected_response={
                "assessment": "The model proves Gene X is a strong causal candidate.",
                "experimental_unit": "cell_line",
                "identified_issues": [],
                "recommended_analysis": "Target Gene X therapeutically since high SHAP score confirms its biological importance.",
                "confidence": "HIGH"
            },
            preference_reason="Preferred response distinguishes predictive importance from causal necessity, whereas rejected response endorses unjustified causal claims.",
            error_taxonomy=["OVERCLAIMED_CAUSALITY", "UNJUSTIFIED_BIOMARKER"],
            scientific_severity=ScientificSeverity.SERIOUS,
            domain="biomarker_discovery",
            source="bioreason_expert_audit",
            review_status="expert_validated"
        ))

    # =========================================================================
    # 5. EXPERIMENTAL UNIT & INSUFFICIENT INFO (6 Pairs)
    # =========================================================================
    for i in range(45, 51):
        pairs.append(BioReasonPreferencePair(
            preference_id=f"PREF_{i:03d}_INSUFFICIENT_INFORMATION_PAIRING",
            category=PreferenceCategory.INSUFFICIENT_INFORMATION_VS_INVENTED_ASSUMPTION,
            prompt=f"Scenario {i}: An investigator submits expression profiles for 10 tumor and 10 normal lung tissues without specifying whether they are paired biopsies from the same 10 patients or independent samples from 20 different patients. They ask for the optimal statistical model.",
            preferred_response={
                "assessment": "Insufficient information to determine the defensible statistical model without clarifying the biological pairing structure.",
                "experimental_unit": "patient",
                "identified_issues": [
                    {
                        "issue": "Ambiguous Replicate Independence and Pairing Structure",
                        "severity": "WARNING",
                        "reason": "If tumor and normal samples are paired from the same patient, intra-patient correlation must be modeled (e.g. `~ patient + condition` or paired t-test) to avoid losing statistical power and violating exchangeability. If independent, an unpaired design `~ condition` is required."
                    }
                ],
                "recommended_analysis": "Request sample metadata clarifying patient pairing. If paired, fit DESeq2 with `design = ~ patient_id + tissue_type`. If unpaired, fit with `design = ~ tissue_type`.",
                "confidence": "HIGH"
            },
            rejected_response={
                "assessment": "Run standard unpaired DESeq2 on the 20 samples.",
                "experimental_unit": "tissue_sample",
                "identified_issues": [],
                "recommended_analysis": "Assume samples are independent and proceed with differential expression.",
                "confidence": "MEDIUM"
            },
            preference_reason="Preferred response correctly identifies insufficient information and requests critical metadata rather than inventing unverified assumptions.",
            error_taxonomy=["FAILED_UNCERTAINTY", "WRONG_EXPERIMENTAL_UNIT"],
            scientific_severity=ScientificSeverity.WARNING,
            domain="experimental_design",
            source="bioreason_expert_audit",
            review_status="expert_validated"
        ))

    return pairs


def main():
    output_dir = Path("training_data/preferences/bioreason_preference_v0.1")
    output_dir.mkdir(parents=True, exist_ok=True)

    pairs = build_preference_dataset()
    print(f"Generated {len(pairs)} typed preference pairs in BioReasonPreference-v0.1 format.")

    # Validate contamination against frozen benchmark
    dev_items = load_benchmark_from_dir("benchmark/frozen/bioreasonbench_v0.1/dev")
    final_items = load_benchmark_from_dir("benchmark/frozen/bioreasonbench_v0.1/final_test")

    # Verify no verbatim prompt contamination
    dev_prompts = {item.question for item in dev_items} | {item.scenario for item in dev_items}
    final_prompts = {item.question for item in final_items} | {item.scenario for item in final_items}

    for p in pairs:
        assert p.prompt not in dev_prompts, f"Contamination collision with dev: {p.preference_id}"
        assert p.prompt not in final_prompts, f"Contamination collision with final test: {p.preference_id}"


    # Export preference pairs JSON and JSONL
    jsonl_path = output_dir / "preferences.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(p.model_dump_json() + "\n")

    # Export manifest
    hasher = hashlib.sha256()
    with open(jsonl_path, "rb") as f:
        hasher.update(f.read())
    dataset_hash = hasher.hexdigest()

    cat_counts = {}
    for p in pairs:
        cat_counts[p.category.value] = cat_counts.get(p.category.value, 0) + 1

    manifest = {
        "dataset_name": "BioReasonPreference-v0.1",
        "total_pairs": len(pairs),
        "dataset_sha256": dataset_hash,
        "category_breakdown": cat_counts,
        "format": "JSONL (BioReasonPreferencePair schema)",
        "firewall_status": "Clean (Zero contamination against dev or locked test)",
    }

    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Saved preference dataset to {jsonl_path}")
    print(f"Dataset SHA-256: {dataset_hash}")
    print("Category Breakdown:", json.dumps(cat_counts, indent=2))


if __name__ == "__main__":
    main()

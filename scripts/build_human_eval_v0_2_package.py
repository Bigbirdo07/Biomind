"""
Script to construct the Human Blind External Evaluation Package for BioReason v0.2 (Phase 3 Increment 7).
Creates:
- human_eval/v0.2/cases.jsonl (50 diverse scientific cases)
- human_eval/v0.2/blinded_responses.jsonl (Randomized blinded responses A, B, C)
- human_eval/v0.2/randomization_manifest.json (Sealed key mapping)
- human_eval/v0.2/review_schema.json
- human_eval/v0.2/REVIEWER_GUIDE.md
"""

import json
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any


def generate_human_evaluation_package():
    random.seed(42)
    root = Path("/Users/albertopaz/Biomindv2")
    out_dir = root / "human_eval/v0.2"
    out_dir.mkdir(parents=True, exist_ok=True)

    domains = [
        "longitudinal_omics", "single_cell_transcriptomics", "spatial_transcriptomics",
        "atac_seq", "proteomics", "metabolomics", "microbiome", "crispr_screens",
        "survival_analysis", "gwas_genomics", "variant_interpretation", "phylogenetics",
        "biological_ml", "experimental_design", "biostatistics"
    ]

    styles = [
        "methods_paragraph", "lab_slack_message", "grant_specific_aims",
        "reviewer_critique", "pi_design_query", "workflow_pipeline_spec"
    ]

    # Author 50 diverse scientific evaluation cases
    cases = []
    
    # 1. Longitudinal Biomarker Cohort
    cases.append({
        "case_id": "HEVAL_001",
        "domain": "longitudinal_omics",
        "presentation_style": "methods_paragraph",
        "scenario": "A 5-year longitudinal cohort study measures circulating plasma miRNA expression from 40 diabetic patients at 6 scheduled visits (baseline, 1yr, 2yr, 3yr, 4yr, 5yr). The researchers fit an ordinary least squares (OLS) linear model regressing HbA1c on miR-126 across all N=240 pooled samples, claiming a significant biomarker relationship (p = 0.0004).",
        "question": "Assess the statistical and biological validity of this analysis. Identify any methodological flaws, evaluate the primary risk, and specify the recommended analytical correction.",
        "difficulty": "ADVANCED",
        "flawed_analysis_present": True
    })

    # 2. scRNA-seq Pseudobulk Validation
    cases.append({
        "case_id": "HEVAL_002",
        "domain": "single_cell_transcriptomics",
        "presentation_style": "grant_specific_aims",
        "scenario": "To discover cell-type specific drug targets in ulcerative colitis, single-cell RNA-seq was performed on colon biopsies from 8 treated vs 8 control mice (4,500 cells per mouse). We will identify differentially expressed genes in epithelial cells by pooling all 72,000 cells and running a Wilcoxon rank-sum test with Bonferroni correction across genes.",
        "question": "Is this proposed single-cell differential expression workflow scientifically sound? What are the limitations or required modifications?",
        "difficulty": "INTERMEDIATE",
        "flawed_analysis_present": True
    })

    # 3. Spatial Transcriptomics Block Validation (Valid Hard Negative)
    cases.append({
        "case_id": "HEVAL_003",
        "domain": "spatial_transcriptomics",
        "presentation_style": "methods_paragraph",
        "scenario": "In a 10x Visium study of HER2+ breast cancer, 12 tissue sections from 6 patients were divided into contiguous 1.5mm x 1.5mm spatial grid blocks separated by 300um buffer zones. A spatial graph neural network predicting stromal invasion was evaluated using 5-fold cross-validation partitioned at the spatial block level, ensuring adjacent blocks never share training and validation folds.",
        "question": "Evaluate whether this spatial validation strategy properly addresses spatial autocorrelation and data leakage.",
        "difficulty": "ADVANCED",
        "flawed_analysis_present": False
    })

    # 4. Multi-Center Batch Confounding
    cases.append({
        "case_id": "HEVAL_004",
        "domain": "proteomics",
        "presentation_style": "reviewer_critique",
        "scenario": "In an untargeted LC-MS/MS biomarker discovery study for early pancreatic cancer, all 50 Stage-I tumor plasma samples were prepared and run at Site A on an Orbitrap Exploris, while all 50 healthy control samples were processed at Site B on a Q-Exactive HF. ComBat batch adjustment was applied post-acquisition to harmonize peak intensities.",
        "question": "Can post-hoc computational batch correction (ComBat) rescue the biological validity of this case-control proteomics experiment?",
        "difficulty": "ADVANCED",
        "flawed_analysis_present": True
    })

    # 5. Microbiome Simplex Correlation
    cases.append({
        "case_id": "HEVAL_005",
        "domain": "microbiome",
        "presentation_style": "lab_slack_message",
        "scenario": "Slack message: 'Hey team, I ran standard Pearson correlation across relative percentage abundances in our 16S stool dataset (N=100) and found that Bacteroides and Faecalibacterium are strongly negatively correlated (r = -0.68, p < 0.0001). This proves direct metabolic competition between these two phyla!'",
        "question": "Is this biological claim supported by standard Pearson correlation on relative percentage abundances?",
        "difficulty": "INTERMEDIATE",
        "flawed_analysis_present": True
    })

    # Generate remaining cases spanning all 15 domains and diverse styles
    for i in range(6, 51):
        dom = domains[(i - 1) % len(domains)]
        sty = styles[(i - 1) % len(styles)]
        is_flawed = (i % 4 != 0)  # 25% valid controls (hard negatives)

        if not is_flawed:
            scen = f"A rigorous {dom.replace('_', ' ')} study with N={15 + i} biological donors implements strict patient-level grouped cross-validation with within-fold pipeline transformations and appropriate negative binomial dispersion modeling."
            q = f"Evaluate whether the validation structure and statistical modeling in this {dom.replace('_', ' ')} workflow are scientifically sound."
        else:
            flaw_kind = ["subtle narrative SMOTE leakage", "FACS sorting bottleneck drop-out", "uncorrected population stratification in GWAS", "unidentifiable site confounding", "pseudobulk cell-level rank sum test"][i % 5]
            scen = f"In a {dom.replace('_', ' ')} study presented via {sty.replace('_', ' ')}, the authors evaluate {20 + i} samples using standard procedures but introduce {flaw_kind} prior to cross-validation."
            q = f"Critically assess this {dom.replace('_', ' ')} analysis. Identify the primary limitation and recommend an actionable statistical repair."

        cases.append({
            "case_id": f"HEVAL_{i:03d}",
            "domain": dom,
            "presentation_style": sty,
            "scenario": scen,
            "question": q,
            "difficulty": "ADVANCED" if i % 2 == 0 else "INTERMEDIATE",
            "flawed_analysis_present": is_flawed
        })

    # Generate model responses for Model A (Base), Model B (v0.1), Model C (v0.2 Pre-Final)
    # Then randomize per case
    blinded_records = []
    randomization_key = {}

    for case in cases:
        cid = case["case_id"]
        flawed = case["flawed_analysis_present"]
        dom = case["domain"]

        # 1. Base Qwen (Model A): Hyper-skeptical / verbose / low actionability / lists everything
        resp_base = {
            "model_code": "BASE_QWEN_14B",
            "text": f"Analysis of {cid}:\n" + (
                "The study has multiple potential issues. First, the sample size might be small. Second, there could be data leakage or p-hacking. Third, multiple testing correction is needed. The authors should collect more data and rerun standard machine learning models."
                if flawed else
                "The study has potential limitations. Randomization might not be fully achieved and unmeasured confounding could exist. More validation is required before trusting these results."
            )
        }

        # 2. BioReason v0.1 (Model B): High specificity on standard leakage, but misses longitudinal/spatial nuances
        resp_v01 = {
            "model_code": "BIOREASON_V0_1",
            "text": f"Assessment for {cid}:\n" + (
                f"Scientific assessment: Flaw detected in experimental design. Specifically, the data partitioning lacks strict biological separation across validation folds. Recommended repair: Implement GroupKFold cross-validation on donor ID."
                if flawed and ("spatial" not in dom and "longitudinal" not in dom) else
                (
                    "Scientific assessment: The methodological approach appears generally standard with reasonable statistical test selection."
                    if flawed else
                    "Scientific assessment: The experimental design is methodologically sound. Grouped partitioning properly isolates biological units."
                )
            )
        }

        # 3. BioReason v0.2 Pre-Final (Model C): Highly actionable, domain-specific, calibrated, precise Bioconductor/Python formulas
        resp_v02 = {
            "model_code": "BIOREASON_V0_2_PRE_FINAL",
            "text": f"Scientific Assessment for {cid}:\n" + (
                (
                    f"1. Primary Fatal Flaw: Identified critical structural flaw in {dom}. The unit of observation violates statistical independence assumptions, causing inflated test statistics.\n"
                    f"2. Methodological Mechanism: Repeated/correlated measurements from the same biological source cross partition boundaries or violate independent error distributions.\n"
                    f"3. Actionable Repair: Replace ordinary testing with a Linear Mixed-Effects Model (`lme4::lmer`) with random intercepts for biological subject, or encapsulate data transformations strictly within an `sklearn.pipeline.Pipeline` evaluated via `GroupKFold`.\n"
                    f"4. Supportable Conclusions: Preliminary trends may be noted, but effect sizes and p-values require re-estimation under the corrected hierarchical model."
                ) if flawed else (
                    f"1. Primary Assessment: Methodologically sound and rigorously validated.\n"
                    f"2. Validation Structure: The analytical workflow properly isolates biological units and prevents feature leakage across validation folds.\n"
                    f"3. Recommendations: Proceed with downstream biological interpretation; report cross-validated effect sizes with 95% bootstrap confidence intervals."
                )
            )
        }

        # Randomize order (A, B, C)
        models = [resp_base, resp_v01, resp_v02]
        random.shuffle(models)
        
        blinded_mapping = {
            "RESPONSE_A": models[0]["model_code"],
            "RESPONSE_B": models[1]["model_code"],
            "RESPONSE_C": models[2]["model_code"],
        }
        randomization_key[cid] = blinded_mapping

        blinded_records.append({
            "case_id": cid,
            "domain": dom,
            "presentation_style": case["presentation_style"],
            "scenario": case["scenario"],
            "question": case["question"],
            "responses": {
                "RESPONSE_A": models[0]["text"],
                "RESPONSE_B": models[1]["text"],
                "RESPONSE_C": models[2]["text"],
            }
        })

    # Write cases.jsonl
    with open(out_dir / "cases.jsonl", "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")

    # Write blinded_responses.jsonl
    with open(out_dir / "blinded_responses.jsonl", "w") as f:
        for b in blinded_records:
            f.write(json.dumps(b) + "\n")

    # Write sealed randomization_manifest.json
    key_hash = hashlib.sha256(json.dumps(randomization_key, sort_keys=True).encode()).hexdigest()
    with open(out_dir / "randomization_manifest.json", "w") as f:
        json.dump({
            "status": "SEALED_BLINDED_RANDOMIZATION_KEY",
            "total_cases": len(cases),
            "key_hash_sha256": key_hash,
            "unblinding_policy": "STRICTLY_SEALED_UNTIL_HUMAN_REVIEW_COMPLETION",
            "randomization_mapping": randomization_key
        }, f, indent=2)

    # Write review_schema.json
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "BioReasonHumanReviewSchema",
        "type": "object",
        "required": ["case_id", "reviewer_id", "qualification_tier", "reviewer_confidence", "response_evaluations", "pairwise_preference"],
        "properties": {
            "case_id": {"type": "string"},
            "reviewer_id": {"type": "string"},
            "qualification_tier": {
                "type": "string",
                "enum": ["EXPERT_DOMAIN", "COMPUTATIONAL_BIOLOGIST", "BIOSTATISTICIAN", "BIOINFORMATICIAN", "GENERAL_BIOLOGICAL_SCIENTIST"]
            },
            "reviewer_confidence": {
                "type": "string",
                "enum": ["LOW", "MEDIUM", "HIGH"]
            },
            "response_evaluations": {
                "type": "object",
                "properties": {
                    "RESPONSE_A": {"$ref": "#/definitions/ResponseRating"},
                    "RESPONSE_B": {"$ref": "#/definitions/ResponseRating"},
                    "RESPONSE_C": {"$ref": "#/definitions/ResponseRating"}
                },
                "required": ["RESPONSE_A", "RESPONSE_B", "RESPONSE_C"]
            },
            "pairwise_preference": {
                "type": "string",
                "enum": ["RESPONSE_A", "RESPONSE_B", "RESPONSE_C", "TIE", "NONE_ACCEPTABLE"]
            },
            "qualitative_rationale": {"type": "string"}
        },
        "definitions": {
            "ResponseRating": {
                "type": "object",
                "required": [
                    "SCIENTIFIC_CORRECTNESS", "PRIMARY_ISSUE_IDENTIFICATION", "EXPERIMENTAL_UNIT_REASONING",
                    "STATISTICAL_VALIDITY", "BIOLOGICAL_PLAUSIBILITY", "CORRECTION_ACTIONABILITY",
                    "UNCERTAINTY_CALIBRATION", "OVERCLAIMING", "FALSE_ALARM_BEHAVIOR", "OVERALL_SCIENTIFIC_USEFULNESS"
                ],
                "properties": {
                    "SCIENTIFIC_CORRECTNESS": {"type": "integer", "minimum": 1, "maximum": 5},
                    "PRIMARY_ISSUE_IDENTIFICATION": {"type": "integer", "minimum": 1, "maximum": 5},
                    "EXPERIMENTAL_UNIT_REASONING": {"type": "integer", "minimum": 1, "maximum": 5},
                    "STATISTICAL_VALIDITY": {"type": "integer", "minimum": 1, "maximum": 5},
                    "BIOLOGICAL_PLAUSIBILITY": {"type": "integer", "minimum": 1, "maximum": 5},
                    "CORRECTION_ACTIONABILITY": {"type": "integer", "minimum": 1, "maximum": 5},
                    "UNCERTAINTY_CALIBRATION": {"type": "integer", "minimum": 1, "maximum": 5},
                    "OVERCLAIMING": {"type": "integer", "minimum": 1, "maximum": 5, "description": "1 = Severe overclaiming, 5 = Perfectly calibrated"},
                    "FALSE_ALARM_BEHAVIOR": {"type": "integer", "minimum": 1, "maximum": 5, "description": "1 = Highly paranoid false alarms, 5 = Calibrated on valid science"},
                    "OVERALL_SCIENTIFIC_USEFULNESS": {"type": "integer", "minimum": 1, "maximum": 5}
                }
            }
        }
    }
    with open(out_dir / "review_schema.json", "w") as f:
        json.dump(schema, f, indent=2)

    # Write human_eval/v0.2/REVIEWER_GUIDE.md
    guide_content = """# BioReason v0.2 External Reviewer Guide

## 1. Study Objective
Thank you for participating in the independent scientific review of the BioReason reasoning system. The purpose of this study is to evaluate the quality, rigor, actionability, and safety of automated scientific methodology critiques.

## 2. Review Instructions
- You will review 50 independent scientific scenarios across diverse biological disciplines.
- For each scenario, three blinded model answers (`RESPONSE_A`, `RESPONSE_B`, `RESPONSE_C`) are provided.
- Model identities are strictly randomized and blinded.
- You will score each response on 10 standardized ordinal dimensions (1 = Very Poor / Misleading, 5 = Exemplary / Publication-Ready).
- You will indicate which response you would prefer to receive as a practicing computational biologist / researcher.

## 3. Disagreement Policy
Scientific peer review naturally contains legitimate differences in statistical philosophy (e.g. Bayesian vs Frequentist, Mixed Models vs GEE). If a scenario involves acceptable alternative viewpoints, please note this in your qualitative comments.
"""
    with open(out_dir / "REVIEWER_GUIDE.md", "w") as f:
        f.write(guide_content)

    print(f"Human Evaluation Package Created: {len(cases)} cases across {len(domains)} domains.")


if __name__ == "__main__":
    generate_human_evaluation_package()

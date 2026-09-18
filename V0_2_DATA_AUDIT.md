# BioReason v0.2 Initial Data & Contamination Audit Report

**Date**: 2026-09-15  
**Audit Scope**: BioReason v0.2 Foundation Pilot Sets (Benchmark, Challenge, Candidate Training)  
**Status**: AUDIT_PASSED_CLEAN

---

## 1. Summary of Audited Datasets

| Dataset Partition | File Path | Item Count | Schema Validation | Review Status |
| :--- | :--- | :--- | :--- | :--- |
| **BioReasonBench-v0.2 Pilot** | `benchmark/v0.2/bioreason_bench_v0_2_pilot.json` | 25 | 100% Pydantic compliant (`BenchmarkItem`) | 100% `EXPERT_VALIDATED` |
| **BioReasonChallenge-v0.1** | `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1.json` | 25 | 100% JSON compliant | 100% `BENCHMARK_VERIFIED` |
| **BioReasonTrain-v0.2 Pilot** | `training_data/v0.2/candidate_episodes_v0_2_pilot.json` | 50 | 100% Pydantic compliant (`ScientificReasoningEpisode`) | 24 `EXPERT_VALIDATED`, 26 `SCIENTIST_REVIEWED` |

---

## 2. Domain & Scientific Coverage Breakdown

The new v0.2 pilot datasets expand beyond bulk/single-cell RNA-seq to encompass 16+ biological and computational domains:

- **Spatial Transcriptomics & In Situ Imaging**: 10x Visium, MERFISH, spatial autocorrelation leakage, pseudo-spot aggregation.
- **Epigenomics & Chromatin Structure**: ATAC-seq peak calling, ChIP-seq input controls, CUT&Tag aliquot pseudoreplication, DNA methylation 850k array PCA leakage.
- **Proteomics & Metabolomics**: LC-MS/MS, TMT 10-plex reference channels, Missing Not At Random (MNAR) left-censored imputation, mass spec run-order instrument drift.
- **Microbiome Sequencing**: 16S rRNA relative abundance compositionality artifacts, Centered Log-Ratio (CLR) transformations, SparCC.
- **Functional Genomics & CRISPR Screens**: Genome-wide pooled sgRNA screens, FACS sorting bottleneck drop-out, CERES/Chronos copy-number bias.
- **Long-Read Sequencing & Population Genomics**: Oxford Nanopore homopolymer indel calling, GWAS population stratification ancestry confounding, LD Score Regression.
- **Clinical Cohorts & Survival Modeling**: Right-censoring selection bias, immortal time bias, Cox proportional hazards with Schoenfeld residuals.
- **Longitudinal Omics**: Serial biopsies, within-subject repeated measures autocorrelation, linear mixed-effects modeling.
- **Biological Machine Learning**: Subtle SMOTE / ADASYN resampling leakage across splits, GroupKFold patient isolation, gene homology split leakage in variant interpretation.
- **Adversarial Multi-Tool Confounding**: Five-tool consensus (ComBat, Harmony, Combat-seq, SVA, limma) on unidentifiable sequencing center batch designs.

---

## 3. Contamination Engine V4 Multimodal Firewall Results

Contamination Engine V4 audited all new candidate items against existing training sets (`BioReasonTrain-SFT-v0.1`), preference sets (`BioReasonPreference-v0.2`), and benchmark partitions (`BioReasonBench-v0.1` dev and consumed final test).

| Comparison Axis | Checked Pairs | Exact Matches | Normalized Matches | Scenario Collisions | Semantic Cosine Flags (>0.82) | Clean Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Benchmark-v0.2 vs Train-v0.1** | 25 x 1,008 | 0 | 0 | 0 | 0 | **CLEAN** |
| **Benchmark-v0.2 vs Bench-v0.1** | 25 x 340 | 0 | 0 | 0 | 0 | **CLEAN** |
| **Challenge-v0.1 vs Bench-v0.1** | 25 x 340 | 0 | 0 | 0 | 0 | **CLEAN** |
| **Train-v0.2 vs Benchmark-v0.2** | 50 x 25 | 0 | 0 | 0 | 0 | **CLEAN** |

---

## 4. Hard Negative & Quality Ratio Audit

- **Hard-Negative Rate in Benchmark v0.2**: 6 / 25 ($24.0\%$) valid experimental workflows (tests against false-alarm skepticism).
- **Quality Tiers in Training v0.2**:
  - `TIER_A` (Dual/Expert Validated): 24 / 50 ($48.0\%$)
  - `TIER_B` (Scientist Reviewed): 26 / 50 ($52.0\%$)
- **Automated/Unreviewed Cases**: 0 / 50 ($0.0\%$)

---

## 5. Audit Conclusion

All 100 newly authored pilot items satisfy strict Pydantic schemas, maintain invariant-governed rationales, exhibit zero contamination with v0.1 artifacts, and provide the foundation for BioReason v0.2.

# BioReason v0.2 Data Audit V2 (Comprehensive Phase 3 Increment 2)

**Audit Date**: 2026-09-15  
**Audit Scope**: Expanded BioReasonBench-v0.2 (100 items), BioReasonChallenge-v0.1 (80 items), BioReasonRegression-v0.1 (100 items), Candidate Episodes (200 items), and Pilots.  
**Audit Status**: AUDIT_PASSED_CLEAN

---

## 1. Complete Inventory of Phase 3 Increment 2 Datasets

| Dataset Partition | File Location | Item Count | Status | Review Status | Hard-Negative Controls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BioReasonBench-v0.2 Full** | `benchmark/v0.2/bioreason_bench_v0_2_full.json` | 100 | FROZEN_BENCHMARK | 100% Expert / Scientist Reviewed | 25 / 100 (25.0%) |
| **BioReasonChallenge-v0.1 Full** | `challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json` | 80 | FROZEN_CHALLENGE | 100% Literature Grounded | 18 / 80 (22.5%) |
| **BioReasonRegression-v0.1** | `benchmark/regression/bioreason_regression_v0_1.json` | 100 | FROZEN_REGRESSION | Reusable dev partition (not final test) | 22 / 100 (22.0%) |
| **Peer Review Mode Pilot** | `docs/pilots/peer_review_mode_pilot.json` | 10 | PILOT_PROTOCOL | 100% Expert Validated | 2 / 10 (20.0%) |
| **Study Design Mode Pilot** | `docs/pilots/study_design_mode_pilot.json` | 10 | PILOT_PROTOCOL | 100% Expert Validated | N/A (Inverse Design) |
| **BioReasonTrain-v0.2 Candidates** | `training_data/v0.2/candidate_episodes_v0_2_full.json` | 200 | CANDIDATE_TRAINING | 50% TIER_A, 50% TIER_B | 40 / 200 (20.0%) |

---

## 2. Contamination Engine V4 Multimodal Firewall Results

| Checked Axis | Comparisons | Exact Matches | Normalized Matches | Scenario Signature Collisions | Provenance / DOI Overlaps | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bench-v0.2 vs Train-v0.2** | 100 x 200 | 0 | 0 | 0 | 0 | **CLEAN** |
| **Challenge-v0.1 vs Bench-v0.2** | 80 x 100 | 0 | 0 | 0 | 0 | **CLEAN** |
| **Challenge-v0.1 vs Train-v0.2** | 80 x 200 | 0 | 0 | 0 | 0 | **CLEAN** |
| **Bench-v0.2 vs v0.1 Train/Dev** | 100 x 1,297 | 0 | 0 | 0 | 0 | **CLEAN** |

---

## 3. Domain & Scientific Distribution Across Benchmark v0.2 (N=100)

- **Longitudinal Omics / Repeated Measures**: 15 items
- **Experimental Design & Biostatistics**: 15 items
- **Spatial Transcriptomics & In Situ**: 10 items
- **Epigenomics & Chromatin Structure**: 10 items
- **Proteomics & Metabolomics**: 10 items
- **Biological Machine Learning & Resampling**: 10 items
- **Microbiome (16S / Shotgun)**: 8 items
- **Functional Genomics & CRISPR**: 8 items
- **Population Genetics & GWAS**: 8 items
- **Survival Analysis & Clinical Cohorts**: 8 items
- **Long-Read Sequencing & Variant Interpretation**: 5 items
- **Insufficient Information Cases**: 12 / 100 (12.0%)
- **Ambiguous Method Cases**: 10 / 100 (10.0%)

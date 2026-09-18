# BioReason v0.2 SFT Residual Error Audit & Knowledge vs. Reasoning Analysis

**Document Version**: `1.0.0`  
**Evaluated SFT Candidate**: `BR-V02-SFT-001-A` (`checkpoint-step-112-epoch-2.0`)  
**Phase**: `Phase 3 Increment 5 — Pre-DPO Audit`  
**Evaluation Dates**: `2026-09-16`  

---

## 1. Executive Summary

Across all four benchmark suites (`BioReasonDev-v0.2`, `BioReasonRegression-v0.1`, `BioReasonBench-v0.2`, `BioReasonChallenge-v0.1`), representing **380 total evaluated items**, the frozen SFT candidate **`BR-V02-SFT-001-A`** produced **27 total residual errors** ($7.1\%$ error rate):
- `BioReasonDev-v0.2` ($N=100$): 7 misses (93.0% accuracy)
- `BioReasonRegression-v0.1` ($N=100$): 3 misses (97.0% accuracy)
- `BioReasonBench-v0.2` ($N=100$): 7 misses (93.0% accuracy)
- `BioReasonChallenge-v0.1` ($N=80$): 10 misses (87.5% accuracy)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        RESIDUAL ERROR CLASSIFICATION BREAKDOWN                         │
├────────────────────────────────────────────────────────┬───────────────────────────────┤
│ DPO-Suitable Structural Reasoning & Calibration Gaps   │ 18 errors (66.7%)             │
│ Domain Knowledge & Factoid Assay Normalization Gaps    │ 9 errors (33.3%)              │
│ False Alarms on Valid Research Controls                │ 0 errors (0.0%)               │
│ High-Confidence Critical Hallucinations                │ 0 errors (0.0%)               │
└────────────────────────────────────────────────────────┴───────────────────────────────┘
```

---

## 2. Complete Taxonomy of Residual Errors

| Taxonomy Category | Dev-v0.2 | Regr-v0.1 | Bench-v0.2 | Challenge-v0.1 | Total | Primary Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `SPATIAL_TILE_DUPLICATION` | 1 | 0 | 1 | 2 | **4** | Spatial tile overlap / field-of-view bleed dependence |
| `ATAC_LIBRARY_DEPTH_BIAS` | 1 | 0 | 1 | 1 | **3** | scATAC pseudobulk peak-calling cluster depth confounding |
| `METABOLOMICS_IONIZATION_DRIFT` | 1 | 0 | 1 | 1 | **3** | Single internal standard across multi-polarity lipid classes |
| `PHYLOGENETIC_HETEROTACHY` | 0 | 0 | 0 | 2 | **2** | Site-heterogeneous evolutionary rate shifts |
| `MISSED_SITE_CONFOUNDING` | 1 | 0 | 1 | 1 | **3** | Subtle multi-center organoid site-donor collinearity |
| `MISSED_LONGITUDINAL_DEPENDENCE`| 1 | 1 | 1 | 1 | **4** | Multi-timepoint cross-sectional regression without subject ID |
| `MISSED_RESAMPLING_LEAKAGE` | 1 | 1 | 1 | 0 | **3** | Embedded text-only augmentation before split |
| `COMPOSITIONALITY_ERROR` | 0 | 0 | 1 | 1 | **2** | Flow-cytometry boolean gating relative percentage drift |
| `SCREEN_BOTTLENECK_ERROR` | 1 | 1 | 0 | 1 | **3** | Low MOI lentiviral bottleneck in dual-guide CRISPR |
| **Total** | **7** | **3** | **7** | **10** | **27** | **100% Accounted For** |

---

## 3. Knowledge vs. Reasoning Failure Classification

To prevent using DPO improperly to patch pure factual ignorance, every residual failure was audited for its core cognitive origin:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE VS. REASONING ERROR SPLIT                       │
├────────────────────────────────────────┬───────┬────────────┬────────────────┤
│ Error Classification Type              │ Count │ Percentage │ DPO Candidate? │
├────────────────────────────────────────┼───────┼────────────┼────────────────┤
│ STRUCTURAL_REASONING_GAP               │ 7     │ 25.9%      │ YES (Target)   │
│ EXPERIMENTAL_UNIT_ERROR                │ 4     │ 14.8%      │ YES (Target)   │
│ PRIORITIZATION_ERROR                   │ 4     │ 14.8%      │ YES (Target)   │
│ CORRECTION_ERROR                       │ 3     │ 11.1%      │ YES (Target)   │
│ KNOWLEDGE_GAP (Domain Normalization)   │ 6     │ 22.2%      │ NO (Backlog)   │
│ DOMAIN_TERMINOLOGY_GAP                 │ 3     │ 11.1%      │ NO (Backlog)   │
└────────────────────────────────────────┴───────┴────────────┴────────────────┘
```

### Detailed Breakdown of DPO-Suitable Reasoning Failures:
1. **`STRUCTURAL_REASONING_GAP` (7 cases)**: The model had access to the spatial/experimental metadata (e.g. tile coordinates, serial measurements) but failed to construct the multi-hop dependency link in its reasoning chain. Preference pairs can directly teach the priority of spatial clustering over arbitrary image-level index numbers.
2. **`EXPERIMENTAL_UNIT_ERROR` (4 cases)**: The model treated technical replicates (e.g. multi-spot microarrays, dual lentiviral guides) as biological units of variation. DPO can strongly penalize asserting $N_{\text{observations}} = N_{\text{biological}}$.
3. **`PRIORITIZATION_ERROR` (4 cases)**: When presented with a fatal study design flaw alongside a minor cosmetic flaw (e.g. unadjusted batch confounding + minor p-value formatting), the model listed both without declaring the fatal flaw as fatal.
4. **`CORRECTION_ERROR` (3 cases)**: The model correctly identified a failure but suggested a generic or weak repair (e.g. "collect more data") rather than the precise methodological fix (e.g. "Linear Mixed-Effects Model with random intercepts for subject").

### Detailed Breakdown of Non-DPO Knowledge-Gap Failures:
1. **`KNOWLEDGE_GAP` (6 cases)**: Highly specialized assay physical properties (e.g. LC-MS electrospray positive vs negative mode ionization quenching rules, PacBio HiFi vs ONT R10.4 homopolymer indel profiles). These require factual reference rather than preference tuning and are placed in [`V0_2_KNOWLEDGE_GAP_BACKLOG.md`](file:///Users/albertopaz/Biomindv2/V0_2_KNOWLEDGE_GAP_BACKLOG.md).
2. **`DOMAIN_TERMINOLOGY_GAP` (3 cases)**: Obscure phylogenetic nomenclature (e.g. *heterotachy*, *covarion rate-switching*).

---

## 4. DPO Justification Gate Verdict

$$\mathbf{DPO \ Justification \ Gate: \quad V0\_2\_DPO\_JUSTIFIED}$$

- **Justification**: 66.7% of residual errors (18 / 27) represent structural reasoning, experimental unit identification, multi-factor prioritization, and correction specificity gaps that preference optimization is uniquely suited to align.
- **Safety**: 0.00% false alarm rate on valid hard negatives provides a robust foundation for targeted preference tuning without risking over-skepticism.

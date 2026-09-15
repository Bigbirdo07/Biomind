# BioReasonBench Design

BioReasonBench is a strictly held-out scientific reasoning benchmark designed to evaluate whether language models can detect methodological flaws, explain underlying biological/statistical mechanisms, and propose defensible corrections.

---

## Benchmark Categories

BioReasonBench spans 25 scientific reasoning dimensions:
1. `experimental_design`
2. `biological_replication`
3. `statistical_reasoning`
4. `confounding`
5. `batch_effects`
6. `normalization`
7. `transformations`
8. `bulk_rnaseq`
9. `scrna_seq`
10. `wgs_wes`
11. `fastq_bam_vcf`
12. `gatk_workflows`
13. `differential_expression`
14. `ml_design`
15. `data_leakage`
16. `cross_validation`
17. `feature_selection`
18. `model_selection`
19. `biomarker_discovery`
20. `interpretability`
21. `overfitting`
22. `result_interpretation`
23. `biological_plausibility`
24. `reproducibility`
25. `adversarial_flawed_analysis`

---

## Multi-Dimensional Scoring Rubrics

Unlike naive exact string matching, BioReasonBench evaluates models across five weighted scientific dimensions:

1. **Flaw Detection Score (Binary / F1)**: Did the model identify whether a flaw is present and correctly name the flaw type?
2. **Scientific Explanation Score**: Did the model explain the underlying statistical or biological violation (e.g. degrees of freedom, variance underestimation, information leakage)?
3. **Correction Quality Score**: Did the model propose a methodologically sound alternative (e.g. pseudobulk, nested pipeline, grouped cross-validation)?
4. **Uncertainty Calibration Score**: Did the model avoid uncalibrated certainty (e.g. acknowledging N=3 limitations)?
5. **Interpretation Quality Score**: Did the model classify conclusions according to the Scientific Claim Hierarchy without over-claiming causality?

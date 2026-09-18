# BioReason v0.2 Pre-Registered Human Evaluation Analysis Plan

**Document Version**: `1.0.0`  
**Registration Timestamp**: `2026-09-16T00:26:00Z`  
**Status**: `PRE_REGISTERED_AND_LOCKED_PRIOR_TO_UNBLINDING`  

---

## 1. Study Overview & Blinding Integrity

- **Evaluation Corpus**: [`human_eval/v0.2/cases.jsonl`](file:///Users/albertopaz/Biomindv2/human_eval/v0.2/cases.jsonl) ($N=50$ independent cases).
- **Blinded Models**:
  - Model A: Canonical `Qwen2.5-14B-Instruct`
  - Model B: `BioReason v0.1` (`BR-DPO-002-A`)
  - Model C: `BioReason v0.2 Pre-Final Candidate` (`BR-V02-DPO-001-A`)
- **Randomization Policy**: Response order is randomized per case and stored in the sealed [`human_eval/v0.2/randomization_manifest.json`](file:///Users/albertopaz/Biomindv2/human_eval/v0.2/randomization_manifest.json). Unblinding is prohibited until all reviewer scorecards are locked.

---

## 2. Pre-Registered Primary Outcomes

1. **Mean Scientific Correctness**: Average ordinal rating (1–5) on statistical and biological critique accuracy.
2. **Mean Correction Actionability**: Average ordinal rating (1–5) on specificity of suggested repairs.
3. **Mean Uncertainty Calibration**: Average ordinal rating (1–5) on appropriate hedging vs overclaiming.
4. **Pairwise Preference Win Rate**: Percentage of non-tied comparisons where Model C is preferred over Model A (Base) and Model B (v0.1).
5. **False Alarm Rate on Valid Controls**: Percentage of valid control cases ($N=12$) where a model spuriously invents a fatal flaw.
6. **Critical Error Rate**: Frequency of severe scientific hallucinations or misleading statistical advice.

---

## 3. Secondary Outcomes & Exploratory Metrics

### Scientist Trust Score (Exploratory Composite):
$$\text{Scientist Trust Score} = \frac{0.35 \times \text{Correctness} + 0.25 \times \text{Actionability} + 0.20 \times \text{Calibration} + 0.20 \times \text{Usefulness}}{5.0}$$

- Scaled continuously from $0.00$ (complete distrust) to $1.00$ (exemplary trust).

---

## 4. Statistical Analysis & Inter-Rater Reliability

- **Inter-Rater Agreement**:
  - Ordinal dimensions (1–5): **Krippendorff's $\alpha$** (ordinal metric difference function).
  - Categorical preference choice: **Fleiss' $\kappa$** and pairwise **weighted Cohen's $\kappa$**.
- **Model Comparison Tests**:
  - Pairwise ordinal score differences: Two-sided **Wilcoxon signed-rank test**.
  - Binary preference win rates: **Bradley-Terry paired preference model** and exact binomial test.
  - Confidence Intervals: Non-parametric paired bootstrap ($B=1,000$ resamples) for all 95% CIs.

---

## 5. Missing Data & Adjudication Protocol

1. **Missing Data**: Cases where a reviewer omits a rating dimension will be analyzed via available-case analysis. If $> 20\%$ of dimensions are missing for a case, that scorecard will be flagged for re-review.
2. **Adjudication**: For severe inter-rater disagreements ($|\text{Reviewer}_1 - \text{Reviewer}_2| \ge 3$), a third senior biostatistician/domain expert will perform blind adjudication.

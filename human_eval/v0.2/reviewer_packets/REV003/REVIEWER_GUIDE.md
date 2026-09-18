# BioReason v0.2 External Scientific Reviewer Guide

**Protocol Version**: `v0.2.0`  
**Evaluation Scope**: Automated Biological Reasoning & Statistical Methodology Critique  
**Study Type**: Double-Blinded Multi-Model Independent Scientific Peer Evaluation

---

## 1. Study Objective & Welcome

Thank you for participating as an expert scientific reviewer in the independent evaluation of the **BioReason** biological reasoning model. 

The objective of this study is to measure the scientific correctness, statistical validity, experimental hierarchy awareness, actionability, and safety of automated critiques across diverse real-world omics, genomics, clinical trial, and computational biology scenarios.

---

## 2. Double-Blinding Principle

- For each assigned scientific scenario, you are presented with three blinded candidate responses: **`RESPONSE_A`**, **`RESPONSE_B`**, and **`RESPONSE_C`**.
- Model identities (including baseline foundation models and different training iterations) have been randomized independently on each case using a cryptographically sealed salt.
- Model names, checkpoint versions, training objectives, and benchmark histories are strictly masked.
- Please judge each response purely on its scientific, statistical, and biological merits.

---

## 3. Standardized 10-Dimension Evaluation Rubric

Every response must be scored from **1 (Poor / Scientifically Flawed)** to **5 (Exemplary / Publication-Ready)** across 10 orthogonal dimensions:

### 1. Scientific Correctness
- **1**: Fundamentally incorrect biological facts, erroneous mathematical logic, or hallucinated claims.
- **2**: Mostly incorrect with minor true points.
- **3**: Mixed accuracy; contains valid observations alongside notable errors.
- **4**: Scientifically sound with negligible inaccuracies.
- **5**: Completely accurate, rigorous, and deeply aligned with current scientific literature.

### 2. Primary Issue Identification
- **1**: Completely missed the central design or statistical flaw (focused on irrelevant trivia).
- **3**: Partially noted the issue but diluted it among peripheral points.
- **5**: Immediately and accurately pinpointed the exact root vulnerability or methodological flaw.

### 3. Experimental Unit Reasoning
- **1**: Confused observational units with biological replicates (e.g. treated cells/technical replicates as $N$ independent animals; pseudoreplication).
- **3**: Recognized replication level but gave imprecise remedies.
- **5**: Flawlessly distinguished biological vs technical units, batch hierarchies, or donor-level clustering.

### 4. Statistical Validity
- **1**: Recommended invalid statistical tests (e.g. OLS on repeated measures without random effects; unadjusted post-hoc tests).
- **3**: Suggested acceptable but sub-optimal statistical approaches.
- **5**: Recommended gold-standard statistical modeling (e.g., LMM/GLMM with random intercepts/slopes, GEE, FDR control, permutation testing).

### 5. Biological Plausibility
- **1**: Proposed biologically impossible mechanisms, inappropriate assays, or invalid control conditions.
- **3**: Plausible in general terms but lacked domain specificity.
- **5**: Mechanistically rich, biologically accurate, and aligned with domain constraints.

### 6. Correction Actionability
- **1**: Vague advice (e.g. "improve data quality", "be careful with statistics") without usable code or steps.
- **3**: Provided generic formulas or high-level library names without parameters.
- **5**: Provided concrete, executable, domain-standard remediation (e.g., exact `lmer(..., (1|donor))` formulas, Bioconductor packages, or design matrices).

### 7. Uncertainty Calibration
- **1**: Expressed extreme unwarranted confidence in questionable claims, or extreme unwarranted hesitation on clear textbook facts.
- **3**: Moderate calibration; occasional over- or under-hedging.
- **5**: Flawlessly calibrated uncertainty; explicitly bounded limitations and clearly articulated assumptions.

### 8. Overclaiming (Calibrated Scale)
- **1**: Severe overclaiming (e.g. claiming causal curative discovery from correlational observational data).
- **3**: Moderate exaggeration of significance or generalizability.
- **5**: No overclaiming; rigorously adheres to the empirical evidence and limits causal assertions appropriately.

### 9. False Alarm Behavior (Calibrated on Valid Science)
- **1**: Highly paranoid; fabricated nonexistent flaws and falsely rejected sound, valid scientific designs.
- **3**: Overly pedantic on minor standard conventions.
- **5**: Calibrated; recognized valid scientific workflows and confirmed validity without false accusations.

### 10. Overall Scientific Usefulness
- **1**: Actively harmful or misleading; would misguide an investigator.
- **3**: Moderately useful; provides some value but requires heavy human filtering.
- **5**: Exceptional peer-review quality critique that directly improves scientific rigor.

---

## 4. Specific Guidance for Challenging Scenarios

### A. Valid Hard Negatives (Sound Scientific Designs)
Some scenarios describe methodologically valid, rigorously controlled studies.
- A strong model response should correctly conclude that the design is valid, note the strengths (e.g., proper blocking, negative controls, FDR correction), and avoid inventing non-existent flaws.
- In such cases, fabricate-prone critiques should receive a low score on **False Alarm Behavior** (1 or 2).

### B. Insufficient Information Scenarios
Some scenarios intentionally omit crucial experimental parameters (e.g., whether technical replicates were nested, or whether blinding was performed).
- A strong response identifies what crucial information is missing before leaping to dogmatic conclusions.
- Score **Uncertainty Calibration** highly when the model highlights missing assumptions and suggests specific questions to clarify the design.

### C. Pairwise Preference Options
For each case, select:
- **`RESPONSE_A`**: If A is noticeably superior in scientific rigor and usefulness.
- **`RESPONSE_B`**: If B is noticeably superior.
- **`RESPONSE_C`**: If C is noticeably superior.
- **`TIE`**: If two or more responses share equivalent top quality.
- **`NONE_ACCEPTABLE`**: If all three responses contain dangerous methodological flaws or severe hallucinations.

---

## 5. Reviewer Workflow & Submission Options

### Option 1: Interactive Offline Review Portal (Recommended)
1. Open `viewer.html` in your web browser (Chrome, Firefox, Safari, Edge).
2. It runs 100% locally on your computer—no internet connection or server required.
3. Review cases sequentially. Your ratings are saved automatically to your local browser storage.
4. When finished (or during your review), click **"Export Scorecards JSON"** to download `{REVIEWER_ID}_submissions.json`.
5. Email or submit `{REVIEWER_ID}_submissions.json` to the study coordinator.

### Option 2: CSV Scorecard
1. Open `scorecard_template.csv` in Excel or Google Sheets.
2. Enter your scores (1–5) for each dimension and select your `pairwise_preference`.
3. Save as CSV and submit to the study coordinator.

---

## 6. Time Estimate & Fatigue Mitigation

- Each case scenario is concise (1–2 paragraphs of methodology description).
- Average review time per case is estimated at **3–5 minutes**.
- For a packet of 12–15 cases, total expected review duration is **45–75 minutes**.
- You do not need to complete all cases in one sitting; the `viewer.html` tool preserves your progress across sessions.

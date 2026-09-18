# BioReason v0.2 Human Evaluation Governance & Ethical Framework

**Document Version**: `v0.2.0`  
**Effective Date**: 2026-09-16  
**Scope**: Governance, Data Handling, Privacy, and Ethical Standards for External Scientific Evaluation

---

## 1. Nature of the Evaluation Study

- **Research Artifact Evaluation**: This study evaluates the methodological reasoning capabilities of AI language models on synthetic and de-identified published biological research scenarios.
- **Non-Clinical Disclaimer**: This evaluation is strictly for computational and statistical methodology research. It is **not** a clinical trial, medical device evaluation, or healthcare intervention. No patient care decisions, diagnostic claims, or clinical treatments are informed or made by this study.

---

## 2. Reviewer Anonymity & Data Protection

### Pseudonymous Data Storage
- All reviewer submissions, scorecards, and qualitative rationales are stored and processed using pseudonymous identifiers (e.g., `REV001`, `REV002`).
- No personal contact details, IP addresses, or direct identifiers are embedded in evaluation scorecards or published datasets.

### Collected Metadata
To enable stratified scientific analysis without compromising privacy, the study records only:
1. **Pseudonymous ID** (`REV001`, etc.)
2. **Qualification Tier** (`COMPUTATIONAL_BIOLOGIST`, `BIOSTATISTICIAN`, `BIOINFORMATICIAN`, `EXPERT_DOMAIN`, `GENERAL_BIOLOGICAL_SCIENTIST`)
3. **Research Experience Band** (`3-5_years`, `6-10_years`, `10+_years`)
4. **Domain Specialties** (e.g. `survival_analysis`, `single_cell_transcriptomics`)

---

## 3. Data Usage & Open Science

- **Evaluation Aggregation**: Review scores will be aggregated to compute pre-registered inter-rater agreement metrics (Krippendorff's $\alpha$, weighted $\kappa$), pairwise preference distributions, and multidimensional rubric statistics.
- **Reproducibility**: De-identified, frozen score files will be released with the open research package to ensure fully reproducible scientific auditing.
- **No Model Retraining During Evaluation**: Scores submitted during Phase 3 Increment 8 are strictly reserved for post-hoc validation; no model weights are modified or tuned against human scorecards.

---

## 4. Acknowledgment Policy

External reviewers contribute substantial scientific expertise to validating BioReason. Reviewers may choose their preferred acknowledgment status upon completing their review packet:

1. **Named Co-Author / Acknowledgment**: Listed by name and institutional affiliation in the research paper / technical report acknowledgments section.
2. **Anonymous Acknowledgment**: Acknowledged as an anonymous expert reviewer (e.g., *"We thank our panel of 8 independent computational biologists and biostatisticians..."*).
3. **No Acknowledgment**: Excluded from acknowledgment sections by request.

Acknowledgment preferences are tracked separately by the study coordinator and are completely unlinked from case-level ratings.

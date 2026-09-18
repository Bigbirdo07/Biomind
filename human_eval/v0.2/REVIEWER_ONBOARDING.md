# BioReason v0.2 External Scientific Reviewer Onboarding

Welcome to the independent scientific evaluation of **BioReason v0.2**. This document outlines everything you need to know to participate as an expert reviewer.

---

## 1. Study Purpose & Scope

BioReason is a specialized foundation model and critique system designed to evaluate biological and statistical methodology in computational biology, multi-omics, genomics, and clinical-style research.

The goal of this evaluation study is to measure the scientific fidelity, primary flaw prioritization, experimental unit awareness, and actionable remediation quality of automated critiques compared to baseline models and human scientific standards.

---

## 2. Reviewer Eligibility & Independence

### Eligibility
- Practicing computational biologists, biostatisticians, bioinformaticians, statistical geneticists, and wet-lab scientists with substantial experience in experimental design or data analysis.
- Experience with common design pitfalls (e.g. pseudoreplication, sample leakage, batch confounding, survival truncation, multiple testing).

### Scientific Independence
- All evaluations are conducted independently without collaboration between reviewers.
- You are encouraged to apply your own expert domain judgment and rigorous standards.
- Differences in statistical methodology philosophy (e.g., GEE vs LMM, permutation vs parametric) should be noted in the qualitative feedback box.

---

## 3. Double-Blinding Protocol

- Each case scenario presents three candidate critiques labeled **`RESPONSE_A`**, **`RESPONSE_B`**, and **`RESPONSE_C`**.
- Model identities (Canonical Qwen2.5-14B-Instruct, BioReason v0.1, BioReason v0.2) have been randomly assigned per case.
- You will not know which response corresponds to which model or training stage.
- Do not attempt to guess or de-anonymize the models; evaluate each purely on the scientific quality of its argument.

---

## 4. Your Reviewer Packet

Your individual reviewer packet is located at:
`human_eval/v0.2/reviewer_packets/{YOUR_REVIEWER_ID}/`

It contains:
1. **`viewer.html`**: A standalone, zero-dependency offline web interface for reading scenarios, reviewing responses side-by-side, scoring rubric dimensions, and exporting your scorecards.
2. **`assigned_cases.json`**: The complete text of your assigned cases and blinded responses in JSON format.
3. **`scorecard_template.csv`**: A spreadsheet template if you prefer scoring in Excel / Google Sheets.
4. **`REVIEWER_GUIDE.md`**: Complete rubric definitions, rating anchors (1–5), and edge-case instructions.

---

## 5. Step-by-Step Review Workflow

```mermaid
flowchart LR
    A["Open viewer.html"] --> B["Read Scenario & Question"]
    B --> C["Compare Responses A, B, C"]
    C --> D["Rate 10 Rubric Dimensions"]
    D --> E["Select Pairwise Preference"]
    E --> F["Add Qualitative Comments"]
    F --> G["Export JSON / CSV"]
    G --> H["Submit to Study Coordinator"]
```

1. **Open `viewer.html`** in any modern web browser.
2. **Read the scenario**: Note the biological objective, experimental hierarchy, sample sizes, and analytical workflow.
3. **Compare responses side-by-side**: Examine whether each response identifies the central vulnerability, avoids hallucinating non-existent flaws, and provides concrete remedies.
4. **Score the 10 standardized dimensions (1–5)**: Use the rating anchors in the Reviewer Guide.
5. **Select Pairwise Preference**: Choose which response you would prefer to receive as an investigator (`RESPONSE_A`, `RESPONSE_B`, `RESPONSE_C`, `TIE`, or `NONE_ACCEPTABLE`).
6. **Export your scorecards**: Click **"Export Scorecards JSON"** to save `{REVIEWER_ID}_submissions.json`.
7. **Submit**: Provide your completed file to the coordination team.

---

## 6. Time Commitment & Assistance

- **Workload**: 12–15 cases per reviewer.
- **Estimated Time**: ~3–5 minutes per case (~45–75 minutes total).
- **Session Continuity**: Progress is automatically saved locally in your browser storage so you can pause and resume at any time.

For questions regarding edge cases, contact the BioReason Study Coordination Team.

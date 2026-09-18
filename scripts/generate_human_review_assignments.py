#!/usr/bin/env python3
"""
scripts/generate_human_review_assignments.py

Generates balanced, deterministic reviewer assignments and reviewer packets
for BioReason v0.2 human external evaluation.

Governance Rules:
1. Every case receives at least 2 independent reviews.
2. High-severity and methodologically complex cases (longitudinal, confounding,
   survival, clinical-style, causal inference) receive 3 independent reviews (triple review).
3. No reviewer is assigned the same case more than once.
4. Reviewer workload is balanced (target: 12-16 cases per reviewer).
5. Reviewer expertise is matched to specialized domains where possible.
6. Absolute Blinding: No model names, checkpoint IDs, or randomization mappings
   are leaked into reviewer assignments, packets, or templates.
"""

import os
import json
import csv
import random
import argparse
from pathlib import Path
from typing import Dict, List, Any

DEFAULT_REVIEWER_POOL = [
    {
        "reviewer_id": "REV001",
        "qualification_tier": "BIOSTATISTICIAN",
        "domain_specialties": ["biostatistics", "survival_analysis", "longitudinal_omics"],
        "experience_band": "10+_years"
    },
    {
        "reviewer_id": "REV002",
        "qualification_tier": "COMPUTATIONAL_BIOLOGIST",
        "domain_specialties": ["single_cell_transcriptomics", "spatial_transcriptomics", "crispr_screens"],
        "experience_band": "6-10_years"
    },
    {
        "reviewer_id": "REV003",
        "qualification_tier": "BIOINFORMATICIAN",
        "domain_specialties": ["atac_seq", "gwas_genomics", "phylogenetics"],
        "experience_band": "6-10_years"
    },
    {
        "reviewer_id": "REV004",
        "qualification_tier": "EXPERT_DOMAIN",
        "domain_specialties": ["metabolomics", "proteomics", "experimental_design"],
        "experience_band": "10+_years"
    },
    {
        "reviewer_id": "REV005",
        "qualification_tier": "BIOSTATISTICIAN",
        "domain_specialties": ["biostatistics", "survival_analysis", "experimental_design"],
        "experience_band": "6-10_years"
    },
    {
        "reviewer_id": "REV006",
        "qualification_tier": "COMPUTATIONAL_BIOLOGIST",
        "domain_specialties": ["biological_ml", "variant_interpretation", "crispr_screens"],
        "experience_band": "3-5_years"
    },
    {
        "reviewer_id": "REV007",
        "qualification_tier": "GENERAL_BIOLOGICAL_SCIENTIST",
        "domain_specialties": ["microbiome", "experimental_design", "proteomics"],
        "experience_band": "6-10_years"
    },
    {
        "reviewer_id": "REV008",
        "qualification_tier": "BIOINFORMATICIAN",
        "domain_specialties": ["variant_interpretation", "gwas_genomics", "atac_seq"],
        "experience_band": "6-10_years"
    }
]

# Domains/types prioritized for triple-review
TRIPLE_REVIEW_DOMAINS = {
    "survival_analysis",
    "longitudinal_omics",
    "biostatistics",
    "variant_interpretation"
}

HTML_VIEWER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BioReason v0.2 External Review Portal - __REVIEWER_ID__</title>
<style>
  :root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: #1e293b;
    --border-color: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent: #38bdf8;
    --accent-hover: #0ea5e9;
    --success: #10b981;
    --warning: #f59e0b;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    margin: 0;
    padding: 24px;
    line-height: 1.5;
  }
  .container {
    max-width: 1200px;
    margin: 0 auto;
  }
  header {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    padding: 20px 24px;
    border-radius: 12px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  h1, h2, h3 { margin: 0 0 12px 0; }
  h1 { font-size: 22px; color: var(--accent); }
  .badge {
    background: #0284c7;
    color: white;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
  }
  .progress-container {
    background: #0f172a;
    border-radius: 8px;
    height: 12px;
    width: 250px;
    overflow: hidden;
    border: 1px solid var(--border-color);
    margin-top: 6px;
  }
  .progress-bar {
    background: var(--success);
    height: 100%;
    width: 0%;
    transition: width 0.3s ease;
  }
  .case-nav {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 24px;
  }
  .nav-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  .nav-btn.active {
    border-color: var(--accent);
    background: #0369a1;
  }
  .nav-btn.completed {
    border-color: var(--success);
    color: var(--success);
  }
  .card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
  }
  .scenario-box {
    background: #090d16;
    border-left: 4px solid var(--accent);
    padding: 16px;
    border-radius: 4px;
    margin: 16px 0;
    white-space: pre-wrap;
    font-size: 14px;
  }
  .response-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 16px;
  }
  @media (max-width: 900px) {
    .response-grid { grid-template-columns: 1fr; }
  }
  .response-card {
    background: #0f172a;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
  }
  .response-card h3 {
    color: var(--accent);
    font-size: 16px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
  }
  .response-text {
    flex: 1;
    font-size: 13px;
    white-space: pre-wrap;
    margin: 12px 0;
    max-height: 400px;
    overflow-y: auto;
    background: #090d16;
    padding: 12px;
    border-radius: 6px;
  }
  .rubric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 12px;
  }
  .rubric-row select {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 4px 6px;
    border-radius: 4px;
  }
  .decision-box {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
  }
  .form-group {
    margin-bottom: 16px;
  }
  .form-group label {
    display: block;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 6px;
  }
  select, textarea, input {
    background: #0f172a;
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    width: 100%;
    box-sizing: border-box;
  }
  textarea { height: 80px; resize: vertical; }
  .btn-bar {
    display: flex;
    justify-content: space-between;
    margin-top: 24px;
  }
  .btn {
    background: var(--accent);
    color: #0f172a;
    font-weight: 600;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
  }
  .btn:hover { background: var(--accent-hover); }
  .btn-secondary {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }
  .export-btn {
    background: var(--success);
    color: white;
  }
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>BioReason v0.2 Scientific Review Portal</h1>
      <div style="font-size: 13px; color: var(--text-secondary);">Reviewer: <strong>__REVIEWER_ID__</strong> (<span id="role-text">__ROLE__</span>)</div>
    </div>
    <div>
      <div style="font-size: 12px; text-align: right; margin-bottom: 4px;">Progress: <span id="progress-text">0 / 0</span></div>
      <div class="progress-container">
        <div class="progress-bar" id="progress-bar"></div>
      </div>
    </div>
  </header>

  <div class="case-nav" id="case-nav"></div>

  <div class="card" id="case-container">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2 id="case-title">Case Evaluation</h2>
      <span class="badge" id="case-domain">Domain</span>
    </div>
    <div class="scenario-box" id="scenario-text">Loading scenario...</div>
    <div style="font-size: 13px; color: var(--accent); font-weight: 600;" id="question-text"></div>

    <div class="response-grid">
      <div class="response-card" id="card-A">
        <h3>RESPONSE_A</h3>
        <div class="response-text" id="text-A"></div>
        <div id="rubric-A"></div>
      </div>
      <div class="response-card" id="card-B">
        <h3>RESPONSE_B</h3>
        <div class="response-text" id="text-B"></div>
        <div id="rubric-B"></div>
      </div>
      <div class="response-card" id="card-C">
        <h3>RESPONSE_C</h3>
        <div class="response-text" id="text-C"></div>
        <div id="rubric-C"></div>
      </div>
    </div>

    <div class="decision-box">
      <div class="form-group">
        <label>Overall Pairwise Scientist Preference:</label>
        <select id="pairwise-preference">
          <option value="">-- Select Preferred Response --</option>
          <option value="RESPONSE_A">RESPONSE_A is best</option>
          <option value="RESPONSE_B">RESPONSE_B is best</option>
          <option value="RESPONSE_C">RESPONSE_C is best</option>
          <option value="TIE">TIE (Equivalent Quality)</option>
          <option value="NONE_ACCEPTABLE">NONE_ACCEPTABLE (All Flawed/Misleading)</option>
        </select>
      </div>

      <div class="form-group">
        <label>Reviewer Confidence in Scientific Assessment:</label>
        <select id="reviewer-confidence">
          <option value="HIGH">HIGH (Certain of scientific mechanisms & methodology)</option>
          <option value="MEDIUM" selected>MEDIUM (Confident in assessment)</option>
          <option value="LOW">LOW (Subtle domain specifics outside primary area)</option>
        </select>
      </div>

      <div class="form-group">
        <label>Qualitative Rationale / Identified Strengths & Weaknesses (Optional):</label>
        <textarea id="qualitative-comments" placeholder="Note key flaws, overclaims, or why the chosen response is best..."></textarea>
      </div>
    </div>

    <div class="btn-bar">
      <button class="btn btn-secondary" id="prev-btn" onclick="prevCase()">← Previous Case</button>
      <div>
        <button class="btn btn-secondary" onclick="saveCurrentCase()">Save Case Review</button>
        <button class="btn export-btn" onclick="exportSubmissionsJSON()">Export Scorecards JSON</button>
      </div>
      <button class="btn" id="next-btn" onclick="nextCase()">Next Case →</button>
    </div>
  </div>
</div>

<script>
const ASSIGNED_CASES = __ASSIGNED_CASES_JSON__;
const REVIEWER_INFO = __REVIEWER_INFO_JSON__;
const RUBRIC_DIMS = [
  "SCIENTIFIC_CORRECTNESS",
  "PRIMARY_ISSUE_IDENTIFICATION",
  "EXPERIMENTAL_UNIT_REASONING",
  "STATISTICAL_VALIDITY",
  "BIOLOGICAL_PLAUSIBILITY",
  "CORRECTION_ACTIONABILITY",
  "UNCERTAINTY_CALIBRATION",
  "OVERCLAIMING",
  "FALSE_ALARM_BEHAVIOR",
  "OVERALL_SCIENTIFIC_USEFULNESS"
];

let currentIndex = 0;
let reviews = JSON.parse(localStorage.getItem('bioreason_reviews_' + REVIEWER_INFO.reviewer_id) || '{}');

function init() {
  buildNav();
  renderRubricSelectors();
  loadCase(0);
  updateProgress();
}

function buildNav() {
  const nav = document.getElementById('case-nav');
  nav.innerHTML = '';
  ASSIGNED_CASES.forEach((c, idx) => {
    const btn = document.createElement('button');
    btn.className = 'nav-btn' + (idx === currentIndex ? ' active' : '') + (reviews[c.case_id] ? ' completed' : '');
    btn.textContent = `${idx + 1}. ${c.case_id}`;
    btn.onclick = () => loadCase(idx);
    btn.id = 'nav-' + idx;
    nav.appendChild(btn);
  });
}

function renderRubricSelectors() {
  ['A', 'B', 'C'].forEach(letter => {
    const container = document.getElementById('rubric-' + letter);
    container.innerHTML = '';
    RUBRIC_DIMS.forEach(dim => {
      const row = document.createElement('div');
      row.className = 'rubric-row';
      const label = document.createElement('span');
      label.textContent = dim.replace(/_/g, ' ').toLowerCase();
      const select = document.createElement('select');
      select.id = `dim_${letter}_${dim}`;
      for (let i = 5; i >= 1; i--) {
        const opt = document.createElement('option');
        opt.value = i;
        opt.textContent = i + (i === 5 ? ' (Best)' : (i === 1 ? ' (Poor)' : ''));
        if (i === 3) opt.selected = true;
        select.appendChild(opt);
      }
      row.appendChild(label);
      row.appendChild(select);
      container.appendChild(row);
    });
  });
}

function loadCase(idx) {
  saveCurrentCase();
  currentIndex = idx;
  const c = ASSIGNED_CASES[idx];
  document.getElementById('case-title').textContent = `Case ${idx + 1} of ${ASSIGNED_CASES.length}: ${c.case_id}`;
  document.getElementById('case-domain').textContent = c.domain || 'General Biology';
  document.getElementById('scenario-text').textContent = c.scenario;
  document.getElementById('question-text').textContent = c.question || '';

  const resp = c.responses;
  document.getElementById('text-A').textContent = resp.RESPONSE_A;
  document.getElementById('text-B').textContent = resp.RESPONSE_B;
  document.getElementById('text-C').textContent = resp.RESPONSE_C;

  // Populate from saved review if present
  const saved = reviews[c.case_id];
  if (saved) {
    document.getElementById('pairwise-preference').value = saved.pairwise_preference || '';
    document.getElementById('reviewer-confidence').value = saved.reviewer_confidence || 'MEDIUM';
    document.getElementById('qualitative-comments').value = saved.comments || '';
    ['A', 'B', 'C'].forEach(letter => {
      const modelKey = 'RESPONSE_' + letter;
      if (saved.response_evaluations && saved.response_evaluations[modelKey]) {
        RUBRIC_DIMS.forEach(dim => {
          const val = saved.response_evaluations[modelKey][dim];
          if (val) document.getElementById(`dim_${letter}_${dim}`).value = val;
        });
      }
    });
  } else {
    document.getElementById('pairwise-preference').value = '';
    document.getElementById('reviewer-confidence').value = 'MEDIUM';
    document.getElementById('qualitative-comments').value = '';
    ['A', 'B', 'C'].forEach(letter => {
      RUBRIC_DIMS.forEach(dim => {
        document.getElementById(`dim_${letter}_${dim}`).value = 3;
      });
    });
  }

  // Update nav buttons
  ASSIGNED_CASES.forEach((_, i) => {
    const el = document.getElementById('nav-' + i);
    if (el) {
      el.className = 'nav-btn' + (i === currentIndex ? ' active' : '') + (reviews[ASSIGNED_CASES[i].case_id] ? ' completed' : '');
    }
  });

  document.getElementById('prev-btn').disabled = (idx === 0);
  document.getElementById('next-btn').disabled = (idx === ASSIGNED_CASES.length - 1);
  window.scrollTo(0, 0);
}

function saveCurrentCase() {
  if (currentIndex < 0 || currentIndex >= ASSIGNED_CASES.length) return;
  const c = ASSIGNED_CASES[currentIndex];
  const pref = document.getElementById('pairwise-preference').value;
  if (!pref) return; // Do not mark complete if preference not chosen

  const evalA = {}, evalB = {}, evalC = {};
  RUBRIC_DIMS.forEach(dim => {
    evalA[dim] = parseInt(document.getElementById(`dim_A_${dim}`).value, 10);
    evalB[dim] = parseInt(document.getElementById(`dim_B_${dim}`).value, 10);
    evalC[dim] = parseInt(document.getElementById(`dim_C_${dim}`).value, 10);
  });

  const record = {
    schema_version: "v0.2",
    reviewer_id: REVIEWER_INFO.reviewer_id,
    case_id: c.case_id,
    qualification_tier: REVIEWER_INFO.qualification_tier,
    reviewer_confidence: document.getElementById('reviewer-confidence').value,
    response_evaluations: {
      RESPONSE_A: evalA,
      RESPONSE_B: evalB,
      RESPONSE_C: evalC
    },
    pairwise_preference: pref,
    comments: document.getElementById('qualitative-comments').value,
    submitted_at: new Date().toISOString()
  };

  reviews[c.case_id] = record;
  localStorage.setItem('bioreason_reviews_' + REVIEWER_INFO.reviewer_id, JSON.stringify(reviews));
  updateProgress();
}

function updateProgress() {
  const completed = Object.keys(reviews).length;
  const total = ASSIGNED_CASES.length;
  document.getElementById('progress-text').textContent = `${completed} / ${total}`;
  const pct = Math.round((completed / total) * 100);
  document.getElementById('progress-bar').style.width = pct + '%';
}

function prevCase() {
  if (currentIndex > 0) loadCase(currentIndex - 1);
}

function nextCase() {
  if (currentIndex < ASSIGNED_CASES.length - 1) loadCase(currentIndex + 1);
}

function exportSubmissionsJSON() {
  saveCurrentCase();
  const records = Object.values(reviews);
  if (records.length === 0) {
    alert("No reviews completed yet.");
    return;
  }
  const blob = new Blob([JSON.stringify(records, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${REVIEWER_INFO.reviewer_id}_submissions.json`;
  a.click();
}

window.onload = init;
</script>
</body>
</html>
"""


def load_cases_and_responses(cases_path: str, responses_path: str) -> Dict[str, Dict[str, Any]]:
    """Loads cases and blinded responses and combines them into blinded case records."""
    cases = {}
    with open(cases_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                cases[item["case_id"]] = item

    with open(responses_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                cid = item["case_id"]
                if cid in cases:
                    cases[cid]["responses"] = item["responses"]

    return cases


def generate_assignments(
    cases_dict: Dict[str, Dict[str, Any]],
    reviewer_pool: List[Dict[str, Any]],
    seed: int = 42
) -> Dict[str, Any]:
    """
    Generates balanced, deterministic assignments ensuring:
    - Every case gets >= 2 reviews
    - Complex/high-priority cases get 3 reviews (triple review)
    - Reviewer capacity is balanced
    - Domain specialization is leveraged where possible
    """
    random.seed(seed)
    case_ids = sorted(list(cases_dict.keys()))

    # Categorize cases by target review count
    target_reviews = {}
    for cid in case_ids:
        domain = cases_dict[cid].get("domain", "")
        if domain in TRIPLE_REVIEW_DOMAINS or cid in ["HEVAL_001", "HEVAL_005", "HEVAL_010", "HEVAL_015", "HEVAL_020", "HEVAL_030", "HEVAL_040"]:
            target_reviews[cid] = 3
        else:
            target_reviews[cid] = 2

    total_needed_reviews = sum(target_reviews.values())
    n_reviewers = len(reviewer_pool)
    target_per_reviewer = total_needed_reviews // n_reviewers

    reviewer_assignments: Dict[str, List[str]] = {r["reviewer_id"]: [] for r in reviewer_pool}
    case_assigned_reviewers: Dict[str, List[str]] = {cid: [] for cid in case_ids}

    # Pass 1: Domain-specialist matching
    for cid in case_ids:
        domain = cases_dict[cid].get("domain", "")
        # Find matching specialists
        specialists = [
            r["reviewer_id"] for r in reviewer_pool
            if domain in r.get("domain_specialties", [])
        ]
        random.shuffle(specialists)
        for s_id in specialists:
            if len(case_assigned_reviewers[cid]) < target_reviews[cid] and len(reviewer_assignments[s_id]) < (target_per_reviewer + 3):
                if s_id not in case_assigned_reviewers[cid]:
                    case_assigned_reviewers[cid].append(s_id)
                    reviewer_assignments[s_id].append(cid)

    # Pass 2: Fill remaining required coverage balancing reviewer load
    for cid in case_ids:
        needed = target_reviews[cid] - len(case_assigned_reviewers[cid])
        if needed > 0:
            # Sort reviewers by current load ascending
            available = sorted(
                reviewer_pool,
                key=lambda r: (len(reviewer_assignments[r["reviewer_id"]]), random.random())
            )
            for r in available:
                r_id = r["reviewer_id"]
                if r_id not in case_assigned_reviewers[cid]:
                    case_assigned_reviewers[cid].append(r_id)
                    reviewer_assignments[r_id].append(cid)
                    needed -= 1
                    if needed == 0:
                        break

    # Build manifest
    manifest = {
        "assignment_manifest_version": "v0.2",
        "random_seed": seed,
        "total_cases": len(case_ids),
        "total_case_reviews_planned": sum(len(v) for v in reviewer_assignments.values()),
        "reviews_per_case_distribution": {
            "2_reviews": sum(1 for c, revs in case_assigned_reviewers.items() if len(revs) == 2),
            "3_reviews": sum(1 for c, revs in case_assigned_reviewers.items() if len(revs) == 3),
            "less_than_2": sum(1 for c, revs in case_assigned_reviewers.items() if len(revs) < 2)
        },
        "reviewers": reviewer_pool,
        "case_assignments": {cid: sorted(revs) for cid, revs in case_assigned_reviewers.items()},
        "reviewer_workload": {r_id: len(cases) for r_id, cases in reviewer_assignments.items()}
    }

    return manifest, reviewer_assignments


def create_csv_scorecard_template(output_path: Path, assigned_cases: List[Dict[str, Any]], reviewer_info: Dict[str, Any]):
    """Generates an offline CSV scorecard template for a reviewer."""
    dimensions = [
        "SCIENTIFIC_CORRECTNESS",
        "PRIMARY_ISSUE_IDENTIFICATION",
        "EXPERIMENTAL_UNIT_REASONING",
        "STATISTICAL_VALIDITY",
        "BIOLOGICAL_PLAUSIBILITY",
        "CORRECTION_ACTIONABILITY",
        "UNCERTAINTY_CALIBRATION",
        "OVERCLAIMING",
        "FALSE_ALARM_BEHAVIOR",
        "OVERALL_SCIENTIFIC_USEFULNESS"
    ]

    header = [
        "reviewer_id",
        "qualification_tier",
        "case_id",
        "domain",
        "pairwise_preference",
        "reviewer_confidence",
        "comments"
    ]
    for model in ["RESPONSE_A", "RESPONSE_B", "RESPONSE_C"]:
        for dim in dimensions:
            header.append(f"{model}_{dim}")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for c in assigned_cases:
            row = [
                reviewer_info["reviewer_id"],
                reviewer_info["qualification_tier"],
                c["case_id"],
                c.get("domain", ""),
                "", # pairwise_preference
                "MEDIUM", # confidence default
                "" # comments
            ]
            # default 3 for all rubric dimensions
            for _ in range(3 * len(dimensions)):
                row.append(3)
            writer.writerow(row)


def create_reviewer_packet(
    reviewer_info: Dict[str, Any],
    assigned_case_ids: List[str],
    cases_dict: Dict[str, Dict[str, Any]],
    output_dir: Path,
    guide_path: Path
):
    """Generates a standalone, self-contained reviewer packet."""
    packet_dir = output_dir / reviewer_info["reviewer_id"]
    packet_dir.mkdir(parents=True, exist_ok=True)

    assigned_cases = [cases_dict[cid] for cid in sorted(assigned_case_ids)]

    # 1. Write assigned cases JSON
    with open(packet_dir / "assigned_cases.json", "w", encoding="utf-8") as f:
        json.dump(assigned_cases, f, indent=2)

    # 2. Copy/link reviewer guide
    if guide_path.exists():
        guide_content = guide_path.read_text(encoding="utf-8")
        (packet_dir / "REVIEWER_GUIDE.md").write_text(guide_content, encoding="utf-8")

    # 3. Create CSV scorecard template
    create_csv_scorecard_template(packet_dir / "scorecard_template.csv", assigned_cases, reviewer_info)

    # 4. Create interactive standalone HTML Viewer
    html_content = (
        HTML_VIEWER_TEMPLATE
        .replace("__REVIEWER_ID__", reviewer_info["reviewer_id"])
        .replace("__ROLE__", reviewer_info["qualification_tier"])
        .replace("__ASSIGNED_CASES_JSON__", json.dumps(assigned_cases))
        .replace("__REVIEWER_INFO_JSON__", json.dumps(reviewer_info))
    )
    (packet_dir / "viewer.html").write_text(html_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate human review assignments and packets for BioReason v0.2.")
    parser.add_argument("--cases", default="human_eval/v0.2/cases.jsonl", help="Path to cases.jsonl")
    parser.add_argument("--responses", default="human_eval/v0.2/blinded_responses.jsonl", help="Path to blinded_responses.jsonl")
    parser.add_argument("--guide", default="human_eval/v0.2/REVIEWER_GUIDE.md", help="Path to REVIEWER_GUIDE.md")
    parser.add_argument("--assignments-dir", default="human_eval/v0.2/assignments", help="Output directory for assignments")
    parser.add_argument("--packets-dir", default="human_eval/v0.2/reviewer_packets", help="Output directory for reviewer packets")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for assignment generation")
    args = parser.parse_args()

    cases_dict = load_cases_and_responses(args.cases, args.responses)
    print(f"Loaded {len(cases_dict)} cases with responses.")

    assignments_dir = Path(args.assignments_dir)
    packets_dir = Path(args.packets_dir)
    assignments_dir.mkdir(parents=True, exist_ok=True)
    packets_dir.mkdir(parents=True, exist_ok=True)

    manifest, reviewer_assignments = generate_assignments(cases_dict, DEFAULT_REVIEWER_POOL, seed=args.seed)

    # Save manifest
    manifest_path = assignments_dir / "reviewer_assignment_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved assignment manifest to {manifest_path}")

    # Save individual assignments and packets
    guide_path = Path(args.guide)
    for reviewer_info in DEFAULT_REVIEWER_POOL:
        r_id = reviewer_info["reviewer_id"]
        c_ids = reviewer_assignments[r_id]

        # Individual assignment json
        with open(assignments_dir / f"{r_id}_assignments.json", "w", encoding="utf-8") as f:
            json.dump({
                "reviewer": reviewer_info,
                "assigned_case_count": len(c_ids),
                "assigned_cases": sorted(c_ids)
            }, f, indent=2)

        # Standalone packet
        create_reviewer_packet(reviewer_info, c_ids, cases_dict, packets_dir, guide_path)

    print(f"Generated packets for {len(DEFAULT_REVIEWER_POOL)} reviewers under {packets_dir}")
    print(f"Total reviews planned: {manifest['total_case_reviews_planned']}")
    print(f"Coverage: {manifest['reviews_per_case_distribution']}")


if __name__ == "__main__":
    main()

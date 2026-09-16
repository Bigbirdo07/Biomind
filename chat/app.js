/**
 * BioReason Chat — Core Application Logic
 * Modern, low-friction, privacy-preserving conversational UI
 */

const STORAGE_KEYS = {
  CHATS: 'bioreason_chats_v02',
  ACTIVE_CHAT: 'bioreason_active_chat_id',
  THEME: 'bioreason_theme_pref',
  DEV_MODE: 'bioreason_dev_mode_enabled',
  RESPONSE_MODE: 'bioreason_response_mode'
};

// Guided Pipeline Data Template for RNA-seq & Multi-Omics
const GUIDED_RNASEQ_PIPELINE = {
  is_pipeline: true,
  title: "Tumor vs. Normal RNA-seq Differential Expression & QC Pipeline",
  foundation: {
    experimental_unit: "Biological Patient / Specimen (N=12 Tumor vs N=12 Normal)",
    observation_unit: "Bulk Tissue Biopsy (24 Total Samples)",
    measurement_unit: "Illumina Paired-End RNA-seq (20,000 genes x 24 samples)",
    workflow_map: ["Raw Counts CSV", "QC Filtering (14.8k genes)", "Log1p Normalization", "PCA Loadings", "GroupKFold CV", "Results CSV"],
    shape_progression: [
      { step: "Raw Counts", shape: "20,000 x 24" },
      { step: "Filtered", shape: "14,827 x 24" },
      { step: "Transposed ML", shape: "24 x 14,827" },
      { step: "PCA Matrix", shape: "24 x 20 PCs" }
    ]
  },
  config_fields: [
    { key: "COUNTS_FILE", label: "Counts Matrix File", default: "data/counts.csv" },
    { key: "METADATA_FILE", label: "Sample Metadata File", default: "data/metadata.csv" },
    { key: "GROUP_COL", label: "Condition Column", default: "condition" },
    { key: "PATIENT_COL", label: "Subject / Patient Column", default: "patient_id" },
    { key: "OUTPUT_DIR", label: "Output Directory", default: "./results_rnaseq" },
    { key: "N_PCS", label: "Number of PCs", default: "20" }
  ],
  chunks: [
    {
      id: "chunk-1-config",
      title: "1. User Configuration & File Paths",
      code: `# ==============================================================================
# 1. USER CONFIGURATION — REPLACE WITH YOUR ACTUAL LOCAL/HPC FILE PATHS
# ==============================================================================
COUNTS_FILE = "__COUNTS_FILE__"        # REPLACE: Path to raw expression matrix
METADATA_FILE = "__METADATA_FILE__"    # REPLACE: Path to sample metadata
OUTPUT_DIR = "__OUTPUT_DIR__"            # Directory where results will be saved
GROUP_COL = "__GROUP_COL__"                    # Metadata column name for biological groups
PATIENT_COL = "__PATIENT_COL__"                 # Metadata column name for subject/patient IDs
N_PCS = __N_PCS__                                 # Number of Principal Components to compute`,
      guide: {
        what: "Top-level configuration variables defining file paths and experimental factors.",
        why: "Isolates all environment-specific file locations at the very top so you never need to search through code lines to adjust filenames.",
        data_in: "Local or cluster filesystem paths (.csv, .tsv, .txt).",
        data_out: "Validated configuration constants.",
        modify: "Replace 'data/counts.csv' with your absolute path (e.g. '/Users/alberto/data/counts.csv' on macOS or '/scratch/user/counts.csv' on HPC).",
        troubleshooting: "FileNotFoundError: Check that the file exists from your current working directory (verify using import os; print(os.getcwd()))."
      }
    },
    {
      id: "chunk-2-meta",
      title: "2. Metadata Loading & Alignment Checkpoint",
      code: `import os
import pandas as pd
import numpy as np

os.makedirs(OUTPUT_DIR, exist_ok=True)
metadata = pd.read_csv(METADATA_FILE, index_col=0)

print(f"[CHECKPOINT 1] Loaded metadata for {len(metadata)} samples.")
print(f"Biological groups detected: {metadata[GROUP_COL].value_counts().to_dict()}")

# Verify expected sample count and balance
assert len(metadata) >= 2, "Metadata must contain at least 2 samples."
assert GROUP_COL in metadata.columns, f"Column '{GROUP_COL}' missing in metadata header."`,
      guide: {
        what: "Loads sample annotations and validates column headers.",
        why: "Ensures experimental group labels and subject IDs are present before matrix loading.",
        data_in: "24 rows x 4 columns (sample_id, patient_id, condition, batch).",
        data_out: "Indexed pandas DataFrame.",
        assumptions: "Rows are sample IDs; group column contains distinct biological arms (e.g. Tumor vs Normal).",
        troubleshooting: "KeyError: Check for hidden spaces in your CSV column header names (e.g. 'condition ' vs 'condition')."
      }
    },
    {
      id: "chunk-3-filter",
      title: "3. Count Matrix Loading & Low-Count Filtering",
      code: `# Load count matrix (genes x samples)
counts = pd.read_csv(COUNTS_FILE, index_col=0)

# Critical Checkpoint: Matrix columns MUST align with metadata rows
assert list(counts.columns) == list(metadata.index), \\
    "Sample IDs in count matrix columns do not match metadata rows!"

# Filter out genes with < 10 counts in at least 6 samples (minimum group size)
min_count = 10
min_samples = 6
keep_genes = (counts >= min_count).sum(axis=1) >= min_samples
counts_filtered = counts.loc[keep_genes]

print(f"[SHAPE CHANGE] Raw Matrix: {counts.shape} -> Filtered: {counts_filtered.shape}")`,
      guide: {
        what: "Filters out unexpressed and low-abundance background transcripts.",
        why: "Transcripts with near-zero counts across all samples add statistical noise, increase multiple-testing penalties (FDR), and carry no differential biological signal.",
        bio_change: "Retains robustly transcribed genes (14,827 genes); removes 5,173 low-count background genes.",
        data_in: "20,000 genes x 24 samples.",
        data_out: "14,827 genes x 24 samples.",
        modify: "Change 'min_samples = 6' to match the sample size of your smallest biological group.",
        troubleshooting: "AssertionError: Count matrix column names do not match metadata sample_ids. Strip quotes or reorder columns."
      }
    },
    {
      id: "chunk-4-norm",
      title: "4. Log1p Transformation & Orientation Transpose",
      code: `# Log1p variance stabilization: y = log(1 + count)
# Transpose matrix to (samples x genes) for scikit-learn & downstream modeling
counts_norm = np.log1p(counts_filtered).T

print(f"[MATRIX ORIENTATION] Machine Learning Matrix: {counts_norm.shape} (samples x genes)")`,
      guide: {
        what: "Stabilizes count variance using y = log(1 + x) and transposes matrix orientation.",
        why: "Raw sequencing counts span multiple orders of magnitude with extreme positive skew. Log transformation compresses extreme counts while preserving zeros. Transposing produces rows=samples and cols=genes as required by Python modeling tools.",
        bio_change: "Reduces leverage of extreme outlier transcripts; makes variance approximately homoscedastic.",
        data_in: "14,827 genes x 24 samples.",
        data_out: "24 samples x 14,827 genes."
      }
    },
    {
      id: "chunk-5-pca",
      title: "5. PCA Dimensionality Reduction & Loading Inspection",
      code: `from sklearn.decomposition import PCA

pca = PCA(n_components=N_PCS, random_state=42)
X_pca = pca.fit_transform(counts_norm)

# Extract top driving genes (loadings) for PC1
pc1_loadings = pd.Series(pca.components_[0], index=counts_norm.columns)
top_pc1_genes = pc1_loadings.abs().sort_values(ascending=False).head(10)
print(f"Top 10 Genes Driving PC1 Variance:\\n{top_pc1_genes}")

# Save PCA coordinates & loadings to output folder
pca_df = pd.DataFrame(X_pca[:, :2], index=counts_norm.index, columns=['PC1', 'PC2'])
pca_df[GROUP_COL] = metadata[GROUP_COL]
pca_df.to_csv(os.path.join(OUTPUT_DIR, "pca_sample_scores.csv"))
pc1_loadings.to_csv(os.path.join(OUTPUT_DIR, "pca_gene_loadings.csv"))`,
      guide: {
        what: "Principal Component Analysis decomposes 14,827 gene dimensions into orthogonal variance axes.",
        why: "Visualizes global sample clustering and identifies which specific genes drive major variance across the cohort.",
        scores_vs_loadings: "Scores (X_pca) = where samples lie in 2D coordinate space. Loadings (pca.components_) = gene weights showing how strongly each gene contributes to PC1 = sum(w_i * G_i).",
        modify: "Change 'N_PCS = 20' to 10 or 50 depending on cohort size.",
        warning: "Do NOT fit PCA globally across all samples before cross-validation if using PCs as predictive machine learning features."
      }
    },
    {
      id: "chunk-6-cv",
      title: "6. Group-Aware Cross-Validation (Preventing Subject Leakage)",
      code: `from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

# Ensure subject-level split so biopsies from same patient never cross train/test
gkf = GroupKFold(n_splits=min(4, len(metadata[PATIENT_COL].unique())))
groups = metadata[PATIENT_COL]
y = (metadata[GROUP_COL] == metadata[GROUP_COL].unique()[0]).astype(int)

fold_aucs = []
for fold, (train_idx, test_idx) in enumerate(gkf.split(X_pca, y, groups=groups)):
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_pca[train_idx], y.iloc[train_idx])
    preds = clf.predict_proba(X_pca[test_idx])[:, 1]
    auc = roc_auc_score(y.iloc[test_idx], preds)
    fold_aucs.append(auc)
    print(f"Fold {fold+1} Holdout ROC-AUC: {auc:.3f}")

print(f"[VALIDATION COMPLETE] Mean Group-Aware ROC-AUC: {np.mean(fold_aucs):.3f}")`,
      guide: {
        what: "GroupKFold cross-validation splitting strictly by Patient / Subject ID.",
        why: "If multiple samples or timepoints exist per subject, standard random splitting leaks patient-specific genetic background across folds, producing artificially inflated 100% accuracy. GroupKFold guarantees genuine prospective generalization.",
        data_in: "24 samples with patient grouping.",
        data_out: "Unbiased generalization metrics."
      }
    }
  ]
};

// Domain knowledge base for conversational simulation
const DOMAIN_KNOWLEDGE = [
  {
    triggers: ['pipeline', 'guided', 'build guided', 'workflow script', 'deseq2 pipeline', 'rna-seq pipeline'],
    pipeline_data: GUIDED_RNASEQ_PIPELINE,
    response: `I have constructed a **Guided Pipeline** tailored to your RNA-seq experimental design.

### Pipeline Foundation:
- **Experimental Unit**: Patient / Biological Specimen ($N=12$ Tumor vs $N=12$ Normal)
- **Data Shape Progression**: $\\text{Raw Counts } (20,000 \\times 24) \\to \\text{Filtered } (14,827 \\times 24) \\to \\text{ML Matrix } (24 \\times 14,827) \\to \\text{PCA } (24 \\times 20)$
- **Workflow Stages**: Path Config $\\to$ Metadata QC $\\to$ Count Filtering $\\to$ Log1p $\\to$ PCA Loadings $\\to$ Group-Aware CV.

Below is your interactive two-pane **Code & Explanation Guide**. Click any section to inspect data transformations, assumptions, parameter modifications, and common troubleshooting solutions.`,
    audit: {
      experimental_unit: "Biological Patient (N=12 Tumor vs N=12 Normal)",
      primary_issue: "Complete Guided Pipeline with Group-Aware Validation and PCA Loadings Inspection",
      severity: "Valid / Best Practice",
      correction: "GroupKFold by patient_id + pre-split filtering + explicit PCA loadings extraction",
      confidence: "High (99%)"
    }
  },
  {
    triggers: ['mouse', 'mice', 'histological', 'slice', 't-test', 'section', 'pseudoreplication', 'n=60'],
    response: `Your study design exhibits **pseudoreplication** (experimental unit misalignment).

### Key Methodological Issues:
1. **Biological vs. Observational Units**: You have $N=12$ biological animals (6 per group), but $N=60$ histological section slices. Slices obtained from the same animal are non-independent technical observations that share animal-level physiological and batch variance.
2. **Artificially Inflated Degrees of Freedom**: Running a two-sample independent t-test with $df = 58$ assumes 60 independent biological events, which severely underestimates standard errors and produces an elevated false positive (Type I error) rate.

### Recommended Statistical Remediation:
- **Linear Mixed-Effects Model (LMM)**: Model mouse-level clustering with random intercepts:
  \`\`\`r
  library(lme4)
  model <- lmer(apoptotic_index ~ treatment + (1 | mouse_id), data = histology_data)
  summary(model)
  \`\`\`
- **Pre-analysis Aggregation**: Alternatively, compute the mean slice measurement per mouse ($N=6$ per group, $df = 10$) and conduct a standard two-sample $t$-test.`,
    audit: {
      experimental_unit: "Biological Mouse (N=6/group)",
      primary_issue: "Pseudoreplication (nested histological slices pooled as independent)",
      severity: "Critical",
      correction: "Linear Mixed-Effects Model with random mouse intercepts: lmer(index ~ tx + (1|mouse_id))",
      confidence: "High (98%)"
    }
  },
  {
    triggers: ['combat', 'batch', 'cell-level', 'split', 'normalize'],
    response: `Your RNA-seq preprocessing workflow contains **cross-validation data leakage**.

### Analysis of the Workflow:
1. **Preprocessing Leakage**: Performing ComBat batch correction or global normalization across the pooled dataset *before* splitting into train/test partitions exposes the test distribution to the training pipeline.
2. **Optimistic Bias**: In downstream classification or biomarker discovery, this causes severe over-optimistic performance estimation that fails on independent external cohorts.

### Recommended Correction:
- **Strict Partition-First Order**: Split your samples into training and validation sets *first*.
- Fit normalization and batch parameters strictly on the training set, and apply the learned transformations to the held-out test set:
  \`\`\`python
  from sklearn.model_selection import StratifiedKFold
  # Split raw counts first
  skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
  for train_idx, test_idx in skf.split(X_raw, y):
      X_train_norm = fit_transform_norm(X_raw[train_idx])
      X_test_norm = apply_norm(X_raw[test_idx], params=X_train_norm.params)
  \`\`\``,
    audit: {
      experimental_unit: "Biological Sample / Donor",
      primary_issue: "Data leakage via global pre-split batch correction and normalization",
      severity: "Critical",
      correction: "Encapsulate batch correction and scaling inside CV pipeline",
      confidence: "High (96%)"
    }
  },
  {
    triggers: ['feature selection', 'leak', 'machine learning', 'cross-validation', 'cv', 'entire dataset'],
    response: `Selecting features across the entire dataset prior to cross-validation is a classic form of **resampling leakage** (selection bias).

### Why This Flaw Occurs:
- When features (e.g. top differentially expressed genes) are ranked using all samples, information from the validation fold directly influences which features the model trains on.
- This produces near-perfect cross-validation accuracy ($>95\%$) that collapses when tested on true prospective data.

### Correct Implementation:
Perform feature filtering, differential expression ranking, and hyperparameter tuning **inside each cross-validation fold**:
\`\`\`python
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier

pipeline = Pipeline([
    ('select', SelectKBest(f_classif, k=50)),
    ('clf', RandomForestClassifier(random_state=42))
])
# Features are selected strictly on training split in each fold
scores = cross_val_score(pipeline, X, y, cv=5)
\`\`\``,
    audit: {
      experimental_unit: "Patient / Sample Cohort",
      primary_issue: "Resampling leakage via pre-split supervised feature selection",
      severity: "Critical",
      correction: "Embed SelectKBest / feature ranking strictly inside cross-validation folds",
      confidence: "High (99%)"
    }
  },
  {
    triggers: ['longitudinal', 'diabetic', 'mirna', 'hba1c', 'repeated', 'timepoints', 'ols'],
    response: `In a 5-year longitudinal cohort with 40 patients measured at 6 timepoints ($N=240$ total observations), the **experimental unit is the Patient**, while the visit is an observational repeated measure.

### Core Critique:
- **Autocorrelation & Sphericity**: Observations from the same patient across time are autocorrelated. Fitting an Ordinary Least Squares (OLS) model assumes independent identically distributed (i.i.d.) errors, which invalidates $p$-values and confidence intervals.
- **Between vs. Within-Subject Variance**: OLS conflates longitudinal within-subject change with cross-sectional baseline differences between subjects.

### Recommended Modeling:
Use a **Linear Mixed Model with random slopes or autoregressive correlation structure**:
\`\`\`r
library(nlme)
# Mixed model with AR(1) correlation for longitudinal visits
lme_fit <- lme(HbA1c ~ miR126 * time, random = ~ 1 | patient_id, 
               correlation = corAR1(form = ~ visit | patient_id), data = df)
summary(lme_fit)
\`\`\``,
    audit: {
      experimental_unit: "Patient (N=40, with 6 repeated measures per subject)",
      primary_issue: "Longitudinal dependence ignored by pooled OLS regression",
      severity: "Critical",
      correction: "Linear Mixed Model with random patient intercepts and AR(1) autocorrelation",
      confidence: "High (97%)"
    }
  }
];

// Default fallback response generator
function generateGeneralBiologicalResponse(prompt) {
  return {
    response: `Thank you for sharing this scientific methodology.

### Methodological Evaluation:
Based on your experimental description, here is a structured critique:
1. **Replication & Hierarchy**: Ensure that biological replicates (independent organisms/donors) are strictly distinguished from technical replicates (repeated assays, sequencing lanes, or culture wells).
2. **Confounding & Batch Controls**: Verify whether experimental batches align with biological treatment arms. If batch and condition are collinear, batch correction cannot separate technical noise from biological signal.
3. **Statistical Power & Multiplicity**: If testing multiple genes, metabolites, or operational taxonomic units (OTUs), apply Benjamini-Hochberg False Discovery Rate (FDR) control rather than unadjusted raw $p$-values.

Let me know if you would like me to draft an exact statistical model formula (e.g. in \`lme4\`, \`DESeq2\`, or \`scikit-learn\`) tailored to your specific assay!`,
    audit: {
      experimental_unit: "Biological Specimen / Donor",
      primary_issue: "General experimental design & multiplicity review",
      severity: "Minor / Advisory",
      correction: "Establish balanced block randomization and Benjamini-Hochberg FDR control",
      confidence: "Medium (88%)"
    }
  };
}

// App State
let appState = {
  chats: [],
  activeChatId: null,
  isGenerating: false,
  attachedFile: null,
  devMode: false,
  responseMode: 'conversational'
};

// DOM Elements
const elements = {
  sidebar: document.getElementById('sidebar'),
  btnCollapseSidebar: document.getElementById('btn-collapse-sidebar'),
  btnExpandSidebar: document.getElementById('btn-expand-sidebar'),
  btnNewChatSidebar: document.getElementById('btn-new-chat-sidebar'),
  btnTopNewChat: document.getElementById('btn-top-new-chat'),
  historyContainer: document.getElementById('history-items-container'),
  emptyState: document.getElementById('empty-state'),
  messagesContainer: document.getElementById('messages-container'),
  chatScrollArea: document.getElementById('chat-scroll-area'),
  chatInput: document.getElementById('chat-input'),
  btnSend: document.getElementById('btn-send'),
  btnStop: document.getElementById('btn-stop'),
  btnAttach: document.getElementById('btn-attach'),
  fileInput: document.getElementById('file-input'),
  attachmentPreview: document.getElementById('attachment-preview'),
  settingsModal: document.getElementById('settings-modal'),
  btnOpenSettingsSidebar: document.getElementById('btn-open-settings-sidebar'),
  btnOpenSettingsTop: document.getElementById('btn-open-settings-top'),
  btnCloseSettings: document.getElementById('btn-close-settings'),
  settingTheme: document.getElementById('setting-theme'),
  settingResponseMode: document.getElementById('setting-response-mode'),
  settingDevMode: document.getElementById('setting-dev-mode'),
  btnClearChats: document.getElementById('btn-clear-chats'),
  devDrawer: document.getElementById('dev-drawer'),
  btnToggleDev: document.getElementById('btn-toggle-dev'),
  btnCloseDev: document.getElementById('btn-close-dev'),
  devLatency: document.getElementById('dev-latency'),
  devTokens: document.getElementById('dev-tokens'),
  devJsonDisplay: document.getElementById('dev-json-display')
};

// Markdown Parser Helper
function formatMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks with syntax highlighting wrapper
  html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<div class="code-block-wrapper">
      <button class="btn-copy-code" onclick="copyCode(this)">Copy code</button>
      <pre><code class="language-${lang || 'plaintext'}">${code.trim()}</code></pre>
    </div>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');

  // Bold and Italics
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // LaTeX inline math formatting ($...$)
  html = html.replace(/\$([^$]+)\$/g, '<span style="font-family: serif; font-style: italic;">$1</span>');

  // Lists
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

  // Paragraphs
  html = html.split('\n\n').map(p => {
    if (p.startsWith('<h') || p.startsWith('<div') || p.startsWith('<ul>') || p.startsWith('<pre')) return p;
    return `<p>${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}

// Global copy helper
window.copyCode = function(button) {
  const code = button.parentElement.querySelector('code').textContent;
  navigator.clipboard.writeText(code).then(() => {
    button.textContent = 'Copied!';
    setTimeout(() => { button.textContent = 'Copy code'; }, 2000);
  });
};

window.copyMessageText = function(btn) {
  const row = btn.closest('.message-row');
  const text = row.querySelector('.assistant-body').textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>`;
    setTimeout(() => {
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
    }, 2000);
  });
};

window.toggleAudit = function(btn) {
  btn.classList.toggle('active');
  const card = btn.nextElementSibling;
  card.classList.toggle('open');
};

// Storage Operations
function loadState() {
  const savedChats = localStorage.getItem(STORAGE_KEYS.CHATS);
  appState.chats = savedChats ? JSON.parse(savedChats) : [];
  appState.activeChatId = localStorage.getItem(STORAGE_KEYS.ACTIVE_CHAT);
  
  const theme = localStorage.getItem(STORAGE_KEYS.THEME) || 'dark';
  applyTheme(theme);
  elements.settingTheme.value = theme;

  const devMode = localStorage.getItem(STORAGE_KEYS.DEV_MODE) === 'true';
  appState.devMode = devMode;
  elements.settingDevMode.checked = devMode;
  elements.btnToggleDev.style.display = devMode ? 'flex' : 'none';

  const respMode = localStorage.getItem(STORAGE_KEYS.RESPONSE_MODE) || 'conversational';
  appState.responseMode = respMode;
  elements.settingResponseMode.value = respMode;

  if (appState.chats.length === 0) {
    createNewChat();
  } else if (!appState.activeChatId || !appState.chats.find(c => c.id === appState.activeChatId)) {
    appState.activeChatId = appState.chats[0].id;
  }

  renderSidebarHistory();
  renderActiveChat();
}

function saveChats() {
  localStorage.setItem(STORAGE_KEYS.CHATS, JSON.stringify(appState.chats));
  localStorage.setItem(STORAGE_KEYS.ACTIVE_CHAT, appState.activeChatId);
}

function createNewChat() {
  const newChat = {
    id: 'chat_' + Date.now(),
    title: 'New Conversation',
    createdAt: new Date().toISOString(),
    messages: []
  };
  appState.chats.unshift(newChat);
  appState.activeChatId = newChat.id;
  saveChats();
  renderSidebarHistory();
  renderActiveChat();
  elements.chatInput.focus();
}

function deleteChat(chatId, event) {
  if (event) event.stopPropagation();
  appState.chats = appState.chats.filter(c => c.id !== chatId);
  if (appState.chats.length === 0) {
    createNewChat();
  } else if (appState.activeChatId === chatId) {
    appState.activeChatId = appState.chats[0].id;
  }
  saveChats();
  renderSidebarHistory();
  renderActiveChat();
}

function selectChat(chatId) {
  if (appState.activeChatId === chatId) return;
  appState.activeChatId = chatId;
  saveChats();
  renderSidebarHistory();
  renderActiveChat();
}

function applyTheme(theme) {
  if (theme === 'system') {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
  localStorage.setItem(STORAGE_KEYS.THEME, theme);
}

// UI Rendering
function renderSidebarHistory() {
  elements.historyContainer.innerHTML = '';
  appState.chats.forEach(chat => {
    const item = document.createElement('div');
    item.className = 'history-item' + (chat.id === appState.activeChatId ? ' active' : '');
    item.onclick = () => selectChat(chat.id);

    const title = document.createElement('span');
    title.className = 'history-title';
    title.textContent = chat.title || 'New Conversation';

    const actions = document.createElement('div');
    actions.className = 'history-actions';

    const btnDel = document.createElement('button');
    btnDel.className = 'btn-history-action';
    btnDel.title = 'Delete chat';
    btnDel.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`;
    btnDel.onclick = (e) => deleteChat(chat.id, e);

    actions.appendChild(btnDel);
    item.appendChild(title);
    item.appendChild(actions);
    elements.historyContainer.appendChild(item);
  });
}

function renderActiveChat() {
  const activeChat = appState.chats.find(c => c.id === appState.activeChatId);
  if (!activeChat || activeChat.messages.length === 0) {
    elements.emptyState.style.display = 'flex';
    elements.messagesContainer.style.display = 'none';
    elements.messagesContainer.innerHTML = '';
  } else {
    elements.emptyState.style.display = 'none';
    elements.messagesContainer.style.display = 'block';
    elements.messagesContainer.innerHTML = '';
    activeChat.messages.forEach(msg => renderMessageRow(msg, false));
    scrollToBottom();
  }
}

// Guided Pipeline HTML Generator
function renderGuidedPipelineHtml(pipeline, msgId) {
  const pId = 'pipe_' + msgId;
  window['pipeline_data_' + pId] = pipeline;

  let shapeHtml = pipeline.foundation.shape_progression.map((s, idx) => {
    return `<span class="shape-step">${s.step}: <strong>${s.shape}</strong></span>` +
      (idx < pipeline.foundation.shape_progression.length - 1 ? `<span class="shape-arrow">→</span>` : '');
  }).join(' ');

  let configFieldsHtml = pipeline.config_fields.map(f => {
    return `<div class="config-field">
      <label class="audit-item-label">${f.label}:</label>
      <input type="text" class="config-input" value="${f.default}" data-key="${f.key}" data-pipe="${pId}" oninput="updatePipelineConfig(this)">
    </div>`;
  }).join('');

  let codeChunksHtml = '';
  let guideCardsHtml = '';
  let fullScriptCode = '';

  pipeline.chunks.forEach((chunk, idx) => {
    let resolvedCode = chunk.code;
    pipeline.config_fields.forEach(f => {
      resolvedCode = resolvedCode.replaceAll(`__${f.key}__`, f.default);
    });

    fullScriptCode += `\n# --- ${chunk.title} ---\n` + resolvedCode + '\n';

    codeChunksHtml += `
      <div class="pipeline-chunk-wrapper ${idx === 0 ? 'active' : ''}" id="${pId}-code-${chunk.id}" onmouseenter="highlightPipelineChunk('${pId}', '${chunk.id}')" onclick="highlightPipelineChunk('${pId}', '${chunk.id}')">
        <div class="chunk-code-box">
          <div class="chunk-code-header">
            <span>${chunk.title}</span>
            <button class="btn-copy-code" style="position: static;" onclick="event.stopPropagation(); copyCode(this)">Copy Chunk</button>
          </div>
          ${chunk.id === 'chunk-1-config' ? `<div style="padding: 10px 12px; background: #101624; border-bottom: 1px solid var(--border-subtle);"><div class="audit-item-label" style="margin-bottom: 4px; color: var(--accent-secondary);">Fill-in-the-Blank Path Configuration:</div><div class="config-pill-grid">${configFieldsHtml}</div></div>` : ''}
          <pre class="chunk-code-body"><code>${resolvedCode}</code></pre>
        </div>
      </div>
    `;

    guideCardsHtml += `
      <div class="guide-chunk-card ${idx === 0 ? 'active' : ''}" id="${pId}-guide-${chunk.id}" onclick="highlightPipelineChunk('${pId}', '${chunk.id}')">
        <div class="guide-chunk-title">
          <span>${chunk.title}</span>
        </div>
        <div class="guide-meta-block">
          <strong>What is this?</strong> <span>${chunk.guide.what}</span>
        </div>
        <div class="guide-meta-block">
          <strong>Why are we doing this?</strong> <span>${chunk.guide.why}</span>
        </div>
        ${chunk.guide.bio_change ? `<div class="guide-meta-block"><strong>Biological Effect:</strong> <span>${chunk.guide.bio_change}</span></div>` : ''}
        ${chunk.guide.data_in ? `<div class="guide-meta-block"><strong>Data In:</strong> <span style="font-family: var(--font-mono);">${chunk.guide.data_in}</span> | <strong>Data Out:</strong> <span style="font-family: var(--font-mono);">${chunk.guide.data_out}</span></div>` : ''}
        ${chunk.guide.scores_vs_loadings ? `<div class="guide-box-callout"><strong>Scores vs. Loadings:</strong> ${chunk.guide.scores_vs_loadings}</div>` : ''}
        ${chunk.guide.modify ? `<div class="guide-box-callout"><strong>Safe User Customization:</strong> ${chunk.guide.modify}</div>` : ''}
        ${chunk.guide.warning ? `<div class="guide-box-callout warning"><strong>⚠️ Statistical Alert:</strong> ${chunk.guide.warning}</div>` : ''}
        ${chunk.guide.troubleshooting ? `
          <div class="guide-box-callout troubleshooting">
            <strong>Contextual Troubleshooting:</strong>
            <div>${chunk.guide.troubleshooting}</div>
          </div>` : ''}
      </div>
    `;
  });

  return `
    <div class="guided-pipeline-container" id="${pId}-container">
      <div class="pipeline-header">
        <div class="pipeline-title-row">
          <div style="font-weight: 700; font-size: 15px; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
            <span>${pipeline.title}</span>
            <span class="pipeline-badge">Guided Pipeline</span>
          </div>
          <button class="btn-copy-code" style="position: static;" onclick="downloadFullScript('${pId}')">Download Full .py</button>
        </div>
        
        <!-- Controls Bar -->
        <div class="pipeline-controls-bar">
          <div class="view-mode-tabs">
            <button class="tab-btn active" onclick="switchPipelineViewMode(this, 'split', '${pId}')">Split View (Code + Guide)</button>
            <button class="tab-btn" onclick="switchPipelineViewMode(this, 'step', '${pId}')">Step-by-Step</button>
            <button class="tab-btn" onclick="switchPipelineViewMode(this, 'full', '${pId}')">Full Script</button>
          </div>
          <div class="strictness-select-wrap">
            <span>Pedagogical Level:</span>
            <select class="app-select" onchange="switchStrictnessLevel(this.value, '${pId}')">
              <option value="standard">Standard</option>
              <option value="strict">Strict (Audit Warnings)</option>
              <option value="teaching" selected>Teaching (Bio to Code)</option>
            </select>
          </div>
        </div>

        <!-- Layer 1: Foundation Box -->
        <div class="pipeline-foundation-card">
          <div class="foundation-grid">
            <div class="foundation-item">
              <span class="foundation-label">Experimental Unit</span>
              <span class="foundation-val">${pipeline.foundation.experimental_unit}</span>
            </div>
            <div class="foundation-item">
              <span class="foundation-label">Observation Level</span>
              <span class="foundation-val">${pipeline.foundation.observation_unit}</span>
            </div>
            <div class="foundation-item">
              <span class="foundation-label">Assay & Design Matrix</span>
              <span class="foundation-val" style="font-size: 12px;">${pipeline.foundation.measurement_unit}</span>
            </div>
          </div>
          <div class="shape-tracker-row">
            <span class="foundation-label" style="margin-right: 6px;">Matrix Dimension Flow:</span>
            ${shapeHtml}
          </div>
        </div>
      </div>

      <!-- Layer 2 & 3: Two-Pane View -->
      <div class="pipeline-split-view" id="${pId}-split-view">
        <div class="code-pane" id="${pId}-code-pane">
          ${codeChunksHtml}
        </div>
        <div class="guide-pane" id="${pId}-guide-pane">
          ${guideCardsHtml}
        </div>
      </div>

      <!-- Step-by-Step Navigation Bar (Hidden in standard split) -->
      <div class="step-nav-bar" id="${pId}-step-nav" style="display: none;">
        <button class="btn-sidebar-toggle" style="border: 1px solid var(--border-subtle); padding: 6px 12px;" onclick="stepPipelineStage(-1, '${pId}')">← Previous Stage</button>
        <span id="${pId}-step-indicator" style="font-size: 13px; font-weight: 600; color: var(--accent-secondary);">Stage 1 of ${pipeline.chunks.length}</span>
        <button class="btn-sidebar-toggle" style="border: 1px solid var(--border-subtle); padding: 6px 12px; background: var(--bg-surface-hover);" onclick="stepPipelineStage(1, '${pId}')">Next Stage →</button>
      </div>

      <!-- Full Script View (Hidden by default) -->
      <div class="full-script-view" id="${pId}-full-script">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 12px; color: var(--text-muted);">Consolidated executable script with checkpoints:</span>
          <button class="btn-copy-code" style="position: static;" onclick="copyCode(this)">Copy Full Script</button>
        </div>
        <pre><code class="language-python" id="${pId}-full-code-text">${fullScriptCode}</code></pre>
      </div>
    </div>
  `;
}

// Global Interactivity Handlers for Guided Pipeline
window.highlightPipelineChunk = function(pId, chunkId) {
  const container = document.getElementById(`${pId}-container`);
  if (!container) return;

  container.querySelectorAll('.pipeline-chunk-wrapper').forEach(el => el.classList.remove('active'));
  container.querySelectorAll('.guide-chunk-card').forEach(el => el.classList.remove('active'));

  const codeEl = document.getElementById(`${pId}-code-${chunkId}`);
  const guideEl = document.getElementById(`${pId}-guide-${chunkId}`);

  if (codeEl) codeEl.classList.add('active');
  if (guideEl) {
    guideEl.classList.add('active');
    guideEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

window.switchPipelineViewMode = function(btn, mode, pId) {
  const container = document.getElementById(`${pId}-container`);
  if (!container) return;

  container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const splitView = document.getElementById(`${pId}-split-view`);
  const stepNav = document.getElementById(`${pId}-step-nav`);
  const fullScript = document.getElementById(`${pId}-full-script`);

  if (mode === 'split') {
    splitView.style.display = 'grid';
    stepNav.style.display = 'none';
    fullScript.style.display = 'none';
    container.querySelectorAll('.pipeline-chunk-wrapper').forEach(el => el.style.display = 'block');
    container.querySelectorAll('.guide-chunk-card').forEach(el => el.style.display = 'block');
  } else if (mode === 'step') {
    splitView.style.display = 'grid';
    stepNav.style.display = 'flex';
    fullScript.style.display = 'none';
    window[`${pId}_current_stage`] = 0;
    renderCurrentStage(pId, 0);
  } else if (mode === 'full') {
    splitView.style.display = 'none';
    stepNav.style.display = 'none';
    fullScript.style.display = 'block';
  }
};

function renderCurrentStage(pId, stageIdx) {
  const pipeline = window['pipeline_data_' + pId];
  if (!pipeline) return;

  const total = pipeline.chunks.length;
  const chunk = pipeline.chunks[stageIdx];

  const container = document.getElementById(`${pId}-container`);
  container.querySelectorAll('.pipeline-chunk-wrapper').forEach(el => el.style.display = 'none');
  container.querySelectorAll('.guide-chunk-card').forEach(el => el.style.display = 'none');

  const codeEl = document.getElementById(`${pId}-code-${chunk.id}`);
  const guideEl = document.getElementById(`${pId}-guide-${chunk.id}`);

  if (codeEl) { codeEl.style.display = 'block'; codeEl.classList.add('active'); }
  if (guideEl) { guideEl.style.display = 'block'; guideEl.classList.add('active'); }

  const indicator = document.getElementById(`${pId}-step-indicator`);
  if (indicator) indicator.textContent = `Stage ${stageIdx + 1} of ${total}: ${chunk.title}`;
}

window.stepPipelineStage = function(delta, pId) {
  const pipeline = window['pipeline_data_' + pId];
  if (!pipeline) return;

  let current = window[`${pId}_current_stage`] || 0;
  current = Math.max(0, Math.min(pipeline.chunks.length - 1, current + delta));
  window[`${pId}_current_stage`] = current;
  renderCurrentStage(pId, current);
};

window.updatePipelineConfig = function(input) {
  const key = input.getAttribute('data-key');
  const pId = input.getAttribute('data-pipe');
  const val = input.value.trim();

  const codeTextEl = document.querySelector(`#${pId}-code-chunk-1-config code`);
  if (codeTextEl) {
    let text = codeTextEl.textContent;
    // Replace variable assignment line
    const regex = new RegExp(`(${key}\\s*=\\s*)[^\\n#]+`, 'g');
    if (key === 'N_PCS') {
      text = text.replace(regex, `$1${val || 20}`);
    } else {
      text = text.replace(regex, `$1"${val}"`);
    }
    codeTextEl.textContent = text;
  }
};

window.downloadFullScript = function(pId) {
  const codeEl = document.getElementById(`${pId}-full-code-text`);
  if (!codeEl) return;
  const text = codeEl.textContent;
  const blob = new Blob([text], { type: 'text/x-python' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bioreason_pipeline.py';
  a.click();
};

window.switchStrictnessLevel = function(level, pId) {
  const container = document.getElementById(`${pId}-container`);
  if (!container) return;
  const warnings = container.querySelectorAll('.guide-box-callout.warning');
  if (level === 'strict') {
    warnings.forEach(w => w.style.boxShadow = '0 0 8px rgba(245, 158, 11, 0.4)');
  } else {
    warnings.forEach(w => w.style.boxShadow = 'none');
  }
};

function renderMessageRow(msg, isStreaming = false) {
  const row = document.createElement('div');
  row.className = `message-row ${msg.role}`;
  row.id = msg.id;

  if (msg.role === 'user') {
    const bubble = document.createElement('div');
    bubble.className = 'user-bubble';
    
    if (msg.attachmentName) {
      const badge = document.createElement('div');
      badge.className = 'attachment-pill';
      badge.style.marginBottom = '6px';
      badge.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg> <span>${msg.attachmentName}</span>`;
      bubble.appendChild(badge);
    }
    
    const textSpan = document.createElement('div');
    textSpan.textContent = msg.content;
    bubble.appendChild(textSpan);
    row.appendChild(bubble);
  } else {
    // Assistant message
    const avatar = document.createElement('div');
    avatar.className = 'assistant-avatar';
    avatar.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`;
    row.appendChild(avatar);

    const body = document.createElement('div');
    body.className = 'assistant-body';

    if (msg.guided_pipeline) {
      body.innerHTML = renderGuidedPipelineHtml(msg.guided_pipeline, msg.id);
    } else {
      body.innerHTML = formatMarkdown(msg.content);
    }
    row.appendChild(body);

    // Collapsible Scientific Audit Card
    if (msg.audit) {
      const auditWrapper = document.createElement('div');
      auditWrapper.className = 'scientific-audit-wrapper';
      auditWrapper.innerHTML = `
        <button class="btn-audit-toggle" onclick="toggleAudit(this)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <span>Scientific Audit &amp; Rigor Trace</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="chevron"><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <div class="audit-card">
          <div class="audit-grid">
            <div class="audit-item">
              <span class="audit-item-label">Experimental Unit</span>
              <span class="audit-item-val">${msg.audit.experimental_unit || 'Unspecified'}</span>
            </div>
            <div class="audit-item">
              <span class="audit-item-label">Sample Size &amp; Power</span>
              <span class="audit-item-val">${msg.audit.sample_size_check || 'Nominal'}</span>
            </div>
            <div class="audit-item">
              <span class="audit-item-label">Primary Issue / Flaw</span>
              <span class="audit-item-val" style="color: var(--accent-critique); font-weight: 600;">${msg.audit.primary_issue || 'None detected'}</span>
            </div>
            <div class="audit-item">
              <span class="audit-item-label">Recommended Remediation</span>
              <span class="audit-item-val">${msg.audit.recommended_remediation || 'Workflow scientifically sound.'}</span>
            </div>
          </div>
        </div>
      `;
      row.appendChild(auditWrapper);
    }

    // Message Actions Bar
    const actions = document.createElement('div');
    actions.className = 'message-actions';
    actions.innerHTML = `
      <button class="btn-action-icon" title="Copy response" onclick="copyMessageText(this)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
      <button class="btn-action-icon" title="Helpful" onclick="this.classList.toggle('active')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
      </button>
      <button class="btn-action-icon" title="Not helpful" onclick="this.classList.toggle('active')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"/></svg>
      </button>
    `;
    row.appendChild(actions);
  }

  elements.messagesContainer.appendChild(row);
}

function scrollToBottom() {
  elements.chatScrollArea.scrollTop = elements.chatScrollArea.scrollHeight;
}

// Generation & Dispatch
let streamInterval = null;

function handleSend() {
  const text = elements.chatInput.value.trim();
  if (!text || appState.isGenerating) return;

  const activeChat = appState.chats.find(c => c.id === appState.activeChatId);
  if (!activeChat) return;

  // Auto-title on first message
  if (activeChat.messages.length === 0) {
    activeChat.title = text.slice(0, 32) + (text.length > 32 ? '...' : '');
    renderSidebarHistory();
  }

  // 1. Append User Message
  const userMsg = {
    id: 'msg_' + Date.now(),
    role: 'user',
    content: text,
    attachmentName: appState.attachedFile ? appState.attachedFile.name : null,
    timestamp: new Date().toISOString()
  };
  activeChat.messages.push(userMsg);
  saveChats();

  // Clear inputs
  elements.chatInput.value = '';
  elements.chatInput.style.height = 'auto';
  elements.btnSend.disabled = true;
  clearAttachment();
  renderActiveChat();

  // 2. Select Response from Domain Knowledge
  const lower = text.toLowerCase();
  let selectedCritique = null;
  for (const item of DOMAIN_KNOWLEDGE) {
    if (item.triggers.some(t => lower.includes(t))) {
      selectedCritique = item;
      break;
    }
  }
  if (!selectedCritique) {
    selectedCritique = generateGeneralBiologicalResponse(text);
  }

  // 3. Start Simulated Streaming
  appState.isGenerating = true;
  elements.btnSend.style.display = 'none';
  elements.btnStop.style.display = 'flex';

  const assistantMsgId = 'msg_' + (Date.now() + 1);
  const targetResponse = selectedCritique.response;
  let currentLength = 0;
  const startTime = Date.now();

  // Create empty assistant row with typing indicator
  const assistantRow = document.createElement('div');
  assistantRow.className = 'message-row assistant';
  assistantRow.id = `msg-${assistantMsgId}`;
  assistantRow.innerHTML = `
    <div class="assistant-body">
      <div class="typing-indicator">
        <span>BioReason is reasoning</span>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  elements.messagesContainer.appendChild(assistantRow);
  scrollToBottom();

  const chunkSize = 12; // simulated tokens per tick
  streamInterval = setInterval(() => {
    currentLength += chunkSize;
    if (currentLength >= targetResponse.length) {
      currentLength = targetResponse.length;
      clearInterval(streamInterval);
      streamInterval = null;

      // Finalize message
      const latencyMs = Date.now() - startTime;
      const finalMsg = {
        id: assistantMsgId,
        role: 'assistant',
        content: targetResponse,
        audit: selectedCritique.audit,
        timestamp: new Date().toISOString(),
        latency: latencyMs
      };
      activeChat.messages.push(finalMsg);
      saveChats();

      appState.isGenerating = false;
      elements.btnSend.style.display = 'flex';
      elements.btnStop.style.display = 'none';
      elements.btnSend.disabled = false;

      // Update developer mode telemetry
      if (elements.devLatency) elements.devLatency.textContent = `${latencyMs} ms`;
      if (elements.devTokens) elements.devTokens.textContent = `${Math.round(text.length / 4)} / ${Math.round(targetResponse.length / 4)}`;
      if (elements.devJsonDisplay) {
        elements.devJsonDisplay.textContent = JSON.stringify({
          model: "BR-V02-DPO-001-A",
          latency_ms: latencyMs,
          critique: selectedCritique.audit
        }, null, 2);
      }

      renderActiveChat();
    } else {
      const partialText = targetResponse.slice(0, currentLength);
      assistantRow.querySelector('.assistant-body').innerHTML = formatMarkdown(partialText);
      scrollToBottom();
    }
  }, 25);
}

function handleStopGeneration() {
  if (streamInterval) {
    clearInterval(streamInterval);
    streamInterval = null;
  }
  appState.isGenerating = false;
  elements.btnSend.style.display = 'flex';
  elements.btnStop.style.display = 'none';
  elements.btnSend.disabled = elements.chatInput.value.trim().length === 0;
  saveChats();
  renderActiveChat();
}

function handleAttachment(file) {
  if (!file) return;
  appState.attachedFile = file;
  elements.attachmentPreview.style.display = 'flex';
  elements.attachmentPreview.innerHTML = `
    <div class="attachment-pill">
      <span>📄 ${file.name}</span>
      <button class="btn-remove-attachment" onclick="clearAttachment()">✕</button>
    </div>
  `;
}

window.clearAttachment = function() {
  appState.attachedFile = null;
  elements.attachmentPreview.style.display = 'none';
  elements.attachmentPreview.innerHTML = '';
  elements.fileInput.value = '';
};

// Event Listeners Initialization
function setupEventListeners() {
  // Input auto-resize & key bindings
  elements.chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    elements.btnSend.disabled = (this.value.trim().length === 0);
  });

  elements.chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  elements.btnSend.addEventListener('click', handleSend);
  elements.btnStop.addEventListener('click', handleStopGeneration);

  // New Chat buttons
  elements.btnNewChatSidebar.addEventListener('click', createNewChat);
  elements.btnTopNewChat.addEventListener('click', createNewChat);

  // Sidebar toggles
  elements.btnCollapseSidebar.addEventListener('click', () => {
    elements.sidebar.classList.add('collapsed');
    elements.btnExpandSidebar.style.display = 'flex';
  });

  elements.btnExpandSidebar.addEventListener('click', () => {
    elements.sidebar.classList.remove('collapsed');
    elements.btnExpandSidebar.style.display = 'none';
  });

  // Prompt chips
  document.querySelectorAll('.prompt-chip').forEach(chip => {
    chip.addEventListener('click', function() {
      const prompt = this.getAttribute('data-prompt');
      elements.chatInput.value = prompt;
      elements.chatInput.style.height = 'auto';
      elements.chatInput.style.height = (elements.chatInput.scrollHeight) + 'px';
      elements.btnSend.disabled = false;
      handleSend();
    });
  });

  // Attachments
  elements.btnAttach.addEventListener('click', () => elements.fileInput.click());
  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleAttachment(e.target.files[0]);
    }
  });

  // Settings Modal
  const openSettings = () => elements.settingsModal.classList.add('open');
  const closeSettings = () => elements.settingsModal.classList.remove('open');
  elements.btnOpenSettingsSidebar.addEventListener('click', openSettings);
  elements.btnOpenSettingsTop.addEventListener('click', openSettings);
  elements.btnCloseSettings.addEventListener('click', closeSettings);
  elements.settingsModal.addEventListener('click', (e) => {
    if (e.target === elements.settingsModal) closeSettings();
  });

  elements.settingTheme.addEventListener('change', (e) => applyTheme(e.target.value));

  elements.settingResponseMode.addEventListener('change', (e) => {
    appState.responseMode = e.target.value;
    localStorage.setItem(STORAGE_KEYS.RESPONSE_MODE, e.target.value);
    renderActiveChat();
  });

  elements.settingDevMode.addEventListener('change', (e) => {
    appState.devMode = e.target.checked;
    localStorage.setItem(STORAGE_KEYS.DEV_MODE, e.target.checked);
    elements.btnToggleDev.style.display = e.target.checked ? 'flex' : 'none';
    if (!e.target.checked) elements.devDrawer.classList.remove('open');
  });

  elements.btnClearChats.addEventListener('click', () => {
    if (confirm('Clear all conversation history? This cannot be undone.')) {
      appState.chats = [];
      localStorage.removeItem(STORAGE_KEYS.CHATS);
      localStorage.removeItem(STORAGE_KEYS.ACTIVE_CHAT);
      createNewChat();
      closeSettings();
    }
  });

  // Developer Drawer
  elements.btnToggleDev.addEventListener('click', () => {
    elements.devDrawer.classList.toggle('open');
  });
  elements.btnCloseDev.addEventListener('click', () => {
    elements.devDrawer.classList.remove('open');
  });
}

// Bootstrapping
window.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadState();
});

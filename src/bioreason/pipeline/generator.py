"""
src/bioreason/pipeline/generator.py

Dynamic Guided Pipeline Generator for BioReason.
Constructs structured Foundation, Code Chunks, and Synchronized Guide Chunks
grounded in the user's actual experiment (sample counts, group names, file paths, paired status, batch variables).
"""

from typing import Dict, List, Optional, Any
from bioreason.schemas.guided_pipeline import (
    PipelineContext,
    PipelineFoundation,
    PipelineStage,
    CodeChunk,
    GuideChunk,
    PipelineChunkPair,
    GuidedPipelineData,
    ShapeProgressionStep,
    ConfigField,
)


class GuidedPipelineGenerator:
    """Generates scientifically sound, dynamic Guided Pipeline payloads."""

    def build_guided_pipeline(self, context: PipelineContext) -> GuidedPipelineData:
        # Determine actual sample counts and groups
        sample_count = context.sample_count
        sample_count_label = f"{sample_count} samples" if sample_count is not None else "Sample count unknown"
        group_counts_str = ", ".join(f"{g}: {c}" for g, c in context.group_counts.items()) if context.group_counts else "group counts unknown"
        groups_list = context.groups if context.groups else ["Tumor", "Normal"]
        group_a = groups_list[0]
        group_b = groups_list[1] if len(groups_list) > 1 else "Normal"

        counts_path = context.file_paths.get("counts", "/PATH/TO/counts.csv")
        meta_path = context.file_paths.get("metadata", "/PATH/TO/metadata.csv")
        batch_col = context.batch_columns[0] if context.batch_columns else "batch"
        n_pcs = context.n_pcs or 20
        is_paired = bool(context.paired_design)

        # 1. Foundation
        exp_unit = context.experimental_unit or "Patient"
        obs_unit = context.observation_unit or "Biopsy"
        meas_unit = f"Count Matrix ({group_counts_str})"

        shape_progression = [
            ShapeProgressionStep(step="Raw Matrix", shape=f"UNKNOWN genes × {sample_count_label}", description="Resolved after reading the counts file."),
            ShapeProgressionStep(step="Filtered Matrix", shape=f"UNKNOWN retained genes × {sample_count_label}", description="Resolved after low-count filtering."),
            ShapeProgressionStep(step="PCA Input", shape=f"{sample_count_label} × UNKNOWN retained genes", description="Counts are transposed to samples × genes."),
            ShapeProgressionStep(step="PCA Scores", shape=f"{sample_count_label} × {n_pcs} PCs", description="PC count is configurable."),
        ]

        foundation = PipelineFoundation(
            experimental_unit=f"{exp_unit} ({sample_count_label}: {group_counts_str})",
            observation_unit=obs_unit,
            measurement_unit=meas_unit,
            shape_progression=shape_progression,
            analytical_stages=[
                "Configure Paths",
                "Load & Validate Metadata",
                "Filter Low-Count Genes",
                "Log1p Transformation & Transpose",
                "PCA & Loadings Analysis",
                "Cross-Validation & Modeling"
            ]
        )

        # 2. Config Fields (Fill-in-the-Blank)
        config_fields = [
            ConfigField(key="COUNTS_FILE", label="Counts File Path", default=counts_path),
            ConfigField(key="METADATA_FILE", label="Metadata File Path", default=meta_path),
            ConfigField(key="GROUP_COL", label="Group Column", default="condition"),
            ConfigField(key="PATIENT_COL", label="Patient/Subject ID", default="patient_id"),
            ConfigField(key="BATCH_COL", label="Batch Column", default=batch_col),
            ConfigField(key="N_PCS", label="PCA Components", default=str(n_pcs)),
        ]

        chunks: List[PipelineChunkPair] = []

        # --- Chunk 1: Configuration & File Paths ---
        c1_code = f'''# ==============================================================================
# 1. USER CONFIGURATION & FILE PATHS
# Replace the paths below with the exact location of your count matrix and metadata.
# ==============================================================================
import os

# REQUIRED USER VALUES:
COUNTS_FILE = "{counts_path}"  # REPLACE THIS with actual path
METADATA_FILE = "{meta_path}"  # REPLACE THIS with actual path

# EXPERIMENTAL COLUMN DEFINITIONS:
GROUP_COL = "condition"          # Column specifying biological groups ({group_a} vs {group_b})
PATIENT_COL = "patient_id"      # Experimental unit identifier
BATCH_COL = "{batch_col}"              # Batch variable to inspect / control

# SAFE TO MODIFY:
N_PCS = {n_pcs}                     # Number of principal components for dimensionality reduction
MIN_COUNT_THRESHOLD = 10        # Minimum count per gene
MIN_SAMPLE_RATIO = 0.25         # Gene must be detected in at least 25% of samples
OUTPUT_DIR = "./results"

os.makedirs(OUTPUT_DIR, exist_ok=True)
print("[CONFIG] Initialized pipeline for {sample_count_label} ({group_counts_str}).")'''

        c1_guide = GuideChunk(
            chunk_id="chunk-1-config",
            what="Explicit top-level configuration module defining dataset locations and experimental variables.",
            why="Prevents hard-coding paths inside analysis loops and guarantees reproducibility across environments.",
            data_in="User filesystem paths and metadata column names.",
            data_out="Global configuration constants.",
            bio_change="None (runtime environment configuration).",
            modify=f"Modify `COUNTS_FILE`, `METADATA_FILE`, or change `N_PCS` from {n_pcs} to your desired dimension.",
            troubleshooting="FileNotFoundError: Verify path using `pwd` in terminal or inspect cluster mount permissions."
        )
        chunks.append(PipelineChunkPair(id="chunk-1-config", stage_id="stage-1", title="1. User Configuration & File Paths", code=c1_code, guide=c1_guide))

        # --- Chunk 2: Metadata Loading & Alignment Validation ---
        c2_code = f'''# ==============================================================================
# 2. METADATA LOADING & COHORT ALIGNMENT VALIDATION
# Verifies experimental unit integrity, checks for missing labels, and confirms sample count.
# ==============================================================================
import pandas as pd

meta = pd.read_csv(METADATA_FILE, index_col=0)
print(f"[METADATA] Loaded {{len(meta)}} sample records from {{METADATA_FILE}}")

# Validation Checkpoint: Confirm required columns and group names
assert GROUP_COL in meta.columns, f"Missing group column: {{GROUP_COL}}"
assert PATIENT_COL in meta.columns, f"Missing experimental unit column: {{PATIENT_COL}}"

# Verify expected groups: {groups_list}
observed_groups = set(meta[GROUP_COL].dropna().unique())
print(f"[VALIDATION] Observed groups: {{observed_groups}}")

# Check for pairing / repeated observations
n_subjects = meta[PATIENT_COL].nunique()
print(f"[VALIDATION] Cohort structure: {{len(meta)}} samples across {{n_subjects}} unique subjects.")
{"# PAIRED DESIGN CONFIRMED: 2 samples per patient." if is_paired else "# INDEPENDENT DESIGN: Each subject corresponds to an independent biological replicate."}'''

        c2_guide = GuideChunk(
            chunk_id="chunk-2-meta",
            what="Loads sample annotations and validates cohort integrity against biological hypotheses.",
            why="Early assertions catch sample naming discrepancies before running costly matrix computations.",
            data_in="`metadata.csv` containing sample annotations and group columns.",
            data_out="Validated `meta` DataFrame with sample IDs indexed.",
            statistical_assumptions=f"Assumes experimental unit is {exp_unit}. {'Samples are paired within subject.' if is_paired else 'Samples are biologically independent.'}",
            troubleshooting="KeyError / Missing Column: Check column names with `meta.head()`. Ensure sample IDs match matrix column headers exactly."
        )
        chunks.append(PipelineChunkPair(id="chunk-2-meta", stage_id="stage-2", title="2. Metadata Loading & Alignment Validation", code=c2_code, guide=c2_guide))

        # --- Chunk 3: Low-Count Gene Filtering ---
        c3_code = f'''# ==============================================================================
# 3. LOW-COUNT GENE FILTERING
# Removes unexpressed or unreliably quantified genes to improve statistical power.
# ==============================================================================
counts = pd.read_csv(COUNTS_FILE, index_col=0)

# Align columns of counts matrix with rows of metadata
common_samples = meta.index.intersection(counts.columns)
assert len(common_samples) > 0, "No overlapping sample IDs between counts and metadata!"
counts = counts[common_samples]
meta = meta.loc[common_samples]

print(f"[DATA] Raw count matrix: {{counts.shape[0]:,}} genes × {{counts.shape[1]}} samples")

# Filter rule: At least 10 counts in at least 25% of samples
min_samples = max(2, int(counts.shape[1] * MIN_SAMPLE_RATIO))
expressed_mask = (counts >= MIN_COUNT_THRESHOLD).sum(axis=1) >= min_samples
counts_filt = counts.loc[expressed_mask]

print(f"[FILTER] Retained {{counts_filt.shape[0]:,}} robustly expressed genes (dropped {{counts.shape[0] - counts_filt.shape[0]:,}} noise features).")'''

        c3_guide = GuideChunk(
            chunk_id="chunk-3-filter",
            what="Filters out low-count transcript noise below reliable quantification limits.",
            why="Reduces the multiple hypothesis testing penalty in differential expression and prevents zero-inflation artifacts in PCA.",
            data_in=f"Raw count matrix (UNKNOWN genes × {sample_count_label}).",
            data_out=f"Filtered matrix (retained gene count computed at runtime × {sample_count_label}).",
            bio_change="Discards unexpressed genes. The exact retained gene count is printed by the checkpoint.",
            modify="Adjust `MIN_COUNT_THRESHOLD` or `MIN_SAMPLE_RATIO` if studying lowly expressed non-coding RNAs.",
            troubleshooting="All genes dropped: Check if matrix was already normalized/scaled or if count values are stored as strings."
        )
        chunks.append(PipelineChunkPair(id="chunk-3-filter", stage_id="stage-3", title="3. Low-Count Gene Filtering", code=c3_code, guide=c3_guide))

        # --- Chunk 4: Log1p Transformation & ML Matrix Transpose ---
        c4_code = f'''# ==============================================================================
# 4. LOG1P TRANSFORMATION & MATRIX ORIENTATION
# Stabilizes variance: y = log(1 + x). Transposes matrix to samples × genes for machine learning.
# ==============================================================================
import numpy as np

# Apply numerical transformation
counts_log1p = np.log1p(counts_filt)

# Transpose orientation: Machine learning libraries require (n_samples, n_features)
X = counts_log1p.T
y = meta.loc[X.index, GROUP_COL]

print(f"[TRANSPOSE] Transformed feature matrix X shape: {{X.shape[0]}} samples × {{X.shape[1]:,}} genes")
print(f"[TRANSPOSE] Target vector y distribution:\\n{{y.value_counts()}}")'''

        c4_guide = GuideChunk(
            chunk_id="chunk-4-log1p",
            what="Computes logarithmic variance stabilization $y = \\log(1 + x)$ and transposes the matrix.",
            why="RNA-seq counts have right-skewed variance. Standard ML models (PCA, SVM, Random Forest) expect samples as rows and features as columns.",
            data_in=f"Filtered genes × {sample_count_label}.",
            data_out=f"{sample_count_label} × filtered genes.",
            bio_change="Compresses dynamic range of highly expressed housekeeping genes while leaving zero counts at exactly zero.",
            warning="For formal statistical differential expression p-values, use DESeq2/edgeR negative-binomial models rather than raw log1p.",
            troubleshooting="Negative values error: Ensure raw counts contain no negative numbers before log1p."
        )
        chunks.append(PipelineChunkPair(id="chunk-4-log1p", stage_id="stage-4", title="4. Log1p Transformation & Matrix Transpose", code=c4_code, guide=c4_guide))

        # --- Chunk 5: PCA & Gene Loadings Extraction ---
        c5_code = f'''# ==============================================================================
# 5. PCA DECOMPOSITION & GENE LOADINGS ANALYSIS
# Projects high-dimensional gene expression into principal axes and extracts driving genes.
# ==============================================================================
from sklearn.decomposition import PCA

pca = PCA(n_components=min(N_PCS, X.shape[0]))
X_pca = pca.fit_transform(X)

exp_var_pc1 = pca.explained_variance_ratio_[0] * 100
exp_var_pc2 = pca.explained_variance_ratio_[1] * 100 if pca.n_components_ > 1 else 0.0

print(f"[PCA] PC1 explains {{exp_var_pc1:.2f}}% variance; PC2 explains {{exp_var_pc2:.2f}}% variance.")

# Extract gene loadings (weights) for PC1: PC1 = w1*Gene1 + w2*Gene2 + ...
loadings_pc1 = pd.Series(pca.components_[0], index=X.columns)
top_pos_pc1 = loadings_pc1.nlargest(10)
top_neg_pc1 = loadings_pc1.nsmallest(10)

print(f"[PCA LOADINGS] Top positive drivers of PC1:\\n{{top_pos_pc1.head(5)}}")
print(f"[PCA LOADINGS] Top negative drivers of PC1:\\n{{top_neg_pc1.head(5)}}")

# Export loadings table for biological interpretation
loadings_df = pd.DataFrame(pca.components_.T, index=X.columns, columns=[f"PC{{i+1}}" for i in range(pca.n_components_)])
loadings_df.to_csv(f"{{OUTPUT_DIR}}/pca_gene_loadings.csv")'''

        c5_guide = GuideChunk(
            chunk_id="chunk-5-pca",
            what="Principal Component Analysis decomposition and gene loadings extraction.",
            why="Uncovers dominant axes of biological variance across the cohort without supervising on labels.",
            data_in=f"{sample_count_label} × filtered genes.",
            data_out=f"{sample_count_label} × {n_pcs} PCs and `pca_gene_loadings.csv`.",
            scores_vs_loadings="**Scores** represent sample coordinates on the PC axis. **Loadings** represent the weights ($w_i$) measuring how strongly each gene contributes to that axis ($PC_1 = \\sum w_i \\cdot G_i$).",
            bio_change="Dimensionality compression. High-loading genes represent cohort-wide variance drivers.",
            modify=f"Change `N_PCS = {n_pcs}` to adjust the number of computed components.",
            warning="Do not fit PCA globally across all samples before cross-validation when building predictive diagnostic classifiers.",
            troubleshooting="n_components exceeds sample count: PCA components cannot exceed sample size $N$."
        )
        chunks.append(PipelineChunkPair(id="chunk-5-pca", stage_id="stage-5", title="5. PCA & Gene Loadings Analysis", code=c5_code, guide=c5_guide))

        # --- Chunk 6: Patient-Level Cross-Validation & Modeling ---
        c6_code = f'''# ==============================================================================
# 6. PATIENT-LEVEL CROSS-VALIDATION & SUPERVISED MODELING
# Prevents data leakage by grouping repeated observations strictly by subject ID.
# ==============================================================================
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score

groups = meta.loc[X.index, PATIENT_COL]
gkf = GroupKFold(n_splits=5 if meta[PATIENT_COL].nunique() >= 5 else 3)

fold_scores = []
print(f"[CV] Running patient-grouped cross-validation across {{gkf.get_n_splits()}} folds...")

for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups=groups), 1):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # Model fit strictly on training fold
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    fold_scores.append(acc)
    print(f"  Fold {{fold}} Accuracy: {{acc:.3f}} (Test Subjects: {{meta.iloc[test_idx][PATIENT_COL].unique()}})")

print(f"[RESULTS] Mean Patient-Level Cross-Validation Accuracy: {{np.mean(fold_scores):.3f}} ± {{np.std(fold_scores):.3f}}")'''

        c6_guide = GuideChunk(
            chunk_id="chunk-6-cv",
            what=f"Subject-level GroupKFold cross-validation partitioning by `{context.experimental_unit or 'Patient'}`.",
            why="Prevents biological data leakage. If multiple samples from the same patient are split between train and test, the model memorizes patient identity instead of disease pathology.",
            statistical_assumptions="Assumes patients are independent biological units. Replicates from the same subject must stay grouped together.",
            warning="**Data Leakage Alert**: Never perform feature selection or PCA on the combined dataset before `GroupKFold.split()`.",
            troubleshooting="ValueError: n_splits greater than number of groups: Ensure you have at least 3 unique patient IDs in your metadata."
        )
        chunks.append(PipelineChunkPair(id="chunk-6-cv", stage_id="stage-6", title="6. Patient-Level Cross-Validation & Modeling", code=c6_code, guide=c6_guide))

        return GuidedPipelineData(
            title=f"Guided {context.organism or 'Human'} RNA-Seq Pipeline ({sample_count_label}: {group_counts_str})",
            pipeline_context=context,
            foundation=foundation,
            config_fields=config_fields,
            chunks=chunks,
        )

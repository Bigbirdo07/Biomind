"""
src/bioreason/pipeline/file_inspector.py

Inspects user-uploaded metadata or count matrix files to extract:
- Column names
- Dimensions
- Sample IDs
- Group candidate columns
- Possible matrix orientation
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd


class FileInspector:
    """Inspects small CSV/TSV data files to extract experimental structure."""

    @staticmethod
    def inspect_file(file_path: str) -> Dict[str, Any]:
        p = Path(file_path)
        if not p.exists():
            return {"error": f"File not found: {file_path}"}

        try:
            sep = "\t" if p.suffix.lower() in [".tsv", ".txt"] else ","
            df_head = pd.read_csv(p, sep=sep, nrows=5, index_col=0)
            
            # Read line count for total rows estimate
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                total_lines = sum(1 for _ in f)

            total_rows = max(0, total_lines - 1)
            total_cols = len(df_head.columns)

            # Determine likely orientation
            is_count_matrix = False
            is_metadata = False

            if total_rows > 1000 and total_cols < 500:
                is_count_matrix = True
                orientation = "genes_x_samples (rows=genes, cols=samples)"
            elif total_rows < 500 and total_cols < 50:
                is_metadata = True
                orientation = "samples_x_annotations"
            else:
                orientation = "unknown"

            # Check for candidate group columns
            group_candidates = []
            for col in df_head.columns:
                col_lower = str(col).lower()
                if any(k in col_lower for k in ["group", "condition", "treatment", "phenotype", "status", "diagnosis", "batch", "patient"]):
                    group_candidates.append(str(col))

            return {
                "file_name": p.name,
                "file_path": str(p.resolve()),
                "estimated_rows": total_rows,
                "columns": list(df_head.columns),
                "sample_ids_sample": list(df_head.index[:5]),
                "orientation": orientation,
                "is_count_matrix": is_count_matrix,
                "is_metadata": is_metadata,
                "group_candidates": group_candidates
            }
        except Exception as e:
            return {"error": f"Failed to inspect file: {str(e)}"}

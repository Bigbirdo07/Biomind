# Dataset Schema Specification

BioReason replaces unstructured chain-of-thought with structured scientific decision records. Every training episode adheres to the `ScientificReasoningEpisode` schema.

---

## Schema Structure

```json
{
  "episode_id": "EP_001_SCRNA_PSEUDOREPLICATION",
  "domain": "single_cell_transcriptomics",
  "question": "Research question or proposed analysis scenario",
  
  "experiment": {
    "organism": "Mus musculus",
    "assay": "scrna_seq",
    "experimental_unit": "animal",
    "samples": 2,
    "total_observations": 70000,
    "groups": [
      {"name": "Diseased", "sample_count": 1, "cell_count": 40000},
      {"name": "Healthy", "sample_count": 1, "cell_count": 30000}
    ],
    "covariates": ["sequencing_depth", "mitochondrial_percent"],
    "batch_structure": {
      "batch_variable": "run_date",
      "batch_count": 2,
      "confounded_with_group": true
    },
    "input_data_type": "raw_counts",
    "objective": "differential_expression"
  },
  
  "proposed_analysis": "Description of proposed or flawed workflow",
  
  "scientific_checks": {
    "replication_valid": false,
    "confounding_detected": true,
    "leakage_detected": false,
    "transformation_valid": false,
    "multiple_testing_controlled": false,
    "sample_size_adequate": false
  },
  
  "preferred_analysis": "Statistically and biologically valid correction",
  "reasoning_summary": "Concise scientific rationale",
  
  "interpretation": {
    "supported_claims": [
      {"statement": "...", "level": "OBSERVATION"}
    ],
    "unsupported_claims": [
      {"statement": "...", "level": "BIOLOGICAL_INTERPRETATION"}
    ],
    "limitations": ["..."]
  },
  
  "validation_status": "expert_validated",
  "sources": ["DOI or citation"]
}
```

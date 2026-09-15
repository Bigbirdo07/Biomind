# BioReason Open-Weight Model Licensing & Governance Audit

This document records the exact licensing terms, redistribution constraints, commercial permissions, and attribution requirements for all candidate foundation models evaluated in the BioReason benchmark baseline and targeted for future specialization.

---

## 1. Candidate Baseline Models Inventory

### Model A: Qwen2.5-7B-Instruct / Qwen2.5-14B-Instruct / Qwen2.5-32B-Instruct
- **Developer / Organization**: Alibaba Cloud (Qwen Team)
- **Hugging Face Repositories**:
  - `Qwen/Qwen2.5-7B-Instruct`
  - `Qwen/Qwen2.5-14B-Instruct`
  - `Qwen/Qwen2.5-32B-Instruct`
- **License**: **Apache 2.0** (for 7B, 14B, and 32B base and instruct variants)
- **Commercial Use**: **Permitted** without monthly active user restrictions.
- **Redistribution Constraints**: Standard Apache 2.0 notice and disclaimer preservation.
- **Modification & Derivative Works**: Permitted; fine-tuned weights and adaptations may be distributed under Apache 2.0.
- **Attribution Requirement**: Include copyright notice: `Copyright (c) Alibaba Group. Licensed under Apache 2.0.`

---

### Model B: Meta-Llama-3.1-8B-Instruct / Meta-Llama-3.1-70B-Instruct
- **Developer / Organization**: Meta AI Research
- **Hugging Face Repositories**:
  - `meta-llama/Meta-Llama-3.1-8B-Instruct`
  - `meta-llama/Meta-Llama-3.1-70B-Instruct`
- **License**: **Llama 3.1 Community License Agreement**
- **Commercial Use**: Permitted for entities with fewer than 700 million monthly active users (MAU) in the preceding calendar month.
- **Redistribution Constraints**: Must retain "Built with Llama 3.1" attribution. Prohibits using Llama 3.1 outputs to train other models except derivatives of Llama 3.1.
- **Modification & Derivative Works**: Permitted under Llama 3.1 license terms.
- **Attribution Requirement**: Prominently display "Built with Llama 3.1" in user-facing documentation and derived artifacts.

---

### Model C: Mistral-7B-Instruct-v0.3 / Mistral-Nemo-Instruct-2407 (12B)
- **Developer / Organization**: Mistral AI / NVIDIA
- **Hugging Face Repositories**:
  - `mistralai/Mistral-7B-Instruct-v0.3`
  - `mistralai/Mistral-Nemo-Instruct-2407`
- **License**: **Apache 2.0**
- **Commercial Use**: **Permitted** without commercial restrictions.
- **Redistribution Constraints**: Standard Apache 2.0 license file and attribution notice.
- **Modification & Derivative Works**: Permitted; fully compatible with open research and commercial deployment.
- **Attribution Requirement**: Include Mistral AI and NVIDIA Apache 2.0 copyright notices.

---

### Model D: Gemma-2-9B-It / Gemma-2-27B-It
- **Developer / Organization**: Google DeepMind
- **Hugging Face Repositories**:
  - `google/gemma-2-9b-it`
  - `google/gemma-2-27b-it`
- **License**: **Gemma Terms of Use (Open Access)**
- **Commercial Use**: **Permitted** subject to Google Gemma Prohibited Use Policy.
- **Redistribution Constraints**: Must distribute license and notice file.
- **Modification & Derivative Works**: Permitted.
- **Attribution Requirement**: Attribution to Google Gemma required.

---

## 2. Compliance Summary Matrix

| Model Family | Parameter Class | License | Commercial Permitted? | Synthetic Output Training Restrictions? | BioReason Phase 2 Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5** | 7B, 14B, 32B | Apache 2.0 | **Yes (Full)** | **None (Apache 2.0)** | **Highest (Fully Open & Unrestricted)** |
| **Mistral / Nemo** | 7B, 12B | Apache 2.0 | **Yes (Full)** | **None (Apache 2.0)** | **High (Permissive Apache 2.0)** |
| **Llama-3.1** | 8B, 70B | Llama 3.1 Community | Yes (<700M MAU) | Prohibits training non-Llama models | Moderate (Self-contained fine-tuning only) |
| **Gemma-2** | 9B, 27B | Gemma Terms | Yes | Must comply with Use Policy | High (Permissive Open Terms) |

---

## 3. Governance Conclusion for BioReason Foundation
Due to unrestricted Apache 2.0 licensing, robust multilingual/mathematical/coding representations, and complete freedom to distribute specialized fine-tuned weights without restrictive downstream clauses, the **Qwen2.5 family (7B / 14B / 32B)** and **Mistral-Nemo (12B)** represent the optimal open foundation models for BioReason Phase 2 specialization.

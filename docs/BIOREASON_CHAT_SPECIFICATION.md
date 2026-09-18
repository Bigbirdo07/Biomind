# BioReason Chat Interface Specification

**Version**: `v0.2.0`  
**Focus**: Conversational-First Minimalist AI Scientific Assistant  
**Design Philosophy**: "Chat Product First — Scientific Complexity Underneath"

---

## 1. Primary Design Principles

1. **Conversational First**: BioReason looks and behaves like a clean, modern, intuitive conversational assistant (familiar to users of ChatGPT, Claude, and Gemini).
2. **Understated Scientific Power**: Scientific complexity, formal experiment graphs, and deep methodology audits exist underneath the interface and are accessible on demand, without cluttering the primary conversation.
3. **Zero Setup Friction**: The user opens the application and immediately starts chatting. No complex configuration forms, dashboards, or developer controls clutter the default experience.
4. **Local Privacy by Default**: All conversation history and settings are stored locally in the user's browser. Zero training capture, zero telemetry, and zero unconsented data transmission.

---

## 2. Layout & Visual Structure

```
+------------------------------------------------------------------------------------+
| [Sidebar Toggle] BioReason v0.2 • Ready                         [Settings] [Dev]   |
+-------------------+----------------------------------------------------------------+
|                   |                                                                |
| [ + New Chat ]    |                     (Empty State / Conversation)               |
|                   |                                                                |
| Recent            |   User: Is my longitudinal miRNA analysis valid with OLS?      |
| • miRNA design    |                                                                |
| • Single-cell QC  |   BioReason:                                                       |
| • Survival bias   |   Your study has repeated measures from 40 patients over time.     |
|                   |   Fitting an ordinary least squares (OLS) linear model pools all   |
|                   |   N=240 observations, ignoring intra-patient correlation.          |
|                   |                                                                |
|                   |   [ > Scientific audit ]  [Copy] [Thumbs Up] [Thumbs Down]         |
|                   |                                                                |
|                   |   +--------------------------------------------------------+   |
|                   |   | [📎] Ask BioReason about your scientific design... [ ↑ ]|   |
| [ ⚙ Settings ]    |   +--------------------------------------------------------+   |
+-------------------+----------------------------------------------------------------+
```

### Component Hierarchy
- **Region 1: Collapsible Left Sidebar (260px)**
  - BioReason wordmark & emblem
  - Prominent "New chat" button (`Ctrl/Cmd + K` or `+`)
  - Chronological chat history list (localStorage-backed with delete & rename)
  - Bottom Settings trigger
- **Region 2: Top Bar**
  - Sidebar collapse/expand toggle
  - Minimal model indicator: `BioReason v0.2 • Ready`
  - Quick action controls (New chat, Settings, Developer Mode toggle)
- **Region 3: Centered Conversation Stream (max-width: 760px)**
  - User messages: Clean, subtle filled pill aligned to the right or standard conversational block.
  - Assistant messages: High-legibility typography with full Markdown support (lists, tables, code blocks with copy button, inline code).
  - **Collapsible Scientific Audit**: A subtle `🔬 Scientific audit` toggle that smoothly reveals structured fields (Experimental Unit, Primary Issue, Severity, Recommended Correction, and Confidence) without exposing internal chain-of-thought.
  - Message action bar: Copy, Helpful, Not Helpful, Scientific Audit toggle.
- **Region 4: Sticky Bottom Composer**
  - Centered floating rounded rectangle with subtle shadow and border.
  - Multiline auto-expanding textarea (Shift+Enter for newline, Enter to send).
  - Attachment button (`.txt`, `.md`, `.csv`, code files).
  - Send button (up-arrow circle, enabled when text is present) / Stop button during generation.
  - Minimal disclaimer text.

---

## 3. Visual Styling & Color System

- **Typography**: Clean modern system font stack (`Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `sans-serif`).
- **Color Palettes**:
  - **Dark Mode (Default/System)**:
    - Primary Background: `#0f172a` (slate-900)
    - Sidebar Background: `#090d16` (slate-950)
    - Card / Pill Background: `#1e293b` (slate-800)
    - Borders: `#334155` (slate-700)
    - Text Primary: `#f8fafc` (slate-50)
    - Text Secondary: `#94a3b8` (slate-400)
    - Accent: `#10b981` (emerald-500) / `#38bdf8` (sky-400)
  - **Light Mode**:
    - Primary Background: `#ffffff`
    - Sidebar Background: `#f8fafc`
    - Card / Pill Background: `#f1f5f9`
    - Borders: `#e2e8f0`
    - Text Primary: `#0f172a`
    - Text Secondary: `#64748b`
    - Accent: `#059669` / `#0284c7`

---

## 4. Scientific Audit Component Specifications

The Scientific Audit provides structured methodology breakdown without cluttering normal conversation:

| Field | Description | Example |
| :--- | :--- | :--- |
| **Experimental Unit** | Biological vs observational replication level | `Patient / Donor (N=40)` |
| **Primary Issue** | Core methodological or statistical vulnerability | `Repeated measures pseudoreplication` |
| **Severity Level** | Scientific impact score (`Critical`, `Moderate`, `Minor`, `Valid`) | `Critical` |
| **Recommended Correction** | Concrete, executable statistical modeling | `Fit Linear Mixed Model (lme4/lmer) with random patient intercepts` |
| **Confidence** | Calibrated model certainty | `High (96%)` |

*Rule: Internal chain-of-thought reasoning is strictly omitted from the Scientific Audit card to ensure clean, publication-ready takeaways.*

---

## 5. Developer Mode & Diagnostics

When enabled in Settings, Developer Mode opens a non-intrusive drawer displaying:
- **Active Model Lineage**: `BR-V02-DPO-001-A` (`checkpoint-step-27-epoch-1.0`)
- **Generation Temperature**: `0.0` (Deterministic)
- **Inference Latency**: e.g., `340 ms`
- **Estimated Tokens**: Prompt & completion token counts
- **ExperimentGraph Topology**: Node count, edge count, detected cycles/leakages
- **Raw Structured JSON**: Toggle to view raw JSON representation of the critique

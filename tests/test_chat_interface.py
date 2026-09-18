"""
tests/test_chat_interface.py

Validates the BioReason Conversational Chat Interface (chat/index.html, style.css, app.js).

Checks:
1. HTML semantic hierarchy, accessibility attributes, and element IDs.
2. CSS theme tokens, design variables, and responsive layout classes.
3. JavaScript state management, streaming mechanics, and collapsible audit logic.
4. Specification completeness.
"""

from pathlib import Path
import re
import pytest

CHAT_DIR = Path(__file__).resolve().parent.parent / "chat"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"


def test_chat_html_structure():
    index_html = CHAT_DIR / "index.html"
    assert index_html.exists(), "chat/index.html must exist."

    content = index_html.read_text(encoding="utf-8")

    # Essential conversational layout elements
    assert 'id="sidebar"' in content
    assert 'id="main-chat"' in content
    assert 'id="top-bar"' in content
    assert 'id="empty-state"' in content
    assert 'id="chat-scroll-area"' in content
    assert 'id="composer-container"' in content
    assert 'id="chat-input"' in content
    assert 'id="btn-send"' in content
    assert 'id="btn-stop"' in content
    assert 'id="dev-drawer"' in content
    assert 'id="settings-modal"' in content

    # Prompt chips in empty state
    assert 'class="prompt-chip"' in content
    assert 'Check my experimental design' in content
    assert 'Review my RNA-seq workflow' in content

    # Model header status
    assert 'BioReason v0.2 • Ready' in content


def test_chat_css_design_system():
    style_css = CHAT_DIR / "style.css"
    assert style_css.exists(), "chat/style.css must exist."

    content = style_css.read_text(encoding="utf-8")

    # Theme variables
    assert '--bg-app' in content
    assert '--bg-sidebar' in content
    assert '--accent-primary' in content
    assert '--chat-max-width' in content
    assert '[data-theme="light"]' in content

    # Component classes
    assert '.user-bubble' in content
    assert '.assistant-body' in content
    assert '.btn-audit-toggle' in content
    assert '.audit-card' in content
    assert '.composer-box' in content
    assert '.dev-drawer-content' in content


def test_chat_js_logic_and_features():
    app_js = CHAT_DIR / "app.js"
    assert app_js.exists(), "chat/app.js must exist."

    content = app_js.read_text(encoding="utf-8")

    # Local storage persistence
    assert 'STORAGE_KEYS' in content
    assert 'bioreason_chats_v02' in content
    assert 'localStorage.getItem' in content
    assert 'localStorage.setItem' in content

    # Markdown formatting
    assert 'formatMarkdown' in content
    assert 'code-block-wrapper' in content
    assert 'btn-copy-code' in content

    # Collapsible scientific audit
    assert 'toggleAudit' in content
    assert 'scientific-audit-wrapper' in content
    assert 'experimental_unit' in content
    assert 'primary_issue' in content

    # Streaming / Typewriter logic
    assert 'streamInterval' in content
    assert 'typing-indicator' in content
    assert 'handleStopGeneration' in content

    # Developer Mode
    assert 'BR-VERIFIED-SFT-002' in content
    assert 'devLatency' in content
    assert 'devJsonDisplay' in content


def test_chat_specification_document():
    spec_doc = DOCS_DIR / "BIOREASON_CHAT_SPECIFICATION.md"
    assert spec_doc.exists(), "docs/BIOREASON_CHAT_SPECIFICATION.md must exist."

    content = spec_doc.read_text(encoding="utf-8")
    assert "Conversational First" in content
    assert "Scientific Audit Component" in content
    assert "Developer Mode & Diagnostics" in content


def test_guided_pipeline_mode_html_and_css():
    style_css = CHAT_DIR / "style.css"
    assert style_css.exists(), "chat/style.css must exist."
    content = style_css.read_text(encoding="utf-8")

    # Guided Pipeline Container & Split View Classes
    assert '.guided-pipeline-container' in content
    assert '.pipeline-split-view' in content
    assert '.code-pane' in content
    assert '.guide-pane' in content
    assert '.pipeline-chunk-wrapper' in content
    assert '.guide-chunk-card' in content
    assert '.shape-tracker-row' in content
    assert '.config-pill-grid' in content
    assert '.step-nav-bar' in content
    assert '.full-script-view' in content


def test_guided_pipeline_js_interactive_features():
    app_js = CHAT_DIR / "app.js"
    assert app_js.exists(), "chat/app.js must exist."
    content = app_js.read_text(encoding="utf-8")

    # Pipeline generator & synchronized interaction
    assert 'renderGuidedPipelineHtml' in content
    assert 'highlightPipelineChunk' in content
    assert 'switchPipelineViewMode' in content
    assert 'stepPipelineStage' in content
    assert 'updatePipelineConfig' in content
    assert 'downloadFullScript' in content
    assert 'switchStrictnessLevel' in content

    # 3-Layer architecture & scientific explanation cards
    assert 'shape_progression' in content
    assert 'scores_vs_loadings' in content
    assert 'scores' in content
    assert 'loadings' in content
    assert 'renderGuidedPipelineHtml' in content
    assert 'GUIDED_RNASEQ_PIPELINE' not in content
    assert 'Thank you for sharing this scientific methodology' not in content


def test_guided_pipeline_specification_doc():
    pipeline_spec = DOCS_DIR / "GUIDED_PIPELINE_MODE_SPECIFICATION.md"
    assert pipeline_spec.exists(), "docs/GUIDED_PIPELINE_MODE_SPECIFICATION.md must exist."
    content = pipeline_spec.read_text(encoding="utf-8")

    assert "BioReason Guided Pipeline Mode Specification" in content
    assert "Conversational Intake Flow" in content
    assert "The Three-Layer Pipeline Architecture" in content
    assert "Synchronized Two-Pane View" in content
    assert "Data Shape Progression" in content
    assert "PCA SCORES VS LOADINGS" in content
    assert "Context-Aware Troubleshooting Engine" in content

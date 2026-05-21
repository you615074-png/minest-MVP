"""
CSS 常量与主题配色 — JetBrains Mono + Inter + 深色 GitHub 风格。
"""
CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
}

/* prevent Streamlit's default padding from breaking dark bg */
.stApp { background: #0d1117; }

.terminal-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 13px;
    color: #58a6ff;
    min-height: 120px;
    max-height: 320px;
    overflow-y: auto;
    line-height: 1.8;
}
.terminal-box .log-ok  { color: #3fb950; }
.terminal-box .log-warn { color: #d29922; }
.terminal-box .log-err  { color: #f85149; }
.terminal-box .log-info { color: #58a6ff; }

.hook-tag {
    display: inline-block;
    background: rgba(99,102,241,0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    margin: 3px;
    font-weight: 500;
}
.section-title {
    font-size: 15px; font-weight: 600;
    color: #e6edf3; margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #21262d;
}
.persona-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 14px;
}
.history-item {
    font-size: 13px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 6px;
    color: #e5e7eb;
}

/* ── Pipeline progress bar ── */
.pipeline-node {
    transition: all 0.3s ease;
}
.pipeline-node.active {
    box-shadow: 0 0 12px rgba(99,102,241,0.3);
}

/* ── Input area refinements ── */
.stTextArea textarea, .stTextInput input {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}

/* ── Button refinements ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
}
</style>
"""

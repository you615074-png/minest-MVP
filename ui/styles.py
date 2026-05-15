"""
CSS 常量与主题配色 — 全局样式集中管理。
"""

CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.terminal-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #58a6ff;
    min-height: 120px;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.8;
}
.terminal-box .log-ok  { color: #3fb950; }
.terminal-box .log-warn { color: #d29922; }
.terminal-box .log-err  { color: #f85149; }
.terminal-box .log-info { color: #58a6ff; }

.hook-tag {
    display: inline-block;
    background: #1f4e79;
    color: #79c0ff;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    margin: 3px;
}
.section-title {
    font-size: 16px; font-weight: 600;
    color: #e6edf3; margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #21262d;
}
.persona-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
.history-item {
    font-size: 13px;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 8px;
    color: #e5e7eb;
}
</style>
"""

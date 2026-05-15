"""
可复用的 UI 渲染组件。
"""
import streamlit as st


def colorize(line: str) -> str:
    """根据日志内容返回带 CSS class 的 HTML 行"""
    if "✅" in line:
        return f'<span class="log-ok">{line}</span>'
    elif "⚠️" in line:
        return f'<span class="log-warn">{line}</span>'
    elif "❌" in line or "⛔" in line:
        return f'<span class="log-err">{line}</span>'
    return f'<span class="log-info">{line}</span>'


def terminal_box(lines: list[str]) -> str:
    """渲染终端风格的日志盒子 HTML"""
    content = "<br>".join(colorize(l) for l in lines)
    return f'<div class="terminal-box">{content}</div>'


def section_title(label: str, margin_top: str = "0px") -> str:
    """渲染分组标题 HTML"""
    return f'<div class="section-title" style="margin-top: {margin_top};">{label}</div>'


def persona_card(persona: dict, index: int) -> str:
    """渲染人物画像卡片 HTML"""
    return f"""
    <div class="persona-card">
        <h4>👤 画像 {index + 1}: {persona.get('persona_name', '未知群体')}</h4>
        <p><strong>🔴 核心痛点：</strong><br> - {'<br> - '.join(persona.get('pain_points', []))}</p>
        <p><strong>✅ 匹配原因：</strong> {persona.get('why_fit', '')}</p>
    </div>
    """


def hook_tags(hooks: list[str]) -> str:
    """渲染销售切入点标签 HTML"""
    return " ".join(f'<span class="hook-tag">🎯 {h}</span>' for h in hooks)


def history_item(icon: str, title: str, date_str: str) -> str:
    """渲染历史记录条目 HTML"""
    return f"<div class='history-item'><b>{icon} {title}</b><br><span style='color:#9ca3af; font-size:11px;'>{date_str}</span></div>"


def company_target_card(target: dict) -> str:
    """渲染潜在目标公司卡片 HTML"""
    url = target.get('company_url', '')
    url_display = f"<a href='{url}' target='_blank'>{url}</a>" if url.startswith('http') else url
    return f"""
    <div class="persona-card" style="background: #0d1117;">
        <h5 style="margin-top: 0; color: #58a6ff;">🎯 {target.get('company_name', '未知公司')}</h5>
        <p style="font-size: 13px; color: #8b949e;"><strong>🔗 网址：</strong> {url_display}</p>
        <p style="font-size: 14px;"><strong>💡 推荐理由：</strong> {target.get('reason', '')}</p>
    </div>
    """

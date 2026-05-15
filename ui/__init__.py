"""
ui 模块 — 负责 Streamlit 界面组装与状态管理。

目录结构:
    styles.py    — CSS 常量与主题配色
    components.py — 可复用 UI 组件 (终端盒子、卡片等)
    session.py   — Session State 初始化
    auth_ui.py   — 登录/注册弹窗
    workflow.py  — 工作流执行引擎 (流式 + 批量)
    renderer.py  — 结果展示渲染器
"""

from ui.components import colorize, terminal_box, section_title, persona_card, history_item, hook_tags
from ui.session import init_session, is_authenticated, get_user, set_user, clear_user
from ui.auth_ui import render_auth_section, auth_dialog
from ui.workflow import run_workflow
from ui.renderer import render_result

"""
Agent Pipeline 可视化组件 — 5 节点流水线 + 条件分支展示。
"""


def pipeline_html(current_step: int = -1, mode: str = "SDR") -> str:
    """
    渲染 Agent 流水线 SVG 图。

    current_step: -1 表示全部灰色（未启动），0-4 表示高亮到第几步。
    mode: "SDR" 或 "MARKET_ANALYSIS"
    """
    if mode == "MARKET_ANALYSIS":
        steps = [("🧠", "市场分析师", "受众推演 + 5家推荐")]
        step_count = 1
    else:
        steps = [
            ("🕵️", "情报官", "官网抓取 + 新闻搜索"),
            ("⚙️", "处理器", "结构化档案提取"),
            ("📊", "打分员", "四维商机评分"),
            ("✍️", "文案专家", "个性化开发信"),
            ("📦", "导出", "Markdown 报告"),
        ]
        step_count = 5

    nodes = []
    for i, (icon, name, desc) in enumerate(steps):
        active = current_step < 0 or i <= current_step
        opacity = "1" if active else "0.3"
        border = "rgba(99,102,241,0.6)" if active else "rgba(255,255,255,0.06)"
        bg = "rgba(99,102,241,0.12)" if active else "rgba(255,255,255,0.03)"
        color = "#e0e7ff" if active else "#484f58"

        nodes.append(f"""
        <div style="
            display:flex;flex-direction:column;align-items:center;gap:8px;
            flex:1;min-width:0;position:relative;
        ">
            <div style="
                width:56px;height:56px;border-radius:16px;
                background:{bg};border:2px solid {border};
                display:flex;align-items:center;justify-content:center;
                font-size:24px;opacity:{opacity};
            ">{icon}</div>
            <div style="text-align:center;">
                <div style="font-size:13px;font-weight:600;color:{color};">{name}</div>
                <div style="font-size:11px;color:#8b949e;margin-top:2px;line-height:1.3;">{desc}</div>
            </div>
        </div>
        """)

    arrows = ""
    for i in range(step_count - 1):
        active = current_step < 0 or i < current_step
        arrow_color = "#6366f1" if active else "#30363d"
        arrows += f"""
        <div style="display:flex;align-items:center;padding:0 4px;flex-shrink:0;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{arrow_color}" stroke-width="2" stroke-linecap="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
        </div>
        """

    interleaved = []
    for i in range(step_count):
        interleaved.append(nodes[i])
        if i < step_count - 1:
            interleaved.append(arrows)

    pipeline = "".join(interleaved)

    status_text = ""
    if current_step < 0:
        status_text = '<div style="text-align:center;color:#484f58;font-size:12px;margin-top:12px;">等待启动...</div>'
    elif current_step >= step_count - 1:
        status_text = '<div style="text-align:center;color:#3fb950;font-size:12px;margin-top:12px;">✅ Pipeline 完成</div>'
    else:
        status_text = f'<div style="text-align:center;color:#d29922;font-size:12px;margin-top:12px;">⚡ 执行中...({current_step+1}/{step_count})</div>'

    return f"""
    <div style="
        background:#0d1117;border:1px solid #30363d;border-radius:16px;
        padding:24px 20px 16px;margin-bottom:16px;
    ">
        <div style="display:flex;align-items:center;gap:0;">
            {pipeline}
        </div>
        {status_text}
    </div>
    """


def pipeline_step_labels(mode: str = "SDR") -> list[str]:
    if mode == "MARKET_ANALYSIS":
        return ["market_analyzer"]
    return ["researcher", "processor", "scorer", "copywriter", "done"]

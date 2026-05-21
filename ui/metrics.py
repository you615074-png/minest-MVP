"""
关键指标仪表盘 — 展示分析结果的核心数据。
"""


def metrics_dashboard(result: dict) -> str:
    score = result.get("lead_score", 0)
    profile = result.get("company_profile", {})
    hooks_count = len(result.get("key_hooks", []))
    email_exists = bool(result.get("email_draft", {}).get("body"))

    items = [
        ("商机评分", f"{score}/100", _score_color(score)),
        ("行业", profile.get("industry", "—"), "#58a6ff"),
        ("融资阶段", profile.get("funding_stage", "—"), "#a371f7"),
        ("痛点匹配", str(hooks_count), "#3fb950"),
        ("开发信", "已生成" if email_exists else "—", "#d29922" if email_exists else "#484f58"),
    ]

    cards = ""
    for label, value, color in items:
        cards += f"""
        <div style="
            background:#161b22;border:1px solid #30363d;border-radius:12px;
            padding:14px 16px;text-align:center;flex:1;min-width:0;
        ">
            <div style="font-size:11px;color:#8b949e;margin-bottom:4px;">{label}</div>
            <div style="font-size:20px;font-weight:700;color:{color};">{value}</div>
        </div>
        """

    return f"""
    <div style="
        background:#0d1117;border:1px solid #30363d;border-radius:16px;
        padding:16px 12px;margin-bottom:16px;
    ">
        <div style="display:flex;gap:8px;">
            {cards}
        </div>
    </div>
    """


def before_after_comparison() -> str:
    return """
    <div style="
        background:#0d1117;border:1px solid #30363d;border-radius:16px;
        padding:20px;margin-bottom:16px;
    ">
        <div style="font-size:15px;font-weight:600;color:#e6edf3;margin-bottom:14px;">
            ⚡ 引入 AI 团队前后对比
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:rgba(248,81,73,0.08);border:1px solid rgba(248,81,73,0.2);border-radius:10px;padding:14px;">
                <div style="font-size:12px;color:#f85149;font-weight:600;margin-bottom:6px;">⚠ 传统模式</div>
                <div style="font-size:12px;color:#8b949e;line-height:1.7;">
                    · 单条线索耗时 <b>30 分钟</b><br>
                    · 背调依赖人工搜索<br>
                    · 开发信千篇一律<br>
                    · 无评分标准，凭经验判断
                </div>
            </div>
            <div style="background:rgba(63,185,80,0.08);border:1px solid rgba(63,185,80,0.2);border-radius:10px;padding:14px;">
                <div style="font-size:12px;color:#3fb950;font-weight:600;margin-bottom:6px;">✅ AI SDR 模式</div>
                <div style="font-size:12px;color:#8b949e;line-height:1.7;">
                    · 单条线索 <b>30 秒</b>，提效 60x<br>
                    · 全网自动抓取 + AI 结构化<br>
                    · 引用真实钩子的个性化开发信<br>
                    · 四维量化评分，可审计可复现
                </div>
            </div>
        </div>
    </div>
    """


def architecture_diagram() -> str:
    return """
    <details style="margin-bottom:16px;">
        <summary style="
            cursor:pointer;color:#58a6ff;font-size:14px;font-weight:600;
            padding:8px 0;list-style:none;
        ">📐 系统架构图 (点击展开)</summary>
        <div style="
            background:#0d1117;border:1px solid #30363d;border-radius:12px;
            padding:20px;font-family:'Courier New',monospace;font-size:12px;
            color:#8b949e;line-height:1.8;white-space:pre;overflow-x:auto;
        ">
┌──────────────────────────────────────┐
│        Streamlit Web UI 层           │
│  app.py → ui/pipeline → ui/metrics   │
├──────────────────────────────────────┤
│    LangGraph StateGraph 编排引擎      │
│         core/graph.py                │
│   条件路由: 有URL→SDR / 无URL→市场    │
├──────────┬──────────┬───────────────┤
│ 🕵️情报官 │ ⚙️处理器 │ 📊打分员      │
│ Jina抓取 │ Pydantic │ 四维评分      │
│ Tavily搜索│ 结构化  │ 0-100分       │
├──────────┴──────────┴───────────────┤
│  ✍️文案专家 (≥60分)  🧠市场专家(无URL)│
│  EmailDraft生成       Persona推演     │
├──────────────────────────────────────┤
│   LLM: DeepSeek/Kimi/MiniMax        │
│   SQLite WAL · bcrypt · RateLimiter  │
└──────────────────────────────────────┘
        </div>
    </details>
    """


def _score_color(score: int) -> str:
    if score > 60:
        return "#3fb950"
    elif score > 40:
        return "#d29922"
    return "#f85149"

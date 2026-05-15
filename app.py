"""
B2B AI SDR 数字团队 — Streamlit 应用入口
"""
import uuid
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.db import init_db, get_user_history
from ui.styles import CSS_GLOBAL
from ui.session import init_session, is_authenticated
from ui.auth_ui import render_auth_section, auth_dialog
from ui.components import history_item, terminal_box
from ui.workflow import run_workflow
from ui.renderer import render_result

# ── 初始化 ────────────────────────────────────────────────────
init_db()
init_session()

# ── 页面配置 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="AI SDR 数字团队",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

# ── 顶部栏 ────────────────────────────────────────────────────
top_l, top_r = st.columns([8, 2], vertical_alignment="center")

with top_l:
    st.markdown("## 🤖 B2B AI SDR 数字团队")
    st.caption("无人值守的智能销售线索开发引擎 — 情报挖掘 · 商机评分 · 开发信生成 · 市场分析")

with top_r:
    if is_authenticated():
        render_auth_section()
    else:
        if st.button("🔑 登录 / 注册", type="primary"):
            auth_dialog()

st.divider()

# ── 边栏：历史记录 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 历史分析记录")

    if not is_authenticated():
        st.info("请先登录以查看历史记录")
    else:
        uid = st.session_state.current_user["id"]
        records = get_user_history(uid)

        if not records:
            st.caption("暂无记录，快去生成第一条分析吧！")
        else:
            st.caption(f"共 {len(records)} 条记录 (最多保留50条)")
            for r in records:
                mode = r.get("mode")
                date_str = r.get("created_at")[:16]

                if mode == "MARKET_ANALYSIS":
                    icon = "🎯"
                    title = "受众分析"
                else:
                    score = r.get("full_result", {}).get("lead_score", 0)
                    icon = "🟢" if score > 60 else ("🔴" if score > 0 else "⚪")
                    comp = r.get("full_result", {}).get("company_profile", {}).get("company_name", "未知")
                    title = f"{comp}"

                st.markdown(history_item(icon, title, date_str), unsafe_allow_html=True)

                if st.button("查看详情", key=f"btn_{r['id']}", use_container_width=True):
                    st.session_state.current_result = r.get("full_result")

# ── 主布局 ────────────────────────────────────────────────────
if not is_authenticated():
    st.warning("🔒 欢迎使用 AI SDR，请点击右上角 **登录/注册** 后开始使用。")
    st.stop()

left_col, right_col = st.columns([1, 1.5], gap="large")

# 左：控制台
with left_col.container(height=800, border=False):
    st.markdown('<div class="section-title">📥 配置控制台</div>', unsafe_allow_html=True)

    product_desc = st.text_area(
        "🏢 我方产品卖点",
        placeholder="描述你的核心价值主张、目标客群、差异化优势、成功案例...",
        height=130,
        key="product_desc",
    )

    col_icp, col_lang = st.columns([2, 1])
    with col_icp:
        icp_definition = st.text_input(
            "🎯 理想客户画像 (ICP) - 可选",
            placeholder="例：有出海需求的SaaS企业",
            key="icp_definition",
        )
    with col_lang:
        output_lang = st.selectbox(
            "🌐 输出语言",
            ["简体中文", "English", "日本語", "Español"],
            key="output_lang",
        )

    tab_single, tab_batch = st.tabs(["📌 单条开发", "🗂️ 批量处理 (CSV/Excel)"])

    with tab_single:
        target_url = st.text_input(
            "🔗 目标公司网址 (如果不填，将自动进入市场分析模式)",
            placeholder="https://example.com (留空则分析潜在市场)",
            key="target_url",
        )

        run_disabled = st.session_state.is_running
        btn_text = "🚀 一键生成开发信" if target_url.strip() else "🎯 智能分析目标受众"

        run_btn = st.button(
            btn_text if not run_disabled else "⏳ AI 团队工作中...",
            type="primary",
            use_container_width=True,
            disabled=run_disabled,
        )

        if run_btn:
            if not product_desc.strip():
                st.error("请填写我方产品卖点！")
            else:
                st.session_state.is_running = True
                st.session_state.current_result = None
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.run_args = {
                    "product_desc": product_desc,
                    "icp_definition": icp_definition or "不限行业和规模",
                    "target_url": target_url.strip(),
                    "language": output_lang,
                    "batch_mode": False,
                }
                st.rerun()

    with tab_batch:
        st.info("批量处理会自动遍历名单，提取官网进行分析。为防触发 API 限流，两次请求间默认等待 3 秒。")
        uploaded_file = st.file_uploader("上传包含 'url' 或 '网址' 列的文件", type=["csv", "xlsx"])

        batch_run_disabled = st.session_state.is_running or not uploaded_file
        batch_run_btn = st.button(
            "🚀 开始批量处理",
            type="primary",
            use_container_width=True,
            disabled=batch_run_disabled,
            key="batch_run_btn",
        )

        if batch_run_btn and uploaded_file:
            if not product_desc.strip():
                st.error("请填写我方产品卖点！")
            else:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)

                    url_col = None
                    for col in df.columns:
                        if "url" in str(col).lower() or "网址" in str(col):
                            url_col = col
                            break

                    if not url_col:
                        st.error("未找到名为 'url' 或 '网址' 的列！")
                    else:
                        urls = df[url_col].dropna().astype(str).tolist()
                        valid_urls = [u for u in urls if u.startswith("http") or "." in u]

                        if not valid_urls:
                            st.error("列中没有找到有效的网址！")
                        else:
                            st.session_state.is_running = True
                            st.session_state.current_result = None
                            st.session_state.thread_id = str(uuid.uuid4())
                            st.session_state.run_args = {
                                "product_desc": product_desc,
                                "icp_definition": icp_definition or "不限行业和规模",
                                "target_urls": valid_urls[:20],
                                "language": output_lang,
                                "batch_mode": True,
                            }
                            st.rerun()
                except Exception as e:
                    st.error(f"解析文件失败: {str(e)}")

# 右：结果区
with right_col.container(height=800, border=False):
    st.markdown('<div class="section-title">📊 工作流实时状态</div>', unsafe_allow_html=True)

    result = st.session_state.current_result

    if st.session_state.is_running and not result:
        log_slot = st.empty()
        args = st.session_state.run_args
        all_results = run_workflow(args, log_slot)

        st.session_state.current_result = all_results[-1] if all_results else None
        st.session_state.is_running = False
        st.rerun()

    elif not result:
        st.markdown(
            '<div class="terminal-box" style="color:#484f58;">等待任务启动...<br>请在左侧填写配置后点击按钮，或在侧边栏选中历史记录。</div>',
            unsafe_allow_html=True,
        )
    else:
        render_result(result)

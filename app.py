import uuid
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.db import init_db, get_user_history, search_user_history, delete_history
from utils.validator import validate_config
from ui.styles import CSS_GLOBAL
from ui.session import init_session, is_authenticated
from ui.auth_ui import render_auth_section, auth_dialog
from ui.components import history_item, terminal_box
from ui.workflow import run_workflow
from ui.renderer import render_result
from ui.metrics import before_after_comparison, architecture_diagram

init_db()
init_session()

errors, warnings = validate_config()

st.set_page_config(
    page_title="AI SDR 数字团队",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

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

with st.sidebar:
    if errors:
        for err in errors:
            st.error(err)
        st.stop()
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} 个配置提醒"):
            for w in warnings:
                st.warning(w)

    st.markdown("### 📊 历史分析记录")

    if not is_authenticated():
        st.info("请先登录以查看历史记录")
    else:
        uid = st.session_state.current_user["id"]

        search_kw = st.text_input("搜索历史", placeholder="输入关键词...", key="hist_search")
        records = search_user_history(uid, search_kw) if search_kw else get_user_history(uid)

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

                col_view, col_del = st.columns([2, 1])
                with col_view:
                    if st.button("查看详情", key=f"btn_{r['id']}", use_container_width=True):
                        st.session_state.current_result = r.get("full_result")
                with col_del:
                    if st.button("🗑", key=f"del_{r['id']}", help="删除此记录"):
                        delete_history(r["id"], uid)
                        st.rerun()

    st.divider()
    with st.expander("🔧 系统状态"):
        try:
            from utils.db import get_connection
            with get_connection() as conn:
                conn.execute("SELECT 1")
            st.caption("DB: ✅")
        except Exception:
            st.caption("DB: ❌")
        st.caption("LLM: 启动校验已通过")
        if hasattr(st.session_state, "is_running"):
            st.caption(f"运行状态: {'🏃 工作中' if st.session_state.is_running else '⏸ 空闲'}")

if not is_authenticated():
    st.warning("🔒 欢迎使用 AI SDR，请点击右上角 **登录/注册** 后开始使用。")
    st.stop()

left_col, right_col = st.columns([1, 1.5], gap="large")

with left_col.container(height=800, border=False):
    st.markdown('<div class="section-title">📥 配置控制台</div>', unsafe_allow_html=True)

    product_desc = st.text_area(
        "🏢 我方产品卖点",
        placeholder="描述你的核心价值主张、目标客群、差异化优势、成功案例...",
        height=130,
        max_chars=2000,
        key="product_desc",
        help="试试这个示例：AI智能客服系统，面向SaaS企业，支持7×24小时自动应答，降低70%人工客服成本",
    )

    with st.expander("💡 示例数据（点击填入）"):
        ex1_col, ex2_col = st.columns(2)
        with ex1_col:
            if st.button("📋 SaaS CRM 销售", use_container_width=True, key="ex1"):
                st.session_state.product_desc = "企业级AI CRM系统，帮助B2B销售团队管理客户关系、自动化跟进流程。目标客群为50-500人的SaaS企业。已服务200+客户，核心优势是AI驱动的销售预测和自动化邮件序列。"
                st.session_state.icp_definition = "SaaS公司，50-200人规模，有销售团队"
                st.session_state.target_url = "https://www.intercom.com"
                st.rerun()
        with ex2_col:
            if st.button("🛒 跨境电商 ERP", use_container_width=True, key="ex2"):
                st.session_state.product_desc = "跨境电商ERP SaaS平台，支持多平台订单管理、库存同步、物流追踪。服务于东南亚市场的跨境电商卖家，日均处理订单10万+。"
                st.session_state.icp_definition = "跨境电商卖家，年GMV 100万美元以上"
                st.session_state.target_url = "https://www.shopify.com"
                st.rerun()

    col_icp, col_lang = st.columns([2, 1])
    with col_icp:
        icp_definition = st.text_input(
            "🎯 理想客户画像 (ICP) - 可选",
            placeholder="例：有出海需求的SaaS企业",
            max_chars=500,
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
            max_chars=500,
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
                    "product_desc": product_desc[:2000],
                    "icp_definition": icp_definition or "不限行业和规模",
                    "target_url": target_url.strip()[:500],
                    "language": output_lang,
                    "batch_mode": False,
                }
                st.rerun()

    with tab_batch:
        st.info("批量处理会自动遍历名单，提取官网进行分析。最大 2MB，最多 50 行。")
        uploaded_file = st.file_uploader(
            "上传包含 'url' 或 '网址' 列的文件",
            type=["csv", "xlsx"],
            help="文件最大 2MB，最多 50 行",
        )

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
            elif uploaded_file.size > 2 * 1024 * 1024:
                st.error("文件过大，请上传 2MB 以内的文件")
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

                        if len(valid_urls) > 50:
                            st.warning(f"最大处理 50 条，已截取前 50 条")
                            valid_urls = valid_urls[:50]

                        if not valid_urls:
                            st.error("列中没有找到有效的网址！")
                        else:
                            st.session_state.is_running = True
                            st.session_state.current_result = None
                            st.session_state.thread_id = str(uuid.uuid4())
                            st.session_state.run_args = {
                                "product_desc": product_desc[:2000],
                                "icp_definition": icp_definition or "不限行业和规模",
                                "target_urls": valid_urls,
                                "language": output_lang,
                                "batch_mode": True,
                            }
                            st.rerun()
                except Exception as e:
                    st.error(f"解析文件失败: {str(e)}")

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
        st.divider()
        st.markdown(before_after_comparison(), unsafe_allow_html=True)
        st.markdown(architecture_diagram(), unsafe_allow_html=True)
    else:
        render_result(result)

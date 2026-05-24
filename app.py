import uuid
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.db import init_db, get_user_history, search_user_history, delete_history, get_email_config, save_email_config, delete_email_config
from utils.encrypt import encrypt, decrypt
from utils.validator import validate_config
from ui.styles import CSS_GLOBAL
from ui.session import init_session, is_authenticated
from ui.auth_ui import render_auth_section, auth_dialog
from ui.components import history_item, terminal_box
from ui.workflow import run_workflow
from ui.renderer import render_result

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

        if st.session_state.is_running:
            st.warning("⏳ 任务运行中，历史暂不可用")
        else:
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
                            st.session_state._email_dirty = False
                            fr = r.get("full_result", {})
                            st.session_state.product_desc = fr.get("product_desc", "")
                            st.session_state.icp_definition = fr.get("icp_definition", "")
                            st.session_state.target_url = fr.get("target_url", "")
                            st.session_state.output_lang = fr.get("language", "简体中文")
                            st.session_state._viewing_history = True
                            st.rerun()
                    with col_del:
                        if st.button("🗑", key=f"del_{r['id']}", help="删除此记录"):
                            delete_history(r["id"], uid)
                            st.rerun()

    st.divider()
    with st.expander("📧 邮件发送配置"):
        if not is_authenticated():
            st.caption("请先登录后配置")
        else:
            uid = st.session_state.current_user["id"]
            cfg = get_email_config(uid)

            EMAIL_PRESETS = {
                "QQ 邮箱": ("smtp.qq.com", 465),
                "163 邮箱": ("smtp.163.com", 465),
                "Gmail": ("smtp.gmail.com", 587),
                "Outlook": ("smtp-mail.outlook.com", 587),
                "其他": ("", 465),
            }
            preset_names = list(EMAIL_PRESETS.keys())
            saved_preset = "其他"
            if cfg:
                for name, (host, port) in EMAIL_PRESETS.items():
                    if cfg["smtp_host"] == host and cfg["smtp_port"] == port and host:
                        saved_preset = name
                        break

            preset = st.selectbox("你用什么邮箱发送？", preset_names, index=preset_names.index(saved_preset), key="ec_preset")
            auto_host, auto_port = EMAIL_PRESETS[preset]
            custom = (preset == "其他")

            smtp_host = st.text_input("SMTP 服务器地址", value=auto_host if not cfg else cfg["smtp_host"], disabled=not custom, key="ec_host")
            smtp_port = st.number_input("端口", value=auto_port if not cfg else cfg["smtp_port"], min_value=1, max_value=65535, disabled=not custom, key="ec_port")

            smtp_user = st.text_input("邮箱账号", value=cfg["smtp_user"] if cfg else "", placeholder="your@qq.com", key="ec_user")
            smtp_pass = st.text_input("授权码", type="password", placeholder="留空则不修改", key="ec_pass")
            with st.expander("ℹ️ 如何获取授权码？"):
                st.markdown("""
                **QQ 邮箱**：登录 mail.qq.com → 设置 → 账户 → POP3/SMTP 服务 → 开启 → 生成授权码  
                **163 邮箱**：登录 mail.163.com → 设置 → POP3/SMTP/IMAP → 开启 → 新增授权码  
                **Gmail**：Google 账户 → 安全 → 两步验证 → 应用专用密码  
                **Outlook**：Microsoft 账户 → 安全 → 高级安全选项 → 应用密码  
                **飞书企业邮箱**：联系公司 IT 管理员获取
                """)
            sender_name = st.text_input("发件人名称", value=cfg["sender_name"] if cfg else "AI SDR", key="ec_name")

            col_save, col_test, col_del = st.columns([2, 2, 1])
            with col_save:
                if st.button("💾 保存配置", use_container_width=True):
                    if not smtp_user:
                        st.error("邮箱账号为必填项")
                    elif not smtp_pass and not cfg:
                        st.error("首次配置需填写授权码")
                    else:
                        final_host = auto_host if preset != "其他" else smtp_host
                        final_port = auto_port if preset != "其他" else smtp_port
                        final_pass = smtp_pass if smtp_pass else (decrypt(cfg["smtp_pass_encrypted"], cfg["smtp_pass_salt"], uid) if cfg else "")
                        if not final_pass:
                            st.error("无法获取授权码，请重新输入")
                        else:
                            enc_pw, salt = encrypt(final_pass, uid)
                            save_email_config(uid, final_host, final_port, smtp_user, enc_pw, salt, sender_name)
                            st.success("✅ 邮件配置已保存")
            with col_test:
                if st.button("📤 测试发送", use_container_width=True, help="发送测试邮件到你的邮箱"):
                    from utils.mailer import send_email
                    h = auto_host if preset != "其他" else smtp_host
                    p = auto_port if preset != "其他" else smtp_port
                    u = smtp_user
                    if smtp_pass:
                        pw = smtp_pass
                    elif cfg:
                        pw = decrypt(cfg["smtp_pass_encrypted"], cfg["smtp_pass_salt"], uid)
                    else:
                        pw = None
                    n = sender_name
                    if not u or not pw:
                        st.error("请填写邮箱账号和授权码")
                    elif not h:
                        st.error("请选择邮箱提供商或填写 SMTP 服务器")
                    else:
                        ok, msg = send_email(u, "AI SDR 测试邮件", "这是一封来自 AI SDR 数字团队的测试邮件，配置正确即可收到。", "", h, p, u, pw, n)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
            with col_del:
                if st.button("🗑", key="del_ec", help="删除配置"):
                    delete_email_config(uid)
                    st.rerun()
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

    viewing = st.session_state.get("_viewing_history", False)
    locked = viewing or st.session_state.is_running
    if st.session_state.is_running:
        st.info("⏳ AI 团队工作中，输入已锁定")
    elif viewing:
        st.info("📋 正在查看历史记录 — 输入已锁定")
        if st.button("🆕 开启新分析", type="primary", use_container_width=True):
            st.session_state._viewing_history = False
            st.session_state.current_result = None
            st.rerun()

    st.caption("🎬 没想好填什么？选一个场景，三行自动填好，点按钮就能看效果：")
    prefill_col1, prefill_col2 = st.columns(2)
    with prefill_col1:
        if st.button("📋 高分示例：智能办公 → 飞书", use_container_width=True, key="q1",
                     help="AI 办公平台 + 飞书 (SaaS) → 预期高分生成开发信", disabled=locked):
            st.session_state.product_desc = "AI 智能办公平台，提供 IM、文档、视频会议、项目管理一体化方案。面向 50-2000 人中大型企业，服务 10 万+ 客户，核心优势是跨部门协作提效 300%。"
            st.session_state.icp_definition = "中大型企业，50-1000 人，有跨部门协作需求"
            st.session_state.target_url = "https://www.feishu.cn"
            st.session_state._prefill_done = True
            st.session_state._email_dirty = False
            st.session_state._viewing_history = False
            st.rerun()
    with prefill_col2:
        if st.button("📋 低分示例：跨境 ERP → B站", use_container_width=True, key="q2",
                     help="跨境 ERP + B站 (视频娱乐) → 预期低分自动终止", disabled=locked):
            st.session_state.product_desc = "跨境电商 ERP SaaS 平台，支持 Shopee、Lazada、TikTok Shop 等 12 个平台订单、库存、物流一站式管理。服务东南亚卖家，日均处理订单 10 万+。"
            st.session_state.icp_definition = "跨境电商卖家，年 GMV 100 万美元以上"
            st.session_state.target_url = "https://www.bilibili.com"
            st.session_state._prefill_done = True
            st.session_state._email_dirty = False
            st.session_state._viewing_history = False
            st.rerun()
    if st.session_state.get("_prefill_done"):
        st.success("✅ 已填入演示数据，点击下方「一键生成」即可查看分析效果")

    product_desc = st.text_area(
        "🏢 我方产品卖点",
        placeholder="描述你的核心价值主张、目标客群、差异化优势、成功案例...",
        height=130,
        max_chars=2000,
        key="product_desc",
        disabled=viewing,
    )

    col_icp, col_lang = st.columns([2, 1])
    with col_icp:
        icp_definition = st.text_input(
            "🎯 理想客户画像 (ICP) - 可选",
            placeholder="例：有出海需求的SaaS企业",
            max_chars=500,
            key="icp_definition",
            disabled=viewing,
        )
    with col_lang:
        output_lang = st.selectbox(
            "🌐 输出语言",
            ["简体中文", "English", "日本語", "Español"],
            key="output_lang",
            disabled=viewing,
        )

    with st.expander("✏️ 邮件风格", expanded=False):
        st_style = st.session_state.get("_email_style", {"tone": "真诚亲切", "length": "100-200字", "opening": "引用近期动态", "cta": "约15分钟通话"})
        tone = st.selectbox("语气", ["真诚亲切", "专业正式", "简洁直接"], index=["真诚亲切", "专业正式", "简洁直接"].index(st_style.get("tone", "真诚亲切")), key="es_tone", disabled=viewing)
        length = st.selectbox("长度", ["100-200字", "50-100字", "200-300字"], index=["100-200字", "50-100字", "200-300字"].index(st_style.get("length", "100-200字")), key="es_len", disabled=viewing)
        opening = st.selectbox("开头方式", ["引用近期动态", "直接切入痛点", "赞美对方成就"], index=["引用近期动态", "直接切入痛点", "赞美对方成就"].index(st_style.get("opening", "引用近期动态")), key="es_open", disabled=viewing)
        cta = st.selectbox("行动号召", ["约15分钟通话", "发送产品Demo", "邀请免费试用"], index=["约15分钟通话", "发送产品Demo", "邀请免费试用"].index(st_style.get("cta", "约15分钟通话")), key="es_cta", disabled=viewing)
        if not viewing:
            st.session_state._email_style = {"tone": tone, "length": length, "opening": opening, "cta": cta}

    tab_single, tab_batch = st.tabs(["📌 单条开发", "🗂️ 批量处理 (CSV/Excel)"])

    with tab_single:
        target_url = st.text_input(
            "🔗 目标公司网址 (如果不填，将自动进入市场分析模式)",
            placeholder="https://example.com (留空则分析潜在市场)",
            max_chars=500,
            key="target_url",
            disabled=viewing,
        )

        run_disabled = st.session_state.is_running or viewing
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
                st.session_state._prefill_done = False
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.run_args = {
                    "product_desc": product_desc[:2000],
                    "icp_definition": icp_definition or "不限行业和规模",
                    "target_url": target_url.strip()[:500],
                    "target_email": "",
                    "language": output_lang,
                    "email_style": st.session_state.get("_email_style", {}),
                    "batch_mode": False,
                }
                st.rerun()

    with tab_batch:
        st.info("批量处理会自动遍历名单，提取官网进行分析。最大 2MB，最多 50 行。")
        st.download_button("📥 下载 CSV 模板", data="url,email\nhttps://www.feishu.cn,partner@feishu.cn\nhttps://www.deepseek.com,contact@deepseek.com\n", file_name="batch_template.csv", mime="text/csv", key="csv_tpl")
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
                    email_col = None
                    for col in df.columns:
                        c = str(col).lower()
                        if url_col is None and ("url" in c or "网址" in c):
                            url_col = col
                        if email_col is None and ("email" in c or "邮箱" in c or "mail" in c):
                            email_col = col

                    if not url_col:
                        st.error("未找到名为 'url' 或 '网址' 的列！")
                    else:
                        urls = df[url_col].dropna().astype(str).tolist()
                        emails = df[email_col].dropna().astype(str).tolist() if email_col else []
                        valid_urls = [u for u in urls if u.startswith("http") or "." in u]

                        if len(valid_urls) > 50:
                            st.warning(f"最大处理 50 条，已截取前 50 条")
                            valid_urls = valid_urls[:50]

                        if not valid_urls:
                            st.error("列中没有找到有效的网址！")
                        else:
                            st.session_state.is_running = True
                            st.session_state.current_result = None
                            st.session_state._prefill_done = False
                            st.session_state.thread_id = str(uuid.uuid4())
                            st.session_state.run_args = {
                                "product_desc": product_desc[:2000],
                                "icp_definition": icp_definition or "不限行业和规模",
                                "target_urls": valid_urls,
                                "target_emails": emails[:len(valid_urls)] if emails else [],
                                "language": output_lang,
                                "email_style": st.session_state.get("_email_style", {}),
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
        st.session_state._email_dirty = False
        st.session_state.is_running = False
        st.rerun()

    elif not result:
        st.markdown(
            '<div class="terminal-box" style="color:#484f58;">等待任务启动...<br>请在左侧填写配置后点击按钮，或在侧边栏选中历史记录。</div>',
            unsafe_allow_html=True,
        )
    else:
        render_result(result)

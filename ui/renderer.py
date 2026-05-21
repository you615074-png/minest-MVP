"""
结果展示渲染器 — SDR / 市场分析 / 导出。
"""
import time
import streamlit as st
from ui.components import (
    terminal_box, section_title, persona_card, hook_tags, company_target_card,
)
from utils.secrets import redact_secrets


def render_result(result: dict):
    mode = result.get("mode")

    logs = result.get("log_messages", [])
    if logs:
        safe_logs = [redact_secrets(l) for l in logs]
        st.markdown(terminal_box(safe_logs), unsafe_allow_html=True)

    if result.get("error_message"):
        st.error(f"❌ {redact_secrets(result['error_message'])}")
        return

    st.markdown(section_title("📝 输入条件"), unsafe_allow_html=True)
    with st.container():
        st.caption(f"**产品卖点：** {result.get('product_desc', '-')[:120]}...")
        if result.get("icp_definition") and result.get("icp_definition") != "不限行业和规模":
            st.caption(f"**ICP：** {result.get('icp_definition', '-')}")
        if result.get("target_url"):
            st.caption(f"**目标网址：** {result.get('target_url', '-')}")

    if mode == "MARKET_ANALYSIS":
        _render_market_analysis(result)
    else:
        _render_sdr_result(result)

    _render_export(result, mode)


def _render_market_analysis(result: dict):
    st.markdown("<br>" + section_title("🎯 目标受众与市场分析"), unsafe_allow_html=True)
    market_data = result.get("market_analysis", {})

    if not market_data:
        return

    st.info(redact_secrets(f"💡 **市场切入建议：** {market_data.get('market_insights', '')}"))

    for i, persona in enumerate(market_data.get("personas", [])):
        st.markdown(persona_card(persona, i), unsafe_allow_html=True)

    targets = market_data.get("potential_targets", [])
    if targets:
        st.markdown(section_title("🏢 潜在标杆客户推荐"), unsafe_allow_html=True)
        for t in targets:
            st.markdown(company_target_card(t), unsafe_allow_html=True)


def _render_sdr_result(result: dict):
    profile = result.get("company_profile", {})
    if profile:
        with st.expander("📋 公司档案", expanded=True):
            ca, cb = st.columns(2)
            ca.write(f"**公司：** {profile.get('company_name', '-')}")
            ca.write(f"**行业：** {profile.get('industry', '-')}")
            ca.write(f"**规模：** {profile.get('company_size', '-')}")
            cb.write(f"**融资：** {profile.get('funding_stage', '-')}")
            if profile.get("main_products"):
                st.write("**核心产品：** " + " · ".join(profile["main_products"]))
            if profile.get("recent_news"):
                st.write("**近期动态：**")
                for news in profile["recent_news"]:
                    st.write(f"  📰 {news}")
            if profile.get("pain_points_inferred"):
                st.write("**推断痛点：**")
                for p in profile["pain_points_inferred"]:
                    st.write(f"  💡 {p}")

    score = result.get("lead_score", 0)
    if score:
        st.markdown("<br>" + section_title("📊 商机评分"), unsafe_allow_html=True)
        if score > 60:
            st.success(f"✅ 优质线索 — **{score} / 100 分**")
        elif score > 40:
            st.warning(f"⚠️ 边缘线索 — **{score} / 100 分**")
        else:
            st.error(f"⛔ 低质量线索 — **{score} / 100 分**")

        st.progress(score / 100)
        st.caption(f"📝 {result.get('score_rationale', '')}")

        hooks = result.get("key_hooks", [])
        if hooks:
            st.markdown(f"**核心切入点：**<br>{hook_tags(hooks)}", unsafe_allow_html=True)

    email = result.get("email_draft", {})
    if email:
        st.divider()
        st.markdown(section_title("✉️ 开发信草稿"), unsafe_allow_html=True)

        st.session_state.email_subject = redact_secrets(email.get("subject", ""))
        st.text_input("📌 邮件主题", key="email_subject")

        body_val = email.get("body", "")
        if not st.session_state.get("_email_dirty", False):
            if not body_val or len(body_val.strip()) < 5:
                body_val = "（开发信正文生成异常，请联系管理员）"
            st.session_state.email_body = redact_secrets(body_val)
            st.session_state._email_dirty = True

        st.markdown(section_title("📝 邮件正文"), unsafe_allow_html=True)
        body_display = st.session_state.get("email_body", body_val)
        st.markdown(
            f"<div style='background:#161b22;border:1px solid #30363d;border-radius:10px;"
            f"padding:16px 20px;line-height:1.9;color:#e0e7ef;font-size:14px;"
            f"white-space:pre-wrap;min-height:60px;'>{redact_secrets(body_display)}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"📄 正文 {len(body_val)} 字 | 主题 {len(email.get('subject', ''))} 字")
        if email.get("ps_line"):
            st.caption(redact_secrets(f"**PS：** {email['ps_line']}"))

        if st.button("✅ 批准并发送", type="primary", use_container_width=True, key="btn_send"):
            st.balloons()
            st.success("🎉 开发信已加入发件队列！（Demo 演示模式）")

    elif score and score <= 60:
        st.info("⛔ 该线索评分低于 60 分，已自动跳过文案生成，节省 API Token 消耗。")


def _render_export(result: dict, mode: str):
    st.divider()

    report_md = f"# AI SDR 分析报告\n\n**生成语言**: {result.get('language', '简体中文')}\n"

    if mode == "MARKET_ANALYSIS":
        md_data = result.get("market_analysis", {})
        report_md += f"\n## 🎯 市场分析\n\n**市场切入建议**：{md_data.get('market_insights', '')}\n\n"
        for i, p in enumerate(md_data.get("personas", [])):
            report_md += f"### 画像 {i + 1}: {p.get('persona_name')}\n- **痛点**: {', '.join(p.get('pain_points', []))}\n- **匹配原因**: {p.get('why_fit')}\n\n"
        report_md += "## 🏢 潜在客户推荐\n"
        for t in md_data.get("potential_targets", []):
            report_md += f"- **{t.get('company_name')}** ({t.get('company_url')})\n  - 推荐理由: {t.get('reason')}\n"
    else:
        score = result.get("lead_score", 0)
        report_md += f"\n## 📊 商业评估\n**评分**: {score}/100\n**评估依据**: {result.get('score_rationale', '')}\n\n"
        if score > 60 and result.get("email_draft"):
            email_d = result.get("email_draft")
            report_md += f"## ✉️ 开发信草稿\n**主题**: {email_d.get('subject')}\n\n**正文**:\n{email_d.get('body')}\n\n**PS**: {email_d.get('ps_line', '')}\n"

    report_md = redact_secrets(report_md)

    st.download_button(
        label="📥 导出分析报告 (Markdown)",
        data=report_md.encode("utf-8"),
        file_name=f"SDR_Report_{int(time.time())}.md",
        mime="text/markdown",
        use_container_width=True,
    )

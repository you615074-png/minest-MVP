"""
工作流执行引擎 — 处理单条/批量分析任务。
"""
import uuid
import time
import streamlit as st
from core.graph import graph
from ui.components import terminal_box
from utils.db import save_history


def run_workflow(args: dict, log_slot):
    """执行工作流并渲染实时日志，返回 (all_results: list[dict])"""
    is_batch = args.get("batch_mode", False)
    target_urls = args.get("target_urls", [args.get("target_url", "")])
    user_id = st.session_state.current_user["id"]
    thread_id = st.session_state.thread_id

    all_results = []
    for i, url in enumerate(target_urls):
        if is_batch:
            st.markdown(f"**处理进度**: {i + 1}/{len(target_urls)} — `{url}`")

        initial_state = {
            "product_desc": args["product_desc"],
            "icp_definition": args["icp_definition"],
            "target_url": url,
            "language": args.get("language", "简体中文"),
            "company_raw_data": "",
            "company_profile": {},
            "lead_score": 0,
            "score_rationale": "",
            "key_hooks": [],
            "email_draft": {},
            "market_analysis": {},
            "mode": "",
            "log_messages": [f"🚀 启动任务：{url}" if url else "🚀 系统启动中..."],
            "error_message": None,
            "should_proceed": False,
        }
        config = {"configurable": {"thread_id": f"{thread_id}_{i}"}}

        final_state = initial_state
        try:
            for s in graph.stream(initial_state, config=config, stream_mode="values"):
                final_state = s
                logs = s.get("log_messages", [])
                if logs:
                    log_slot.markdown(terminal_box(logs), unsafe_allow_html=True)

            mode = final_state.get("mode", "SDR" if url else "MARKET_ANALYSIS")
            save_history(user_id, mode, args["product_desc"], url, final_state)
            all_results.append(final_state)

            if is_batch and i < len(target_urls) - 1:
                log_slot.markdown(
                    '<div class="terminal-box"><span class="log-info">⏳ 批量模式防限流，等待 3 秒...</span></div>',
                    unsafe_allow_html=True,
                )
                time.sleep(3)

        except Exception as e:
            err_msg = str(e)
            if "api_key" in err_msg.lower() or "sk-" in err_msg:
                safe_msg = "AI 服务配置异常，请检查 .env 中的 API Key 设置"
            elif "connect" in err_msg.lower() or "timeout" in err_msg.lower():
                safe_msg = "网络连接超时，请检查网络后重试"
            elif "bcrypt" in err_msg.lower():
                safe_msg = "密码服务异常，请重新登录"
            else:
                safe_msg = err_msg[:100] if len(err_msg) > 100 else err_msg

            all_results.append({
                "error_message": safe_msg,
                "log_messages": [f"❌ 运行出错：{safe_msg}"],
            })
            if not is_batch:
                break

    return all_results

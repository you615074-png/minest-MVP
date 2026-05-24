"""
Session State 初始化与管理。
"""
import uuid
import streamlit as st

SESSION_KEYS = {
    "thread_id": str(uuid.uuid4()),
    "current_result": None,
    "is_running": False,
    "current_user": None,
    "_email_style": {"tone": "真诚亲切", "length": "100-200字", "opening": "引用近期动态", "cta": "约15分钟通话"},
}


def init_session():
    """初始化所有 session state 键"""
    for key, default in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def is_authenticated() -> bool:
    return st.session_state.current_user is not None


def get_user() -> dict | None:
    return st.session_state.current_user


def set_user(user: dict | None):
    st.session_state.current_user = user
    st.session_state.current_result = None
    st.session_state._prefill_done = False
    st.session_state._last_email_fp = None


def clear_user():
    set_user(None)

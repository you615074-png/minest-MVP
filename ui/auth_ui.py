"""
登录注册弹窗 UI。
"""
import streamlit as st
from utils.auth import register_user, authenticate_user
from ui.session import set_user


@st.dialog("🔐 登录 / 注册", width="small")
def auth_dialog():
    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        log_user = st.text_input("用户名", key="log_user")
        log_pwd = st.text_input("密码", type="password", key="log_pwd")
        if st.button("立即登录", type="primary", use_container_width=True):
            success, msg, user = authenticate_user(log_user, log_pwd)
            if success:
                set_user(user)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        reg_user = st.text_input("新建用户名", key="reg_user")
        reg_pwd = st.text_input("设置密码 (至少6位)", type="password", key="reg_pwd")
        if st.button("注册并登录", type="primary", use_container_width=True):
            success, msg, user = register_user(reg_user, reg_pwd)
            if success:
                set_user(user)
                st.rerun()
            else:
                st.error(msg)


def render_auth_section():
    """顶部栏右侧：登录按钮或用户名+退出"""
    if st.session_state.current_user:
        st.write(f"👤 **{st.session_state.current_user['username']}**")
        if st.button("退出登录"):
            set_user(None)
            st.rerun()
    else:
        if st.button("🔑 登录 / 注册", type="primary"):
            auth_dialog()

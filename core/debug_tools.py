import streamlit as st
import logging
import json
from datetime import datetime

def render_debug_panel(feature_name, context_data=None, log_func=None):
    """
    Hiển thị nút và panel debug dành riêng cho Admin.
    
    Args:
        feature_name (str): Tên tính năng đang debug.
        context_data (dict): Dữ liệu ngữ cảnh cần kiểm tra (biến, state...).
        log_func (callable): Hàm thực thi logic test/debug nếu cần.
    """
    # Kiểm tra quyền Admin
    user_info = st.session_state.get('user_info', {})
    if str(user_info.get('role', '')).lower() != 'admin':
        return

    # Giao diện Debug
    with st.expander(f"🛠️ Debug: {feature_name} (Admin Only)", expanded=False):
        st.markdown(f"**⏱️ Timestamp:** `{datetime.now().strftime('%H:%M:%S')}`")
        
        # 1. Hiển thị Context Data
        if context_data:
            st.markdown("#### 📦 Context Data")
            st.json(context_data)
        
        # 2. Nút chạy Log/Test
        if log_func:
            if st.button(f"▶️ Run Debug Logic ({feature_name})", key=f"btn_debug_{feature_name}"):
                try:
                    with st.spinner("Running debug logic..."):
                        result = log_func()
                    st.success("Debug executed successfully.")
                    st.markdown("#### 📝 Execution Log")
                    if isinstance(result, (dict, list)):
                        st.json(result)
                    else:
                        st.code(str(result))
                except Exception as e:
                    st.error(f"Debug Error: {e}")
        
        # 3. Session State Dump
        if st.checkbox("🔍 Inspect Full Session State", key=f"chk_sess_{feature_name}"):
            st.write(st.session_state)
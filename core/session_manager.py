import streamlit as st

def init_session_state():
    """Khởi tạo các biến session state mặc định cho ứng dụng."""
    defaults = {
        'logged_in': False,
        'user_info': {},
        'auth_mode': 'login',
        'active_page': 'home',
        'last_streak_check': 0,
        'daily_progress': "0/10"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
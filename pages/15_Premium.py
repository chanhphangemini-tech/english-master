import streamlit as st

from core.theme_applier import apply_page_theme
from core.debug_tools import render_debug_panel
from views.premium_view import render_premium_page

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("Home.py")

apply_page_theme()  # Apply theme + sidebar + auth

st.title("⭐ Nâng Cấp Tài Khoản")
st.caption("Chọn gói dịch vụ phù hợp với bạn: Basic, Premium hoặc Pro để mở khóa toàn bộ tính năng và nhận nhiều lượt AI hơn.")

# Render premium page
render_premium_page()

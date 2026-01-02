import streamlit as st
import time
from typing import Dict, Any

from core.auth import change_password, get_user_settings, upload_and_update_avatar
from core.theme_applier import apply_page_theme
from views.settings_view import (
    render_avatar_upload_section,
    render_password_change_form,
    render_notification_settings
)

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

st.title("⚙️ Cài Đặt Tài Khoản")

curr_user: str = st.session_state.user_info.get('username')

tab_profile, tab_pass, tab_notif = st.tabs(["👤 Hồ Sơ Cá Nhân", "🔐 Đổi Mật Khẩu", "🔔 Thông Báo"])

# Avatar Upload Handler
def handle_avatar_upload(username: str, uploaded_file: Any, crop_box: Any = None) -> None:
    ok, res = upload_and_update_avatar(username, uploaded_file, crop_box)
    if ok:
        st.success("✅ Đổi ảnh đại diện thành công!")
        st.session_state.user_info['avatar_url'] = res
        time.sleep(1)
        st.rerun()
    else:
        st.error(f"Lỗi: {res}")

# Password Change Handler
def handle_password_change(username: str, old_pass: str, new_pass: str) -> None:
    ok, msg = change_password(username, old_pass, new_pass)
    if ok:
        st.success("✅ Đổi mật khẩu thành công!")
    else:
        st.error(f"Lỗi: {msg}")

with tab_profile:
    render_avatar_upload_section(curr_user, handle_avatar_upload)

with tab_pass:
    render_password_change_form(curr_user, handle_password_change)

with tab_notif:
    settings: Dict[str, bool] = get_user_settings(curr_user)
    render_notification_settings(curr_user, settings)

import streamlit as st
import time
import logging
from typing import Dict, Any

from core.auth import change_password, get_user_settings, upload_and_update_avatar
from core.theme_applier import apply_page_theme
from views.settings_view import (
    render_avatar_upload_section,
    render_password_change_form,
    render_notification_settings
)

logger = logging.getLogger(__name__)

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

st.title("⚙️ Cài Đặt Tài Khoản")

curr_user: str = st.session_state.user_info.get('username')

tab_profile, tab_pass, tab_notif = st.tabs(["👤 Hồ Sơ Cá Nhân", "🔐 Đổi Mật Khẩu", "🔔 Thông Báo"])

# Avatar Upload Handler - EXACTLY LIKE REFERENCE CODE
def handle_avatar_upload(username: str, uploaded_file: Any, crop_box: Any = None) -> None:
    """
    Handle avatar upload. EXACTLY like reference code - update session_state directly, NO refresh_user_info.
    """
    ok, res = upload_and_update_avatar(username, uploaded_file, crop_box)
    if ok:
        st.success("✅ Đổi ảnh đại diện thành công!")
        
        # EXACTLY like reference code: Update session_state directly, NO refresh_user_info
        st.session_state.user_info['avatar_url'] = res
        
        # Clear sidebar stats cache (like reference code clears get_top_3_details)
        user_id = st.session_state.user_info.get('id')
        if user_id:
            stats_cache_key = f'sidebar_stats_{user_id}'
            if stats_cache_key in st.session_state:
                del st.session_state[stats_cache_key]
        
        # Rerun immediately (like reference code)
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

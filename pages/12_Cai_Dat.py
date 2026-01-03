import streamlit as st
import time
import logging
from typing import Dict, Any

from core.auth import change_password, get_user_settings, upload_and_update_avatar, refresh_user_info
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

# Avatar Upload Handler - COMPLETELY REWRITTEN for reliability
def handle_avatar_upload(username: str, uploaded_file: Any, crop_box: Any = None) -> None:
    """
    Handle avatar upload with aggressive session state update and cache clearing.
    Based on reference code pattern for immediate UI update.
    """
    ok, res = upload_and_update_avatar(username, uploaded_file, crop_box)
    if ok:
        st.success("✅ Đổi ảnh đại diện thành công!")
        
        user_id = st.session_state.user_info.get('id')
        
        # STEP 1: Update session_state IMMEDIATELY (like reference code)
        if 'user_info' not in st.session_state:
            st.session_state.user_info = {}
        
        # Force update avatar_url in session_state
        st.session_state.user_info['avatar_url'] = res
        logger.info(f"Updated session_state.user_info['avatar_url'] = {res[:80]}...")
        
        # STEP 2: Refresh from database to ensure consistency
        try:
            refresh_success = refresh_user_info(user_id)
            if refresh_success:
                # After refresh, ensure avatar_url is still set (in case refresh overwrote it)
                st.session_state.user_info['avatar_url'] = res
                logger.info(f"User info refreshed, avatar_url confirmed: {st.session_state.user_info.get('avatar_url', 'N/A')[:80]}...")
            else:
                logger.warning("refresh_user_info returned False, but continuing with session_state update")
        except Exception as e:
            logger.error(f"Error during refresh_user_info: {e}")
            # Continue anyway - we already updated session_state
        
        # STEP 3: Clear ALL caches that might affect avatar display
        if user_id:
            # Clear sidebar stats cache
            sidebar_cache_key = f'sidebar_stats_{user_id}'
            if sidebar_cache_key in st.session_state:
                del st.session_state[sidebar_cache_key]
                logger.info(f"Cleared {sidebar_cache_key}")
            
            # Clear all cache keys related to user
            cache_keys = [
                key for key in list(st.session_state.keys())
                if (
                    key.startswith('cache_user_info_') or 
                    key.startswith('cache_user_stats_') or
                    key.startswith('cache_') and str(user_id) in key
                )
            ]
            for key in cache_keys:
                try:
                    del st.session_state[key]
                    logger.info(f"Cleared cache key: {key}")
                except:
                    pass
        
        # STEP 4: Verify avatar_url is in session_state before rerun
        final_avatar_url = st.session_state.user_info.get('avatar_url')
        if final_avatar_url:
            logger.info(f"Final avatar_url in session_state before rerun: {final_avatar_url[:80]}...")
        else:
            logger.error("WARNING: avatar_url is NOT in session_state before rerun!")
            # Force set it one more time
            st.session_state.user_info['avatar_url'] = res
        
        # STEP 5: Rerun immediately (no sleep - like reference code)
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

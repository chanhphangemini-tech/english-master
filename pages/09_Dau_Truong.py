import streamlit as st
from typing import Dict, Any, Optional

from core.theme_applier import apply_page_theme
from core.debug_tools import render_debug_panel
from services.game_service import get_open_challenges, get_active_challenge
from views.pvp_view import (
    render_waiting_screen,
    render_game_interface,
    render_room_list,
    render_create_room_form
)

st.set_page_config(
    page_title="Đấu Trường PvP | English Master", 
    page_icon="⚔️", 
    layout="wide"
)

if not st.session_state.get('logged_in'):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

uid: int = st.session_state.user_info['id']

# --- CHECK ACTIVE GAME ---
active_match: Optional[Dict[str, Any]] = get_active_challenge(uid)

if active_match:
    # --- GAME INTERFACE ---
    st.title("⚔️ Đang Trong Trận Đấu")
    
    match_data: Dict[str, Any] = active_match
    is_creator: bool = (match_data['creator_id'] == uid)
    opponent_name: str = (
        match_data['Opponent']['name'] if is_creator 
        else match_data['Users']['name']
    )
    
    # Kiểm tra xem mình đã nộp bài chưa
    my_score_col = 'creator_score' if is_creator else 'challenger_score'
    my_current_score = match_data.get(my_score_col)
    
    if my_current_score is not None:
        # --- WAITING SCREEN ---
        render_waiting_screen(opponent_name, my_current_score)
    else:
        # --- PLAYING SCREEN ---
        render_game_interface(match_data, uid, is_creator, opponent_name)

    # --- DEBUG --- (Disabled)
    # render_debug_panel("PvP Active Match", {
    #     "match_id": match_data.get('id'),
    #     "status": match_data.get('status'),
    #     "scores": {
    #         "creator": match_data.get('creator_score'), 
    #         "challenger": match_data.get('challenger_score')
    #     }
    # })

else:
    # --- LOBBY INTERFACE ---
    st.title("⚔️ Đấu Trường Từ Vựng")
    st.caption("Thách đấu với người học khác để kiếm Coin và leo bảng xếp hạng.")

    tab1, tab2 = st.tabs(["Danh Sách Phòng", "Tạo Phòng Đấu"])

    with tab1:
        challenges = get_open_challenges(uid)
        render_room_list(uid, challenges)

    with tab2:
        render_create_room_form(uid)
    
    st.divider()
    st.markdown("### 🏆 Lịch sử đấu gần đây")
    st.caption("Chưa có dữ liệu trận đấu.")


import streamlit as st
import time
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import sys
import os

# --- CONFIGURATION ---
st.set_page_config(
    page_title="English Master | Học Tiếng Anh Từ Zero",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# --- PATH SETUP TO RESOLVE IMPORTS ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core modules
from core.data import (
    get_user_stats, 
    generate_daily_quests, 
    process_daily_streak, 
    get_leaderboard_english, 
    get_user_level_progress
)
from core.sidebar import render_sidebar
from core.global_theme import apply_global_theme
from core.session_manager import init_session_state
from core.debug_tools import render_debug_panel
from views.auth_view import render_auth_page
from views.dashboard_view import (
    render_hero_section,
    render_stats_bar,
    render_leaderboard,
    render_daily_quests,
    render_weekly_quests,
    render_level_mastery,
    render_user_guide
)
from views.learning_insights_view import render_learning_insights

# --- INIT ---
# apply_custom_theme()  # Disabled to use Streamlit default
# apply_beautiful_theme()  # Disabled to use Streamlit default
init_session_state()

# Load active theme from inventory if user is logged in
if st.session_state.get('logged_in'):
    try:
        from core.data import get_user_inventory
        user_id = st.session_state.user_info.get('id')
        if user_id:
            # Only load if not already set (to preserve theme changes)
            if 'active_theme_value' not in st.session_state or st.session_state.get('active_theme_value') is None:
                from core.data_cache import get_cached_inventory
                inventory = get_cached_inventory(user_id)
                active_theme = next((item['ShopItems']['value'] for item in inventory if item.get('is_active') and item.get('ShopItems', {}).get('type') == 'theme'), None)
                if active_theme:
                    st.session_state.active_theme_value = active_theme
    except Exception as e:
        # Silent fail - theme loading is not critical
        pass

apply_global_theme()  # Apply professional theme to all pages (now theme-aware)

# --- MAIN APP ---
if st.session_state.logged_in:
    user_info = st.session_state.user_info
    uid = user_info.get('id')
    
    # --- Page Navigation State ---
    st.session_state.active_page = "home"
    
    # Streak Logic (Delegated to Service)
    last_check = st.session_state.get('last_streak_check', 0)
    now_ts = time.time()
    if uid and (now_ts - last_check > 300):
        data = process_daily_streak(uid)
        if data:
            st.session_state.user_info['current_streak'] = data.get('current_streak', data.get('streak', 0))
            st.session_state.daily_progress = data.get('progress', "0/10")
            if data.get('status') == 'incremented':
                st.balloons()
                st.toast(data.get('message'), icon="🔥")
            
            # Check for milestone achievements
            milestones = data.get('milestones', [])
            if milestones:
                for milestone in milestones:
                    milestone_name = milestone.get('name', f"{milestone.get('milestone_days', 0)} Days")
                    coins = milestone.get('coins', 0)
                    reward_text = f"🎉 Chúc mừng! Bạn đã đạt milestone {milestone_name}!"
                    if coins > 0:
                        reward_text += f" Nhận {coins} coins!"
                    st.balloons()
                    st.success(reward_text)
        st.session_state.last_streak_check = now_ts

    render_sidebar()
    
    # Load Stats (sử dụng cached data để tránh reload)
    from core.data_cache import get_cached_user_stats
    stats = get_cached_user_stats(uid)

    # --- PLACEMENT TEST PROMPT ---
    if stats.get('latest_test_score') is None:
        user_name = user_info.get('name') or user_info.get('username', 'bạn')
        st.info(f"👋 Chào {user_name}! Bạn chưa biết trình độ của mình?")
        if st.button("🎯 Làm bài kiểm tra đầu vào ngay", type="primary"):
            st.switch_page("pages/00_Kiem_Tra_Dau_Vao.py")
        st.divider()

    # --- HERO SECTION ---
    render_hero_section()

    # --- STATS BAR ---
    current_streak = st.session_state.user_info.get('current_streak', stats.get('current_streak', stats.get('streak', 0)))
    render_stats_bar(stats, current_streak)

    st.divider()

    # --- LEADERBOARD ---
    lb_data = get_leaderboard_english()
    render_leaderboard(lb_data)

    st.divider()

    # --- DAILY QUESTS ---
    from core.timezone_utils import get_vn_today_str
    today_str = get_vn_today_str()
    quest_cache_key = f"daily_quests_{uid}_{today_str}"

    if quest_cache_key not in st.session_state:
        st.session_state[quest_cache_key] = generate_daily_quests(uid)
    
    quests = st.session_state[quest_cache_key]
    render_daily_quests(quests, uid)
    
    st.divider()
    
    # --- WEEKLY QUESTS ---
    render_weekly_quests(uid)

    # --- DEBUG: QUESTS --- (Disabled for production)
    # render_debug_panel("Daily Quests", {
    #     "user_id": uid,
    #     "quests_data": quests,
    #     "cache_key": quest_cache_key
    # })

    # --- LEVEL MASTERY DASHBOARD ---
    from core.data_cache import get_cached_level_progress
    level_progress = get_cached_level_progress(uid)
    render_level_mastery(level_progress)

    st.divider()

    # --- LEARNING INSIGHTS (AI-Powered Recommendations) ---
    # Lazy load - only show if user expands or scrolls
    with st.expander("💡 Gợi Ý Học Tập (AI)", expanded=False):
        render_learning_insights(uid, days=30)

    st.divider()

    # --- USER GUIDE ---
    render_user_guide()

else:
    render_auth_page()

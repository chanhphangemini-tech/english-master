import streamlit as st
from typing import Dict, Any, Tuple
import logging

from core.theme_applier import apply_page_theme
from services.grammar_service import (
    load_grammar_progress, 
    get_theory_cache,
    load_grammar_lessons_from_db
)
from views.grammar_view import (
    render_grammar_guide,
    render_level_selector,
    render_level_progress,
    render_unit_selector,
    render_unit_header,
    render_theory_tab,
    render_test_tab,
    render_drill_tab
)

logger = logging.getLogger(__name__)

# --- AUTH CHECK ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth
user_id: int = st.session_state.user_info.get("id")
user_role: str = str(st.session_state.user_info.get("role", "user")).lower()
user_plan: str = str(st.session_state.user_info.get("plan", "free")).lower()
is_admin: bool = (user_role == "admin")

# --- CONSTANTS & CONFIG ---
LEVEL_MAP: Dict[str, str] = {
    "A1 (Foundation)": "A1", "A2 (Elementary)": "A2",
    "B1 (Intermediate)": "B1", "B2 (Upper-Intermediate)": "B2",
    "C1 (Advanced)": "C1", "C2 (Proficiency)": "C2"
}

def get_prog(lvl_code: str, units: Dict) -> Tuple[int, int]:
    """Get progress for a level."""
    if not units:
        return 0, 0
    if 'grammar_progress' not in st.session_state:
        st.session_state.grammar_progress = load_grammar_progress(user_id)
    
    done = sum(1 for k in units if f"{lvl_code}_{k}" in st.session_state.grammar_progress)
    return done, len(units)

def is_unlocked(target_code: str) -> bool:
    """Check if a level is unlocked."""
    if is_admin:
        return True
    codes = list(LEVEL_MAP.values())
    idx = codes.index(target_code)
    if idx == 0:
        return True
    prev_code = codes[idx-1]
    prev_data = load_grammar_lessons_from_db(prev_code)
    if not prev_data:
        return False 
    d, t = get_prog(prev_code, prev_data)
    return d == t and t > 0

# --- Page State Reset ---
PAGE_ID = "grammar_page"
if st.session_state.get('active_page') != PAGE_ID:
    # Reset quiz and other temporary states when navigating to this page
    st.session_state.test_quiz = []
    st.session_state.test_score = None
    if 'drill_quiz' in st.session_state:
        del st.session_state.drill_quiz
st.session_state.active_page = PAGE_ID

# --- MAIN PAGE LOGIC ---
st.title("🧩 Ngữ Pháp Toàn Diện")

# 1. Guide
render_grammar_guide()

# 2. Level Selection
curr_code, selected_label = render_level_selector(LEVEL_MAP, is_unlocked, is_admin)

# --- PREMIUM CHECK ---
if curr_code not in ["A1", "A2"] and user_plan != 'premium' and not is_admin:
    st.warning("🔒 Đây là nội dung dành cho tài khoản Premium.")
    st.info("Nâng cấp lên Premium để mở khóa toàn bộ bài học ngữ pháp và các tính năng nâng cao khác!")
    if st.button("⭐ Nâng cấp Premium ngay", type="primary"):
        st.switch_page("pages/15_Premium.py")
    st.stop()

# Check lock
if "🔒" in selected_label and not is_admin:
    st.warning(f"🔒 Cấp độ {curr_code} đang bị khóa. Hãy hoàn thành cấp độ trước đó.")
    st.stop()

# Load Units
units = load_grammar_lessons_from_db(curr_code)
if not units:
    st.error(f"⚠️ Không tìm thấy dữ liệu cho {curr_code}")
    st.stop()

# Progress Bar
render_level_progress(curr_code, units, get_prog)

st.divider()

# 3. Unit Selection
u_key, u_data = render_unit_selector(units, curr_code, st.session_state.grammar_progress)

if u_key:
    # Header
    render_unit_header(u_data['title'], u_data['desc'])
    
    # Tabs Navigation
    TAB_OPTIONS = ["📖 Lý thuyết", "✅ Kiểm tra (Pass/Fail)", "♾️ Luyện tập sâu"]
    if "current_grammar_tab" not in st.session_state:
        st.session_state.current_grammar_tab = TAB_OPTIONS[0]

    selected_tab = st.radio(
        "Chọn chế độ:", 
        TAB_OPTIONS, 
        horizontal=True, 
        label_visibility="collapsed", 
        key="current_grammar_tab"
    )
    st.divider()

    # --- TAB 1: THEORY ---
    if selected_tab == TAB_OPTIONS[0]:
        cached_lecture = get_theory_cache(curr_code, u_key)
        render_theory_tab(user_id, curr_code, u_key, u_data, cached_lecture, is_admin)

    # --- TAB 2: TEST ---
    elif selected_tab == TAB_OPTIONS[1]:
        unit_full_id = f"{curr_code}_{u_key}"
        render_test_tab(user_id, curr_code, u_key, u_data, unit_full_id, st.session_state.grammar_progress)

    # --- TAB 3: DRILL ---
    elif selected_tab == TAB_OPTIONS[2]:
        render_drill_tab(curr_code, u_data)

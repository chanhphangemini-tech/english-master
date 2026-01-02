import streamlit as st
import random
import time
from typing import Dict, Any, List

from core.theme_applier import apply_page_theme
from services.vocab_service import get_irregular_verbs_list
from views.irregular_verbs_view import (
    render_learn_tab,
    render_question_card,
    render_penalty_card,
    validate_penalty_input,
    validate_verb_forms,
    render_streak_display
)

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

st.title("🔥 Động Từ Bất Quy Tắc (Irregular Verbs)")
st.caption("Phương pháp: Chia nhóm quy luật + Chép phạt để ghi nhớ vĩnh viễn.")

RAW_DATA: List[Dict[str, Any]] = get_irregular_verbs_list()

PAGE_ID = "irregular_verbs"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.irr_mode = 'learn'
    st.session_state.irr_current_q = None
    st.session_state.irr_penalty_count = 0
    st.session_state.irr_streak = 0
st.session_state.active_page = PAGE_ID

# --- TABS ---
tab_learn, tab_drill = st.tabs(["📖 Học theo nhóm", "✍️ Luyện tập"])

# --- TAB 1: LEARN ---
with tab_learn:
    render_learn_tab(RAW_DATA)

# --- TAB 2: DRILL ---
with tab_drill:
    st.markdown("### 🛡️ Đấu trường trí nhớ")
    
    # Init Question
    if st.session_state.irr_current_q is None:
        st.session_state.irr_current_q = random.choice(RAW_DATA)
        st.session_state.irr_penalty_count = 0
    
    q = st.session_state.irr_current_q
    
    # --- PENALTY MODE ---
    if st.session_state.irr_penalty_count > 0:
        render_penalty_card(q, st.session_state.irr_penalty_count)
        
        with st.form("penalty_form"):
            u_input = st.text_input("Gõ lại (V1 V2 V3):", placeholder=f"Ví dụ: {q['base']} {q['v2']} {q['v3']}")
            if st.form_submit_button("Nộp phạt"):
                expected = f"{q['base']} {q['v2']} {q['v3']}"
                if validate_penalty_input(u_input, expected):
                    st.session_state.irr_penalty_count -= 1
                    if st.session_state.irr_penalty_count == 0:
                        st.success("🎉 Tốt lắm! Bạn đã được tha.")
                        time.sleep(1)
                        st.session_state.irr_current_q = random.choice(RAW_DATA)
                        st.rerun()
                    else:
                        st.warning(f"Đúng rồi. Còn {st.session_state.irr_penalty_count} lần nữa.")
                        st.rerun()
                else:
                    st.error(f"Chưa đúng. Hãy gõ chính xác: {expected}")
    
    # --- NORMAL MODE ---
    else:
        # Score Board
        render_streak_display(st.session_state.irr_streak)
        
        # Question Card
        render_question_card(q)
        
        with st.form("drill_form"):
            c1, c2 = st.columns(2)
            v2_in = c1.text_input("V2 (Quá khứ đơn)", placeholder="???")
            v3_in = c2.text_input("V3 (Quá khứ phân từ)", placeholder="???")
            
            if st.form_submit_button("Kiểm tra", type="primary"):
                is_v2_ok, is_v3_ok = validate_verb_forms(v2_in, v3_in, q['v2'], q['v3'])
                
                if is_v2_ok and is_v3_ok:
                    st.balloons()
                    st.success("✅ Chính xác! Quá đỉnh.")
                    st.session_state.irr_streak += 1
                    time.sleep(1)
                    st.session_state.irr_current_q = random.choice(RAW_DATA)
                    st.rerun()
                else:
                    st.session_state.irr_streak = 0
                    st.session_state.irr_penalty_count = 3  # Phạt chép 3 lần
                    st.rerun()
        
        if st.button("Bỏ qua (Sẽ mất chuỗi)"):
            st.session_state.irr_streak = 0
            st.session_state.irr_current_q = random.choice(RAW_DATA)
            st.rerun()


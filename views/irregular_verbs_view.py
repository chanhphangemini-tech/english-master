"""View components for Irregular Verbs page."""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional


def render_learn_tab(verbs_data: List[Dict[str, Any]]) -> None:
    """Render the learning tab with verb groups.
    
    Args:
        verbs_data: List of irregular verbs data
    """
    st.markdown("### 🧠 Chia để trị")
    st.info("Mẹo: Hãy học thuộc từng nhóm một. Đừng cố học hết cùng lúc.")
    
    group_filter = st.selectbox(
        "Chọn nhóm:", 
        [
            "Tất cả", 
            "AAA (3 cột giống nhau)", 
            "ABB (Cột 2, 3 giống nhau)", 
            "ABC (Khác nhau)", 
            "ABA (Cột 1, 3 giống nhau)"
        ]
    )
    
    df = pd.DataFrame(verbs_data)
    
    if group_filter != "Tất cả":
        code = group_filter.split()[0]
        df_show = df[df['group'] == code]
    else:
        df_show = df
        
    # Display Table
    st.dataframe(
        df_show[['base', 'v2', 'v3', 'meaning', 'group']], 
        column_config={
            "base": "V1 (Nguyên mẫu)",
            "v2": "V2 (Quá khứ)",
            "v3": "V3 (Phân từ 2)",
            "meaning": "Nghĩa",
            "group": "Nhóm"
        },
        width='stretch',
        hide_index=True,
        height=500
    )


def render_question_card(verb: Dict[str, Any]) -> None:
    """Render the question card for drill mode.
    
    Args:
        verb: Current verb to quiz
    """
    st.markdown(f"""
    <div style="text-align:center; padding: 30px; background: #e3f2fd; border-radius: 15px; margin-bottom: 20px;">
        <div style="font-size: 1.2em; color: #555;">Từ nguyên mẫu (V1)</div>
        <div style="font-size: 3em; font-weight: bold; color: #003366;">{verb['base']}</div>
        <div style="font-size: 1.2em; color: #333;">({verb['meaning']})</div>
    </div>
    """, unsafe_allow_html=True)


def render_penalty_card(verb: Dict[str, Any], penalty_count: int) -> None:
    """Render penalty card when user makes mistake.
    
    Args:
        verb: Verb that was answered incorrectly
        penalty_count: Number of remaining penalties
    """
    st.error(f"⛔ BẠN ĐÃ SAI! HÃY CHÉP PHẠT ĐỂ NHỚ.")
    st.markdown(f"""
    <div style="background:#ffebee; padding:20px; border-radius:10px; border:1px solid #ffcdd2; text-align:center;">
        <h3 style="color:#c62828; margin:0;">{verb['base']} - {verb['v2']} - {verb['v3']}</h3>
        <p>Nghĩa: {verb['meaning']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write(f"📝 Bạn cần chép lại đúng **{penalty_count}** lần nữa.")


def validate_penalty_input(user_input: str, expected: str) -> bool:
    """Validate penalty input.
    
    Args:
        user_input: User's input
        expected: Expected correct answer
        
    Returns:
        True if input matches expected
    """
    return user_input.strip().lower() == expected.lower()


def validate_verb_forms(v2_input: str, v3_input: str, correct_v2: str, correct_v3: str) -> tuple:
    """Validate verb forms input.
    
    Args:
        v2_input: User's V2 input
        v3_input: User's V3 input
        correct_v2: Correct V2 form
        correct_v3: Correct V3 form
        
    Returns:
        Tuple of (is_v2_correct, is_v3_correct)
    """
    is_v2_ok = v2_input.strip().lower() == correct_v2.lower()
    is_v3_ok = v3_input.strip().lower() == correct_v3.lower()
    return is_v2_ok, is_v3_ok


def render_streak_display(streak: int) -> None:
    """Render streak counter.
    
    Args:
        streak: Current streak count
    """
    st.markdown(f"🔥 Chuỗi đúng liên tiếp: **{streak}**")


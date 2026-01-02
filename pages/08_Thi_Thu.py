import streamlit as st
from typing import Dict, Any
import logging
import time

from core.theme_applier import apply_page_theme

apply_page_theme()  # Apply theme + sidebar + auth
from core.theme import apply_custom_theme
from core.debug_tools import render_debug_panel
from core.llm import generate_response_with_fallback, parse_json_response
from views.mock_test_view import (
    render_test_intro,
    render_test_config,
    render_exam_timer,
    render_exam_sidebar_warning,
    render_listening_section,
    render_reading_section,
    render_writing_section,
    render_speaking_section,
    render_result_section
)

logger = logging.getLogger(__name__)

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

user_id: int = st.session_state.user_info.get("id")

# --- Page State Reset Logic ---
PAGE_ID = "mock_exam"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.exam_state = 'intro'
    st.session_state.exam_data = {}
    st.session_state.exam_answers = {}
    st.session_state.exam_start_time = None
st.session_state.active_page = PAGE_ID

# --- State Management ---
if 'exam_mode' not in st.session_state:
    st.session_state.exam_mode = "mini"

# --- EXAM MODE LOGIC (Fullscreen & Lockdown) ---
is_exam_running = st.session_state.exam_state not in ['intro', 'result']

if is_exam_running:
    apply_custom_theme()
    
    # JS for fullscreen and hide nav
    st.markdown("""
    <script>
        var elem = document.documentElement;
        if (!document.fullscreenElement) {
            if (elem.requestFullscreen) { elem.requestFullscreen().catch(err => {}); }
            else if (elem.webkitRequestFullscreen) { elem.webkitRequestFullscreen(); }
            else if (elem.msRequestFullscreen) { elem.msRequestFullscreen(); }
        }
    </script>
    <style>
        [data-testid="stSidebarNav"] {display: none !important;}
        header {visibility: hidden;}
        [data-testid="stSidebar"] { background-color: #fff3cd; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.exam_start_time:
            render_exam_timer(st.session_state.exam_start_time, st.session_state.exam_duration)
        
        if render_exam_sidebar_warning():
            st.session_state.exam_state = 'intro'
            st.session_state.exam_data = {}
            st.session_state.exam_answers = {}
            st.session_state.exam_level = None
            st.session_state.exam_start_time = None
            if 'exam_audio_bytes' in st.session_state:
                del st.session_state['exam_audio_bytes']
            st.rerun()

st.title("📝 Thi Thử (Mock Test)")
st.caption("Mô phỏng bài thi 4 kỹ năng (Nghe, Đọc, Viết, Nói) được chấm điểm bởi AI.")

# --- Helper Functions ---
def start_exam(level: str, mode: str) -> None:
    """Start a new exam with given configuration."""
    st.session_state.exam_level = level
    st.session_state.exam_mode = mode
    
    # Configure exam
    if mode == "full":
        st.session_state.exam_duration = 45 * 60
        n_lis, n_read = 3, 3
        len_lis, len_read = "150-200", "250-300"
    else:  # mini
        st.session_state.exam_duration = 10 * 60
        n_lis, n_read = 1, 1
        len_lis, len_read = "50-80", "100-150"

    with st.spinner(f"AI đang thiết kế đề thi {mode.upper()} ({level})..."):
        try:
            # Generate exam content
            p_lis = f"""
            Create a listening script ({len_lis} words) for Level {level}. Topic: Daily Life.
            Create {n_lis} multiple-choice questions based on it.
            Return JSON: {{
                "script": "...",
                "questions": [
                    {{"q": "Question text", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Explanation in Vietnamese"}}
                ]
            }}
            """
            res_lis = generate_response_with_fallback(p_lis, ["ERROR"])
            listening = parse_json_response(res_lis)

            p_read = f"""
            Create a reading passage ({len_read} words) for Level {level}. Topic: General Knowledge.
            Create {n_read} multiple-choice questions.
            Return JSON: {{
                "passage": "...",
                "questions": [
                    {{"q": "Question text", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Explanation in Vietnamese"}}
                ]
            }}
            """
            res_read = generate_response_with_fallback(p_read, ["ERROR"])
            reading = parse_json_response(res_read)

            writing_prompt = generate_response_with_fallback(
                f"Generate a short writing topic for Level {level}. Return only the topic text."
            )
            speaking_prompt = generate_response_with_fallback(
                f"Generate a short speaking discussion topic for Level {level}. Return only the topic text."
            )
            
            if all([listening, reading, writing_prompt, speaking_prompt]):
                st.session_state.exam_data = {
                    'listening': listening,
                    'reading': reading,
                    'writing_prompt': writing_prompt,
                    'speaking_prompt': speaking_prompt
                }
                st.session_state.exam_state = 'listening'
                st.session_state.exam_start_time = time.time()
                st.rerun()
            else:
                st.error("Không thể tạo đề thi lúc này. Vui lòng thử lại.")
                logger.error(f"Failed to generate exam for level {level}")
        except Exception as e:
            st.error(f"Lỗi khi tạo đề: {e}")
            logger.error(f"Exam generation error: {e}")

# --- UI Stages ---

# 1. INTRO
if st.session_state.exam_state == 'intro':
    render_test_intro()
    
    level, mode_code = render_test_config()
    
    if st.button("🚀 Bắt đầu làm bài", type="primary"):
        start_exam(level, mode_code)
    
    # --- DEBUG --- (Disabled)
    # render_debug_panel("Exam Generation", {
    #     "level": level,
    #     "mode": mode_code
    # })

# 2. LISTENING
elif st.session_state.exam_state == 'listening':
    data = st.session_state.exam_data['listening']
    user_answers = render_listening_section(data)
    
    if user_answers is not None:
        st.session_state.exam_answers['listening'] = user_answers
        st.session_state.exam_state = 'reading'
        if 'exam_audio_bytes' in st.session_state:
            del st.session_state['exam_audio_bytes']
        st.rerun()

# 3. READING
elif st.session_state.exam_state == 'reading':
    data = st.session_state.exam_data['reading']
    user_answers = render_reading_section(data)
    
    if user_answers is not None:
        st.session_state.exam_answers['reading'] = user_answers
        st.session_state.exam_state = 'writing'
        st.rerun()

# 4. WRITING
elif st.session_state.exam_state == 'writing':
    prompt = st.session_state.exam_data['writing_prompt']
    user_text = render_writing_section(prompt)
    
    if user_text is not None:
        st.session_state.exam_answers['writing'] = user_text
        st.session_state.exam_state = 'speaking'
        st.rerun()

# 5. SPEAKING
elif st.session_state.exam_state == 'speaking':
    prompt = st.session_state.exam_data['speaking_prompt']
    user_transcript = render_speaking_section(prompt)
    
    if user_transcript is not None:
        st.session_state.exam_answers['speaking'] = user_transcript
        st.session_state.exam_state = 'result'
        st.rerun()

# 6. RESULT
elif st.session_state.exam_state == 'result':
    data = st.session_state.exam_data
    answers = st.session_state.exam_answers
    level = st.session_state.exam_level
    
    render_result_section(data, answers, level, user_id)

    if st.button("Làm bài thi mới"):
        # Reset all exam state
        st.session_state.exam_state = 'intro'
        st.session_state.exam_data = {}
        st.session_state.exam_answers = {}
        st.session_state.exam_level = None
        st.session_state.exam_start_time = None
        if 'exam_audio_bytes' in st.session_state:
            del st.session_state['exam_audio_bytes']
        st.rerun()

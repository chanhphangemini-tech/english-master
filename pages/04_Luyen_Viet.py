import streamlit as st
import string
from core.theme_applier import apply_page_theme

apply_page_theme()  # Apply theme + sidebar + auth (includes render_sidebar)
from core.llm import generate_response_with_fallback, parse_json_response
from core.premium import can_use_ai_feature, log_ai_usage, show_premium_upsell
from services.skill_tracking_service import track_skill_progress
from services.exercise_cache_service import get_unseen_exercise, save_exercise, mark_exercise_seen, mark_exercise_completed

st.title("✍️ Phòng Luyện Viết (Writing)")

PAGE_ID = "writing_page"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.writing_tab = "📝 Viết câu"
    st.session_state.w_sentence_data = None
    st.session_state.w_essay_feedback = None
    st.session_state.we_topic = "Describe your favorite hobby"
st.session_state.active_page = PAGE_ID

# --- CSS STYLING ---
st.markdown("""
<style>
div.row-widget.stRadio > div {flex-direction: row; gap: 10px; justify-content: center; margin-bottom: 20px;}
div.row-widget.stRadio > div > label {
    background-color: #ffffff; padding: 8px 20px; border-radius: 20px; 
    cursor: pointer; border: 1px solid #e0e0e0; font-weight: 500;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
div.row-widget.stRadio > div > label[data-baseweb="radio"] {
    background-color: #e3f2fd; border-color: #2196f3; color: #1565c0; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
options = ["📝 Viết câu", "📄 Viết đoạn văn", "🤖 Sửa lỗi AI"]
selected = st.radio("Menu", options, horizontal=True, label_visibility="collapsed", key="writing_tab")
st.divider()

# --- TAB 1: SENTENCE SCRAMBLE ---
if selected == "📝 Viết câu":
    st.subheader("Sắp xếp từ thành câu hoàn chỉnh")
    
    c1, c2 = st.columns([1, 1])
    level = c1.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1"], key="ws_lvl")
    
    if can_use_ai_feature("writing"):
        user_id = st.session_state.get("user_info", {}).get("id")
        
        if c2.button("🎲 Tạo câu mới", type="primary", width='stretch'):
            # Try to get from cache first
            cached_exercise = None
            if user_id:
                with st.spinner("Đang tìm câu từ kho lưu trữ..."):
                    cached_exercise = get_unseen_exercise(user_id, "word_scramble", level, topic=None)
                    if cached_exercise:
                        exercise_id = cached_exercise.get('id')
                        data = cached_exercise.get('exercise_data', {})
                        if data and "original" in data:
                            mark_exercise_seen(user_id, exercise_id)
                            st.session_state.w_sentence_data = data
                            st.session_state.w_sentence_exercise_id = exercise_id  # Store for completion tracking
                            st.rerun()
            
            # If not in cache, generate new
            if not cached_exercise or not cached_exercise.get('exercise_data'):
                with st.spinner("AI đang xáo trộn từ..."):
                    prompt = f"""
                    Generate 1 English sentence (Level {level}). 
                    Scramble the words randomly separated by ' / '.
                    Return JSON: {{"original": "Full correct sentence.", "scrambled": "Word / word / ...", "vietnamese": "Meaning"}}
                    """
                    res = generate_response_with_fallback(prompt, ["ERROR"])
                    data = parse_json_response(res)
                    if data and "original" in data:
                        log_ai_usage("writing")
                        st.session_state.w_sentence_data = data
                        
                        # Save to cache
                        if user_id:
                            try:
                                exercise_id = save_exercise(
                                    exercise_type="word_scramble",
                                    level=level,
                                    topic=None,  # Word scramble doesn't have specific topic
                                    exercise_data=data,
                                    user_id=user_id
                                )
                                if exercise_id:
                                    mark_exercise_seen(user_id, exercise_id)
                                    st.session_state.w_sentence_exercise_id = exercise_id  # Store for completion tracking
                            except Exception as e:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.warning(f"Error saving word scramble to cache: {e}")
                        st.rerun()
    else:
        with c2:
            show_premium_upsell("Tạo câu mới", "writing")
    
    if st.session_state.w_sentence_data:
        data = st.session_state.w_sentence_data
        st.info(f"🔀 **{data['scrambled']}**")
        st.caption(f"Gợi ý: {data['vietnamese']}")
        
        u_in = st.text_input("Viết lại câu đúng:", key="ws_input")
        
        if st.button("Kiểm tra"):
            # Normalize strings for comparison
            translator = str.maketrans('', '', string.punctuation)
            clean_u = u_in.strip().lower().translate(translator)
            clean_a = data['original'].strip().lower().translate(translator)
            
            user_id = st.session_state.get("user_info", {}).get("id")
            if clean_u == clean_a:
                st.balloons()
                st.success("Chính xác! 🌟")
                # Mark exercise as completed and track skill progress
                if user_id and st.session_state.get('w_sentence_exercise_id'):
                    try:
                        mark_exercise_completed(user_id, st.session_state.w_sentence_exercise_id, score=100)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Error marking word scramble as completed: {e}")
                if user_id:
                    track_skill_progress(user_id, 'writing', 1, 1)  # 1 exercise, 1 correct
            else:
                st.error(f"Sai rồi. Đáp án đúng: {data['original']}")
                # Track skill progress (0 correct)
                if user_id:
                    track_skill_progress(user_id, 'writing', 1, 0)

# --- TAB 2: ESSAY WRITING ---
elif selected == "📄 Viết đoạn văn":
    st.subheader("Luyện viết theo chủ đề (IELTS/TOEIC style)")
    
    c1, c2 = st.columns([1, 2])
    level = c1.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1", "C2"], key="we_lvl")
    
    if can_use_ai_feature("writing"):
        if c2.button("🎲 AI Chọn Chủ Đề Mới", type="secondary", width='stretch'):
            with st.spinner("AI đang tìm chủ đề hay..."):
                prompt = f"Generate a short, engaging writing topic/question for English learners at Level {level}. Return only the topic text."
                res = generate_response_with_fallback(prompt)
                if res:
                    log_ai_usage("writing")
                    st.session_state.we_topic = res.strip().replace('"', '')
                    st.rerun()
    else:
        with c2:
            show_premium_upsell("Tạo chủ đề mới", "writing")

    st.info(f"📝 **Chủ đề:** {st.session_state.we_topic}")
    
    user_text = st.text_area("Bài viết của bạn:", height=200, placeholder=f"Write about: {st.session_state.we_topic}")
    word_count = len(user_text.split())
    st.caption(f"Số từ: {word_count}")
    
    if can_use_ai_feature("writing"):
        if st.button("📝 Chấm điểm & Sửa lỗi (AI)", type="primary"):
            if word_count < 10:
                st.warning("Bài viết quá ngắn.")
            else:
                with st.spinner("AI đang chấm bài..."):
                    prompt = f"""
                    Act as an English teacher. Grade this writing (Level {level}) on topic '{st.session_state.we_topic}'.
                    Content: '''{user_text}'''
                    Return JSON: {{
                        "score": "X/10",
                        "comment": "General feedback in Vietnamese",
                        "corrected": "Corrected version of the text",
                        "mistakes": [
                            {{"error": "wrong part", "fix": "correction", "explain": "why in Vietnamese"}}
                        ]
                    }}
                    """
                    res = generate_response_with_fallback(prompt)
                    data = parse_json_response(res)
                    log_ai_usage("writing")
                    st.session_state.w_essay_feedback = data
                    # Track skill progress for essay writing
                    user_id = st.session_state.get("user_info", {}).get("id")
                    if user_id and data:
                        # Extract score (e.g., "8/10" -> 8)
                        score_str = data.get('score', '0/10').split('/')[0]
                        try:
                            score_val = int(score_str) if score_str.isdigit() else 0
                            # Convert score to accuracy (0.0 to 1.0)
                            accuracy = score_val / 10.0 if score_val <= 10 else 1.0
                            track_skill_progress(user_id, 'writing', 1, accuracy)  # Score as accuracy
                        except:
                            track_skill_progress(user_id, 'writing', 1, 0.5)  # Default accuracy if parsing fails
    else:
        show_premium_upsell("Chấm điểm AI", "writing")
    
    if st.session_state.w_essay_feedback:
        fb = st.session_state.w_essay_feedback
        st.divider()
        c_score, c_comment = st.columns([1, 3])
        c_score.metric("Điểm số", fb.get('score', 'N/A'))
        c_comment.info(fb.get('comment', ''))
        
        with st.expander("🔍 Xem bài sửa chi tiết", expanded=True):
            st.markdown("### Bản đã sửa:")
            st.success(fb.get('corrected', ''))
            
            st.markdown("### Các lỗi sai:")
            for m in fb.get('mistakes', []):
                st.markdown(f"- ❌ **{m.get('error')}** ➔ ✅ **{m.get('fix')}**")
                st.caption(f"   💡 {m.get('explain')}")

# --- TAB 3: AI CORRECTION ---
elif selected == "🤖 Sửa lỗi AI":
    st.subheader("Công cụ sửa lỗi ngữ pháp tức thì")
    inp = st.text_area("Nhập câu/đoạn văn cần sửa:", height=150)
    
    if can_use_ai_feature("writing"):
        if st.button("✨ Phân tích & Sửa lỗi", type="primary"):
            if not inp:
                st.warning("Vui lòng nhập nội dung.")
            else:
                with st.spinner("AI đang phân tích..."):
                    prompt = f"""
                    Correct grammar and spelling for this text. Explain errors in Vietnamese.
                    Return JSON: {{"corrected": "...", "explanation": "..."}}
                    """
                    res = generate_response_with_fallback(prompt + f"\nText: {inp}")
                    data = parse_json_response(res)
                    
                    if data:
                        log_ai_usage("writing")
                        st.markdown("### Kết quả:")
                        st.success(data.get('corrected'))
                        st.info(f"💡 **Giải thích:** {data.get('explanation')}")
                        # Track skill progress for AI correction
                        user_id = st.session_state.get("user_info", {}).get("id")
                        if user_id:
                            # For AI correction, we assume 1 exercise completed with nominal accuracy
                            track_skill_progress(user_id, 'writing', 1, 1)  # Assume correction means successful engagement
    else:
        show_premium_upsell("Sửa lỗi AI", "writing")
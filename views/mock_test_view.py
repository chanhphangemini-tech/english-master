"""View components for Mock Test page."""
import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any, List, Optional
import time


def render_test_intro() -> None:
    """Render mock test introduction and structure."""
    st.subheader("Cấu trúc bài thi")
    st.markdown("""
    - **Phần 1: Nghe (Listening)** - 1 bài nghe ngắn & câu hỏi trắc nghiệm.
    - **Phần 2: Đọc (Reading)** - 1 đoạn văn & câu hỏi đọc hiểu.
    - **Phần 3: Viết (Writing)** - Viết một đoạn văn ngắn theo chủ đề.
    - **Phần 4: Nói (Speaking)** - Ghi âm câu trả lời cho một chủ đề.
    """)


def render_test_config() -> tuple[str, str]:
    """Render test configuration (level and mode selection).
    
    Returns:
        Tuple of (level, mode_code)
    """
    c1, c2 = st.columns(2)
    level = c1.selectbox("Chọn cấp độ thi:", ["A1", "A2", "B1", "B2", "C1", "C2"])
    mode = c2.selectbox("Chế độ thi:", ["Mini Exam (10 phút)", "Full Exam (45 phút)"])
    
    mode_code = "mini" if "Mini" in mode else "full"
    return level, mode_code


def render_exam_timer(exam_start_time: float, exam_duration: float) -> None:
    """Render countdown timer for exam.
    
    Args:
        exam_start_time: Timestamp when exam started
        exam_duration: Duration of exam in seconds
    """
    # Check for timeout on Python side
    elapsed = time.time() - exam_start_time
    remaining = exam_duration - elapsed
    if remaining <= 0 and st.session_state.exam_state != 'result':
        st.session_state.exam_state = 'result'
        st.rerun()

    end_timestamp_ms = (exam_start_time + exam_duration) * 1000
    tick_url = "https://assets.mixkit.co/active_storage/sfx/2571/2571-preview.mp3"
    
    timer_html = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px;">Thời gian còn lại</div>
        <div id="exam_timer_display" style="font-size: 36px; font-weight: 800; color: #003366; font-family: monospace;">--:--</div>
    </div>
    <script>
        var end_time = {end_timestamp_ms};
        var tickSound = new Audio('{tick_url}');
        var timer_display = document.getElementById("exam_timer_display");

        var timerInterval = setInterval(function() {{
            var now = new Date().getTime();
            var distance = end_time - now;

            if (distance < 0) {{
                clearInterval(timerInterval);
                if(timer_display) timer_display.innerHTML = "00:00";
                window.parent.location.reload();
                return;
            }}

            var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((distance % (1000 * 60)) / 1000);

            if(timer_display) timer_display.innerHTML = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);

            if (distance < 60000) {{
                if(timer_display) timer_display.style.color = "#d63031";
            }}

            if (distance <= 10500 && distance > 0) {{
                tickSound.play().catch(function(e) {{}});
            }}
        }}, 1000);
    </script>
    """
    components.html(timer_html, height=100)


def render_exam_sidebar_warning() -> bool:
    """Render sidebar warning during exam.
    
    Returns:
        True if user wants to cancel exam
    """
    st.error("⚠️ ĐANG LÀM BÀI THI")
    st.warning("Bạn không thể chuyển trang khi đang làm bài.")
    st.info("Nếu muốn thoát, bạn phải hủy kết quả bài thi này.")
    
    return st.button("🛑 Hủy bài & Thoát", type="primary")


def render_listening_section(data: Dict[str, Any]) -> Dict[int, str]:
    """Render listening section with audio and questions.
    
    Args:
        data: Listening section data
        
    Returns:
        Dictionary of user answers
    """
    from core.tts import get_tts_audio
    import logging
    
    logger = logging.getLogger(__name__)
    
    st.subheader("Phần 1: Nghe (Listening)")
    st.progress(0.25, text="Tiến độ: 25%")
    
    # Generate and play audio (cached)
    with st.spinner("Đang tạo âm thanh..."):
        if 'exam_audio_bytes' not in st.session_state:
            try:
                st.session_state.exam_audio_bytes = get_tts_audio(data['script'])
            except Exception as e:
                logger.error(f"TTS Error: {e}")
                st.session_state.exam_audio_bytes = None
            
        if st.session_state.exam_audio_bytes:
            st.audio(st.session_state.exam_audio_bytes, format='audio/mp3')
        else:
            st.warning("Không thể tạo âm thanh cho bài nghe. Vui lòng đọc transcript bên dưới.")
    
    # Questions
    questions = data.get('questions', [])
    if not questions and 'question' in data:
        questions = [{
            'q': data['question'],
            'options': data.get('options', []),
            'answer': data.get('answer'),
            'explanation': data.get('explanation')
        }]
    
    user_answers = {}
    with st.form("listening_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**Câu {i+1}: {q['q']}**")
            user_answers[i] = st.radio(
                f"Chọn đáp án câu {i+1}:", 
                q['options'], 
                key=f"lis_q_{i}", 
                index=None
            )
            st.markdown("---")
        
        submitted = st.form_submit_button("Tiếp tục sang phần Đọc ➡️", type="primary")
    
    return user_answers if submitted else None


def render_reading_section(data: Dict[str, Any]) -> Optional[Dict[int, str]]:
    """Render reading section with passage and questions.
    
    Args:
        data: Reading section data
        
    Returns:
        Dictionary of user answers if submitted, None otherwise
    """
    st.subheader("Phần 2: Đọc (Reading)")
    st.progress(0.50, text="Tiến độ: 50%")
    
    st.markdown(
        f"""<div style="padding:15px; background:#f0f2f6; border-radius:10px; margin-bottom: 20px;">
        {data['passage']}</div>""", 
        unsafe_allow_html=True
    )
    
    questions = data.get('questions', [])
    if not questions and 'question' in data:
        questions = [{
            'q': data['question'],
            'options': data.get('options', []),
            'answer': data.get('answer'),
            'explanation': data.get('explanation')
        }]
    
    user_answers = {}
    with st.form("reading_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**Câu {i+1}: {q['q']}**")
            user_answers[i] = st.radio(
                f"Chọn đáp án câu {i+1}:", 
                q['options'], 
                key=f"read_q_{i}", 
                index=None
            )
            st.markdown("---")
            
        submitted = st.form_submit_button("Tiếp tục sang phần Viết ➡️", type="primary")
    
    return user_answers if submitted else None


def render_writing_section(prompt: str) -> Optional[str]:
    """Render writing section.
    
    Args:
        prompt: Writing prompt/topic
        
    Returns:
        User's written text if submitted, None otherwise
    """
    st.subheader("Phần 3: Viết (Writing)")
    st.progress(0.75, text="Tiến độ: 75%")
    
    st.info(f"📝 **Topic:** {prompt}")
    
    user_text = st.text_area("Nhập bài viết của bạn:", height=200)
    
    if st.button("Tiếp tục sang phần Nói ➡️"):
        if len(user_text.split()) < 5:
            st.warning("Bài viết quá ngắn. Vui lòng viết ít nhất 5 từ.")
            return None
        return user_text
    
    return None


def render_speaking_section(prompt: str) -> Optional[str]:
    """Render speaking section with audio input.
    
    Args:
        prompt: Speaking prompt/topic
        
    Returns:
        Transcript of user's speech if submitted, None otherwise
    """
    from core.stt import recognize_audio
    import logging
    
    logger = logging.getLogger(__name__)
    
    st.subheader("Phần 4: Nói (Speaking)")
    st.progress(0.90, text="Tiến độ: 90%")
    
    st.info(f"🗣️ **Topic:** {prompt}")
    st.write("Hãy ghi âm câu trả lời của bạn:")
    
    audio_val = st.audio_input("Ghi âm bài nói", key="exam_speaking_rec")
    
    user_transcript = None
    if audio_val:
        with st.spinner("Đang xử lý âm thanh..."):
            ok, text = recognize_audio(audio_val.read())
            if ok:
                user_transcript = text
                st.success("Đã ghi nhận câu trả lời!")
                st.markdown(f"**Transcript:** *{text}*")
            else:
                st.error(f"Lỗi nhận dạng: {text}")
    
    if st.button("Nộp bài và Xem kết quả 🏁", type="primary"):
        if user_transcript:
            return user_transcript
        st.warning("Vui lòng ghi âm câu trả lời trước khi nộp bài.")
    
    return None


def render_result_section(
    data: Dict[str, Any],
    answers: Dict[str, Any],
    level: str,
    user_id: int
) -> None:
    """Render complete exam results with grading.
    
    Args:
        data: All exam data
        answers: User's answers
        level: Exam level
        user_id: Current user ID
    """
    from core.llm import generate_response_with_fallback, parse_json_response
    from services.game_service import save_mock_test_result
    import logging
    
    logger = logging.getLogger(__name__)
    
    st.subheader("🎉 Kết quả bài thi thử")
    st.progress(1.0, text="Hoàn thành!")
    
    # Grade Listening & Reading
    lis_score, total_lis = grade_mc_section(data['listening'], answers.get('listening', {}))
    read_score, total_read = grade_mc_section(data['reading'], answers.get('reading', {}))
    
    # Display MC results
    render_mc_results("Listening", data['listening'], answers.get('listening', {}), lis_score, total_lis)
    render_mc_results("Reading", data['reading'], answers.get('reading', {}), read_score, total_read)
    
    # Calculate final MC score
    score_l = (lis_score / total_lis) * 5 if total_lis > 0 else 0
    score_r = (read_score / total_read) * 5 if total_read > 0 else 0
    final_score = round(score_l + score_r, 1)
    
    # Save to DB
    try:
        save_mock_test_result(user_id, level, final_score)
    except Exception as e:
        logger.error(f"Save mock test result error: {e}")
        st.warning("Không thể lưu kết quả thi. Vui lòng thử lại sau.")
    
    st.success(f"**Điểm trắc nghiệm của bạn: {final_score}/10**")
    st.divider()
    
    # Grade Writing (AI)
    render_writing_feedback(data['writing_prompt'], answers.get('writing', ''), level)
    st.divider()
    
    # Grade Speaking (AI)
    render_speaking_feedback(data['speaking_prompt'], answers.get('speaking', ''), level)


def grade_mc_section(data: Dict[str, Any], user_answers: Dict) -> tuple[int, int]:
    """Grade multiple choice section.
    
    Args:
        data: Section data with questions
        user_answers: User's answers
        
    Returns:
        Tuple of (score, total_questions)
    """
    questions = data.get('questions', [])
    if not questions and 'question' in data:
        questions = [{
            'q': data.get('question'),
            'options': data.get('options', []),
            'answer': data.get('answer'),
            'explanation': data.get('explanation')
        }]
    
    # Handle old format where answers might be string instead of dict
    if isinstance(user_answers, str):
        user_answers = {0: user_answers}
    
    score = 0
    for i, q in enumerate(questions):
        if user_answers.get(i) == q['answer']:
            score += 1
    
    return score, len(questions)


def render_mc_results(
    section_name: str,
    data: Dict[str, Any],
    user_answers: Dict,
    score: int,
    total: int
) -> None:
    """Render multiple choice results with detailed feedback.
    
    Args:
        section_name: Name of the section
        data: Section data
        user_answers: User's answers
        score: User's score
        total: Total questions
    """
    questions = data.get('questions', [])
    if not questions and 'question' in data:
        questions = [{
            'q': data.get('question'),
            'options': data.get('options', []),
            'answer': data.get('answer'),
            'explanation': data.get('explanation')
        }]
    
    # Handle old format
    if isinstance(user_answers, str):
        user_answers = {0: user_answers}
    
    with st.expander(f"{score}/{total} - {section_name} (Đáp án chi tiết)", expanded=True):
        if section_name == "Listening":
            st.markdown(f"**Transcript:** *{data['script']}*")
            st.divider()
        
        for i, q in enumerate(questions):
            u_a = user_answers.get(i)
            is_correct = (u_a == q['answer'])
            
            icon = "✅" if is_correct else "❌"
            st.markdown(f"**Câu {i+1}:** {icon} Bạn chọn: {u_a} | Đáp án: {q['answer']}")
            if not is_correct:
                st.caption(f"💡 Giải thích: {q.get('explanation', 'N/A')}")
            st.markdown("---")


def render_writing_feedback(prompt: str, content: str, level: str) -> None:
    """Render AI feedback for writing section.
    
    Args:
        prompt: Writing prompt
        content: User's writing
        level: Exam level
    """
    from core.llm import generate_response_with_fallback, parse_json_response
    
    st.markdown("**3. Writing Feedback (AI):**")
    with st.spinner("AI đang chấm bài viết..."):
        w_prompt = f"""
        Act as an IELTS examiner. Grade this writing (Level {level}) on topic '{prompt}'.
        Content: '''{content}'''
        Return JSON: {{
            "score": "X/10",
            "comment": "General feedback in Vietnamese",
            "corrected": "Corrected version",
            "detailed_analysis": "Detailed analysis of vocabulary, grammar, coherence in Vietnamese"
        }}
        """
        w_res = generate_response_with_fallback(w_prompt)
        w_json = parse_json_response(w_res)
        
        if w_json:
            st.info(f"Điểm: {w_json.get('score')} - {w_json.get('comment')}")
            with st.expander("Xem bài sửa"):
                st.write(w_json.get('corrected'))
            with st.expander("Phân tích chi tiết (Writing)"):
                st.write(w_json.get('detailed_analysis'))
        else:
            st.write(w_res)


def render_speaking_feedback(prompt: str, transcript: str, level: str) -> None:
    """Render AI feedback for speaking section.
    
    Args:
        prompt: Speaking prompt
        transcript: Transcript of user's speech
        level: Exam level
    """
    from core.llm import generate_response_with_fallback, parse_json_response
    
    st.markdown("**4. Speaking Feedback (AI):**")
    with st.spinner("AI đang chấm bài nói..."):
        s_prompt = f"""
        Act as an IELTS examiner. Grade this speaking transcript (Level {level}) on topic '{prompt}'.
        Transcript: '''{transcript}'''
        Return JSON: {{
            "score": "X/10",
            "comment": "General feedback in Vietnamese",
            "pronunciation_note": "Pronunciation feedback in Vietnamese",
            "detailed_analysis": "Detailed analysis of fluency, vocabulary, grammar in Vietnamese"
        }}
        """
        s_res = generate_response_with_fallback(s_prompt)
        s_json = parse_json_response(s_res)
        
        if s_json:
            st.info(f"Điểm: {s_json.get('score')} - {s_json.get('comment')}")
            st.caption(f"Lưu ý phát âm: {s_json.get('pronunciation_note')}")
            with st.expander("Phân tích chi tiết (Speaking)"):
                st.write(s_json.get('detailed_analysis'))
        else:
            st.write(s_res)


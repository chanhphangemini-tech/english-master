import streamlit as st
import time
from core.theme_applier import apply_page_theme

apply_page_theme()  # Apply theme + sidebar + auth (includes render_sidebar)
from core.llm import generate_response_with_fallback, parse_json_response
from core.tts import get_tts_audio
from core.premium import can_use_ai_feature, log_ai_usage, show_premium_upsell
from core.debug_tools import render_debug_panel
from core.data import supabase
from services.skill_tracking_service import track_skill_progress
from services.exercise_cache_service import get_unseen_exercise, save_exercise, mark_exercise_seen, mark_exercise_completed
from services.topic_service import get_vietnamese_topic_options, get_english_topic_from_vietnamese

st.title("📖 Phòng Luyện Đọc (Reading)")

# Get user_id for tracking
user_info = st.session_state.get("user_info", {})
user_id = user_info.get("id")

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

PAGE_ID = "reading_page"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.reading_data = None
    st.session_state.reading_audio = None
    st.session_state.reading_exercise_id = None
    st.session_state.reading_quiz_answers = {}
st.session_state.active_page = PAGE_ID

# --- TABS ---
tab_gen, tab_saved = st.tabs(["✨ Tạo bài mới", "📂 Bài đã lưu"])

# --- TAB 1: GENERATE ---
with tab_gen:
    # 1. Cấu hình
    c1, c2, c3 = st.columns([1, 1, 1])
    level = c1.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=1)
    # Hiển thị chủ đề bằng tiếng Việt
    vietnamese_topics = get_vietnamese_topic_options()
    selected_vietnamese_topic = c2.selectbox("Chủ đề:", vietnamese_topics, index=0, key="read_topic")
    topic = get_english_topic_from_vietnamese(selected_vietnamese_topic)  # Convert về English để lưu DB

    if can_use_ai_feature("reading"):
        if c3.button("Tạo bài đọc mới", type="primary", width='stretch'):
            # Try to get cached exercise first
            cached_exercise = None
            exercise_id = None
            
            if user_id:
                with st.spinner("Đang tìm bài đọc từ kho lưu trữ..."):
                    cached_exercise = get_unseen_exercise(user_id, "reading_question", level, topic)
                    if cached_exercise:
                        exercise_id = cached_exercise.get('id')
                        data = cached_exercise.get('exercise_data', {})
                        # Mark as seen
                        mark_exercise_seen(user_id, exercise_id)
            
            # If no cache, generate new exercise
            if not cached_exercise:
                with st.spinner(f"AI đang viết bài đọc về {topic} ({level})..."):
                    prompt = f"""
                    Act as an English teacher. Create a comprehensive reading lesson about '{topic}' (CEFR Level {level}).
                    Length: 200-250 words.
                    
                    Return strictly JSON format:
                    {{
                        "title": "Title in English",
                        "english_content": "Full English text...",
                        "vietnamese_content": "Full Vietnamese translation...",
                        "summary": "A brief summary of the text (1-2 sentences) in English.",
                        "vocabulary": [
                            {{"word": "word1", "type": "noun/verb...", "meaning": "Vietnamese meaning", "context": "Example sentence from text"}}
                        ],
                        "grammar": [
                            {{"structure": "Name of structure", "explanation": "Brief explanation in Vietnamese", "example": "Example from text"}}
                        ],
                        "quiz": [
                            {{"question": "Question 1?", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Why?"}},
                            {{"question": "Question 2?", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Why?"}},
                            {{"question": "Question 3?", "options": ["A", "B", "C", "D"], "answer": "Correct Option", "explanation": "Why?"}}
                        ]
                    }}
                    """
                    
                    res = generate_response_with_fallback(prompt, ["ERROR"])
                    data = parse_json_response(res)
                    
                    if data and "english_content" in data:
                        log_ai_usage("reading")
                        # Save to cache
                        if user_id:
                            exercise_id = save_exercise(
                                exercise_type="reading_question",
                                level=level,
                                topic=topic,
                                exercise_data=data,
                                user_id=user_id
                            )
                            if exercise_id:
                                mark_exercise_seen(user_id, exercise_id)
            
            # Set session state with exercise data
            if data and "english_content" in data:
                st.session_state.reading_data = data
                st.session_state.reading_exercise_id = exercise_id  # Store exercise_id for completion tracking
                st.session_state.reading_quiz_answers = {}  # Track correct answers for this reading
                st.session_state.reading_audio = None
                st.rerun()
            else:
                st.error("Lỗi khi tạo nội dung. Vui lòng thử lại.")
    else:
        with c3:
            show_premium_upsell("Tạo bài đọc", "reading")

    # --- DEBUG --- (Disabled)
    # render_debug_panel("Reading AI Gen", {
    #     "level": level,
    #     "topic": topic,
    #     "data": st.session_state.reading_data
    # })

    st.divider()

    # 2. Hiển thị nội dung
    if st.session_state.reading_data:
        data = st.session_state.reading_data
        
        c_title, c_save = st.columns([4, 1])
        c_title.markdown(f"### {data.get('title', 'Untitled')}")
        
        # Save Button
        if c_save.button("💾 Lưu bài", width='stretch'):
            try:
                supabase.table("SavedReadings").insert({
                    "user_id": st.session_state.user_info['id'],
                    "title": data.get('title', 'Untitled'),
                    "content": data
                }).execute()
                st.toast("Đã lưu vào kho bài đọc!", icon="✅")
            except Exception as e:
                st.error(f"Lỗi lưu bài: {e}")

        # Audio Player
        if st.button("🔊 Nghe bài đọc (TTS)", help="Nghe giọng đọc AI để luyện kỹ năng nghe và shadowing."):
            with st.spinner("Đang tạo âm thanh..."):
                st.session_state.reading_audio = get_tts_audio(data['english_content'])
        
        if st.session_state.get('reading_audio'):
            st.audio(st.session_state.reading_audio, format='audio/mp3')

        # Chế độ hiển thị
        view_mode = st.radio("Chế độ xem:", ["🇬🇧 Chỉ Tiếng Anh", "🇻🇳 Song ngữ", "🔍 Phân tích (Từ vựng & Ngữ pháp)"], horizontal=True, label_visibility="collapsed")
        
        with st.container(border=True):
            if view_mode == "🇬🇧 Chỉ Tiếng Anh":
                st.markdown(f"""
                <div style="font-size: 1.1em; line-height: 1.6;">
                    {data['english_content']}
                </div>
                """, unsafe_allow_html=True)
                
                if data.get('summary'):
                    st.info(f"**Summary:** {data['summary']}")

                with st.expander("Xem dịch nghĩa"):
                    st.write(data['vietnamese_content'])

            elif view_mode == "🇻🇳 Song ngữ":
                c_en, c_vn = st.columns(2)
                with c_en:
                    st.markdown("#### English")
                    st.info(data['english_content'])
                with c_vn:
                    st.markdown("#### Tiếng Việt")
                    st.success(data['vietnamese_content'])

            elif view_mode == "� Phân tích (Từ vựng & Ngữ pháp)":
                st.markdown(f"**Nội dung:** {data['english_content']}")
                st.divider()
                
                c_vocab, c_gram = st.columns(2)
                
                with c_vocab:
                    st.markdown("#### 🔑 Từ vựng (Vocabulary)")
                vocab_list = data.get('vocabulary', [])
                if vocab_list:
                    for v in vocab_list:
                        with st.container(border=True):
                            st.markdown(f"**{v.get('word')}** ({v.get('type')})")
                            st.caption(v.get('meaning'))
                            st.markdown(f"*{v.get('context')}*")
                else:
                    st.info("Không có từ vựng nào được trích xuất.")
                
                with c_gram:
                    st.markdown("#### 📘 Ngữ pháp (Grammar)")
                    gram_list = data.get('grammar', [])
                    if gram_list:
                        for g in gram_list:
                            with st.container(border=True):
                                st.markdown(f"**{g.get('structure')}**")
                                st.write(g.get('explanation'))
                                st.info(f"Ex: {g.get('example')}")
                    else:
                        st.info("Không có cấu trúc ngữ pháp đặc biệt.")

        # Comprehension Check
        st.divider()
        st.subheader("🧠 Kiểm tra đọc hiểu (Quiz)")
        
        quiz_list = data.get('quiz', [])
        if not quiz_list and data.get('comprehension_question'): # Fallback for old format
            quiz_list = [data.get('comprehension_question')]

        if quiz_list:
            # Initialize tracking if not exists
            if 'reading_quiz_answers' not in st.session_state:
                st.session_state.reading_quiz_answers = {}
            
            total_questions = len(quiz_list)
            correct_count = 0
            
            for i, q in enumerate(quiz_list):
                with st.expander(f"Câu hỏi {i+1}: {q['question']}", expanded=True):
                    user_ans = st.radio("Chọn đáp án:", q['options'], key=f"read_quiz_{i}", index=None)
                    if user_ans:
                        is_correct = user_ans == q['answer']
                        # Track answer for this question
                        st.session_state.reading_quiz_answers[i] = is_correct
                        
                        if is_correct:
                            st.success("✅ Chính xác!")
                            # Track skill progress
                            if user_id:
                                track_skill_progress(user_id, 'reading', 1, 1)  # 1 exercise, 1 correct
                            correct_count += 1
                        else:
                            st.error(f"❌ Sai rồi.")
                            # Track skill progress (0 correct)
                            if user_id:
                                track_skill_progress(user_id, 'reading', 1, 0)
                        
                        if 'explanation' in q:
                            st.caption(f"💡 Giải thích: {q['explanation']}")
                    else:
                        # Check if previously answered correctly
                        if i in st.session_state.reading_quiz_answers:
                            if st.session_state.reading_quiz_answers[i]:
                                correct_count += 1
            
            # Mark exercise as completed when all questions are answered
            # Calculate score based on correct answers
            if len(st.session_state.reading_quiz_answers) == total_questions and user_id:
                score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0
                exercise_id = st.session_state.get('reading_exercise_id')
                if exercise_id:
                    mark_exercise_completed(user_id, exercise_id, score=score)
        
    else:
        st.info("👈 Hãy chọn chủ đề và bấm 'Tạo bài đọc mới' để bắt đầu.")

# --- TAB 2: SAVED READINGS ---
with tab_saved:
    st.subheader("📂 Kho bài đọc đã lưu")
    
    try:
        res = supabase.table("SavedReadings").select("*").eq("user_id", st.session_state.user_info['id']).order("created_at", desc=True).execute()
        saved_items = res.data if res.data else []
        
        if not saved_items:
            st.info("Bạn chưa lưu bài đọc nào.")
        else:
            for item in saved_items:
                with st.expander(f"📅 {item['created_at'][:10]} | {item['title']}"):
                    if st.button("📖 Đọc lại", key=f"load_{item['id']}"):
                        st.session_state.reading_data = item['content']
                        st.session_state.reading_audio = None
                        st.rerun()
                    
                    if st.button("🗑️ Xóa", key=f"del_{item['id']}"):
                        supabase.table("SavedReadings").delete().eq("id", item['id']).execute()
                        st.rerun()
    except Exception as e:
        st.error(f"Lỗi tải bài đã lưu: {e}")
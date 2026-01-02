import streamlit as st
import time
import string
from core.theme_applier import apply_page_theme
from core.tts import get_tts_audio, get_tts_audio_no_cache
from core.llm import generate_response_with_fallback, parse_json_response
from core.premium import can_use_ai_feature, log_ai_usage, show_premium_upsell
from core.debug_tools import render_debug_panel
from services.skill_tracking_service import track_skill_progress
from services.exercise_cache_service import get_unseen_exercise, save_exercise, mark_exercise_seen, mark_exercise_completed
from services.topic_service import get_vietnamese_topic_options, get_english_topic_from_vietnamese

if not st.session_state.get("logged_in"): st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth
st.title("🎧 Phòng Luyện Nghe (Listening)")

# Get user_id for tracking
user_info = st.session_state.get("user_info", {})
user_id = user_info.get("id")

PAGE_ID = "listening_page"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.listening_tab = "✍️ Chép chính tả"
    st.session_state.dictation_data = None
    st.session_state.dictation_audio = None
    st.session_state.comp_data = None
    st.session_state.comp_audio = None
    st.session_state.podcast_script = None
    st.session_state.podcast_audio = None
st.session_state.active_page = PAGE_ID

# --- NAVIGATION ---
options = ["✍️ Chép chính tả", "🧠 Nghe hiểu", "📻 Podcast"]
selected = st.radio("Menu", options, horizontal=True, label_visibility="collapsed", key="listening_tab")
st.divider()

# --- TAB 1: DICTATION ---
if selected == "✍️ Chép chính tả":
    st.subheader("Nghe và chép lại (Dictation)")
    st.caption("AI sẽ tạo câu ngẫu nhiên theo trình độ và chủ đề bạn chọn.")

    # 1. Cấu hình bài tập
    c1, c2, c3 = st.columns([1, 1, 1])
    level = c1.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=1)
    # Hiển thị chủ đề bằng tiếng Việt
    vietnamese_topics = get_vietnamese_topic_options()
    selected_vietnamese_topic = c2.selectbox("Chủ đề:", vietnamese_topics, index=0 if "Cuộc sống hàng ngày" in vietnamese_topics else 0)
    topic = get_english_topic_from_vietnamese(selected_vietnamese_topic)  # Convert về English để lưu DB
    
    # 2. Nút tạo câu mới
    if can_use_ai_feature("listening"):
        if c3.button("🎲 Tạo câu mới", type="primary", width='stretch'):
            # Try to get cached exercise first
            cached_exercise = None
            exercise_id = None
            
            if user_id:
                with st.spinner("Đang tìm bài tập từ kho lưu trữ..."):
                    cached_exercise = get_unseen_exercise(user_id, "dictation", level, topic)
                    if cached_exercise:
                        exercise_id = cached_exercise.get('id')
                        data = cached_exercise.get('exercise_data', {})
                        # Mark as seen
                        mark_exercise_seen(user_id, exercise_id)
            
            # If no cache, generate new exercise
            if not cached_exercise:
                with st.spinner(f"AI đang nghĩ câu tiếng Anh ({level})..."):
                    prompt = f"""
                    Generate 1 English sentence for dictation practice.
                    Level: {level} (CEFR).
                    Topic: {topic}.
                    Length: Moderate (10-20 words).
                    Return strictly JSON format: {{"text": "English sentence", "translation": "Vietnamese meaning"}}
                    """
                    
                    res = generate_response_with_fallback(prompt, ["ERROR"])
                    data = parse_json_response(res)
                    
                    if data and "text" in data:
                        log_ai_usage("listening") # Log usage on success
                        # Save to cache
                        if user_id:
                            exercise_id = save_exercise(
                                exercise_type="dictation",
                                level=level,
                                topic=topic,
                                exercise_data=data,
                                user_id=user_id
                            )
                            if exercise_id:
                                mark_exercise_seen(user_id, exercise_id)
            
            # Set session state with exercise data
            if data and "text" in data:
                st.session_state.dictation_data = data
                st.session_state.dictation_exercise_id = exercise_id  # Store exercise_id for completion tracking
                st.session_state.dictation_audio = None # Reset audio cũ
                if 'user_dictation_input' in st.session_state:
                    del st.session_state['user_dictation_input']
                st.rerun()
            else:
                st.error("Lỗi khi tạo câu. Vui lòng thử lại.")
    else:
        with c3:
            show_premium_upsell("Tạo câu mới", "listening")

    # --- DEBUG --- (Disabled)
    # render_debug_panel("Dictation AI Gen", {
    #     "level": level,
    #     "topic": topic,
    #     "last_prompt": st.session_state.get('last_gemini_prompt')
    # })

    st.divider()

    # 3. Khu vực làm bài
    if st.session_state.dictation_data:
        data = st.session_state.dictation_data
        target_text = data['text']
        
        # --- Audio Player ---
        st.markdown("#### 1. Nghe âm thanh")
        
        # Chỉ tạo audio 1 lần và cache lại
        if st.session_state.dictation_audio is None:
            with st.spinner("Đang tạo âm thanh..."):
                st.session_state.dictation_audio = get_tts_audio(target_text)
        
        if st.session_state.dictation_audio:
            st.audio(st.session_state.dictation_audio, format='audio/mp3')
            st.caption("💡 Mẹo: Bấm nút 3 chấm trên trình phát để chỉnh tốc độ nghe.")

        # --- User Input ---
        st.markdown("#### 2. Chép lại")
        user_text = st.text_area("Nhập những gì bạn nghe được:", height=100, key="user_dictation_input")
        
        # --- Check Result ---
        if st.button("Kiểm tra kết quả"):
            # Chuẩn hóa chuỗi để so sánh (bỏ dấu câu, chữ thường)
            translator = str.maketrans('', '', string.punctuation)
            clean_user = " ".join(user_text.strip().lower().translate(translator).split())
            clean_target = " ".join(target_text.strip().lower().translate(translator).split())

            if clean_user == clean_target:
                st.balloons()
                st.success("🎉 Chính xác hoàn toàn!")
                st.info(f"Dịch nghĩa: {data.get('translation', '')}")
                # Track skill progress
                if user_id:
                    track_skill_progress(user_id, 'listening', 1, 1)  # 1 exercise, 1 correct
                    # Mark exercise as completed in cache
                    exercise_id = st.session_state.get('dictation_exercise_id')
                    if exercise_id:
                        mark_exercise_completed(user_id, exercise_id, score=100)
            else:
                st.warning("Chưa chính xác lắm. Hãy thử lại hoặc xem đáp án.")
                # Track skill progress (0 correct)
                if user_id:
                    track_skill_progress(user_id, 'listening', 1, 0)
                
            with st.expander("Xem đáp án & Dịch nghĩa", expanded=True):
                st.markdown(f"**Gốc:** `{target_text}`")
                st.markdown(f"**Dịch:** {data.get('translation', '')}")
                if user_text:
                    st.text(f"Bạn viết: {user_text}")
    
    else:
        st.info("👈 Hãy chọn trình độ và bấm 'Tạo câu mới' để bắt đầu luyện tập.")

# --- TAB 2: COMPREHENSION ---
elif selected == "🧠 Nghe hiểu":
    st.subheader("Bài tập trắc nghiệm (Listening Comprehension)")
    st.caption("Nghe đoạn văn ngắn và trả lời câu hỏi.")

    # 1. Cấu hình
    c1, c2, c3 = st.columns([1, 1, 1])
    level = c1.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1", "C2"], key="comp_lvl")
    # Hiển thị chủ đề bằng tiếng Việt
    vietnamese_topics = get_vietnamese_topic_options()
    selected_vietnamese_topic = c2.selectbox("Chủ đề:", vietnamese_topics, index=0, key="comp_topic")
    topic = get_english_topic_from_vietnamese(selected_vietnamese_topic)  # Convert về English để lưu DB
    
    if can_use_ai_feature("listening"):
        if c3.button("🎲 Tạo bài tập", type="primary", width='stretch'):
            # Try to get cached exercise first
            cached_exercise = None
            exercise_id = None
            
            if user_id:
                with st.spinner("Đang tìm bài tập từ kho lưu trữ..."):
                    cached_exercise = get_unseen_exercise(user_id, "comprehension", level, topic)
                    if cached_exercise:
                        exercise_id = cached_exercise.get('id')
                        data = cached_exercise.get('exercise_data', {})
                        # Mark as seen
                        mark_exercise_seen(user_id, exercise_id)
            
            # If no cache, generate new exercise
            if not cached_exercise:
                with st.spinner("AI đang soạn bài nghe..."):
                    prompt = f"""
                    Create a short English listening passage (50-80 words) for Level {level} about {topic}.
                    Then create 1 multiple-choice question based on it.
                    Return strictly JSON format: {{
                        "text": "passage text",
                        "question": "question text",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "answer": "Correct Option Text",
                        "explanation": "Explanation in Vietnamese"
                    }}
                    """
                    res = generate_response_with_fallback(prompt, ["ERROR"])
                    data = parse_json_response(res)
                    
                    if data and "text" in data:
                        log_ai_usage("listening")
                        # Save to cache
                        if user_id:
                            exercise_id = save_exercise(
                                exercise_type="comprehension",
                                level=level,
                                topic=topic,
                                exercise_data=data,
                                user_id=user_id
                            )
                            if exercise_id:
                                mark_exercise_seen(user_id, exercise_id)
            
            # Set session state with exercise data
            if data and "text" in data:
                st.session_state.comp_data = data
                st.session_state.comp_exercise_id = exercise_id  # Store exercise_id for completion tracking
                st.session_state.comp_audio = None # Reset audio
                st.rerun()
            else:
                st.error("Lỗi tạo bài tập. Vui lòng thử lại.")
    else:
        with c3:
            show_premium_upsell("Tạo bài tập", "listening")

    # --- DEBUG --- (Disabled)
    # render_debug_panel("Listening Comp AI Gen", {
    #     "level": level,
    #     "topic": topic,
    #     "data": st.session_state.comp_data
    # })

    st.divider()

    # 2. Hiển thị bài tập
    if st.session_state.comp_data:
        data = st.session_state.comp_data
        
        # Audio (sử dụng giọng Jenny - tự nhiên hơn cho comprehension)
        st.markdown("#### 1. Nghe đoạn văn")
        if st.session_state.comp_audio is None:
            with st.spinner("Đang tạo âm thanh..."):
                # Sử dụng en-US-JennyNeural - giọng nữ Mỹ tự nhiên hơn cho comprehension
                st.session_state.comp_audio = get_tts_audio(data['text'], voice="en-US-JennyNeural")
        
        if st.session_state.comp_audio:
            st.audio(st.session_state.comp_audio, format='audio/mp3')

        # Question
        st.markdown("#### 2. Trả lời câu hỏi")
        st.markdown(f"**{data['question']}**")
        
        user_ans = st.radio("Chọn đáp án:", data['options'], key="comp_radio")
        
        if st.button("Kiểm tra đáp án"):
            if user_ans == data['answer']:
                st.balloons()
                st.success("🎉 Chính xác!")
                # Track skill progress
                if user_id:
                    track_skill_progress(user_id, 'listening', 1, 1)  # 1 exercise, 1 correct
                    # Mark exercise as completed in cache
                    exercise_id = st.session_state.get('comp_exercise_id')
                    if exercise_id:
                        mark_exercise_completed(user_id, exercise_id, score=100)
            else:
                st.error(f"Sai rồi. Đáp án đúng: {data['answer']}")
                # Track skill progress (0 correct)
                if user_id:
                    track_skill_progress(user_id, 'listening', 1, 0)
            st.info(f"💡 Giải thích: {data['explanation']}")
            
            with st.expander("📖 Xem Transcript (Lời thoại)"):
                st.write(data['text'])
    else:
        st.info("👈 Chọn chủ đề và bấm 'Tạo bài tập' để bắt đầu.")

# --- TAB 3: PODCAST ---
elif selected == "📻 Podcast":
    st.subheader("🎙️ Podcast AI - Chủ Đề Sâu")
    st.caption("Tạo podcast dài (3-5 phút) về chủ đề bạn chọn với nội dung chi tiết và sâu sắc.")
    
    # Cấu hình podcast
    col1, col2, col3 = st.columns([2, 1, 1])
    # Hiển thị chủ đề bằng tiếng Việt (giống Dictation và Comprehension)
    vietnamese_topics = get_vietnamese_topic_options()
    selected_vietnamese_topic = col1.selectbox("Chủ đề:", vietnamese_topics, index=0 if "Cuộc sống hàng ngày" in vietnamese_topics else 0, key="podcast_topic_select")
    pod_topic_english = get_english_topic_from_vietnamese(selected_vietnamese_topic)  # Convert về English để lưu DB
    # Use English topic name for the prompt (will be translated by AI)
    pod_topic = pod_topic_english if pod_topic_english else selected_vietnamese_topic
    pod_level = col2.selectbox("Trình độ:", ["A2", "B1", "B2", "C1", "C2"], index=2, key="podcast_level")
    pod_duration = col3.selectbox("Độ dài:", ["Ngắn (2-3 phút)", "Trung bình (3-5 phút)", "Dài (5-7 phút)"], index=1, key="podcast_duration")
    
    # Map duration to word count
    duration_map = {
        "Ngắn (2-3 phút)": "300-400 words",
        "Trung bình (3-5 phút)": "500-700 words",
        "Dài (5-7 phút)": "800-1000 words"
    }
    target_words = duration_map[pod_duration]
    
    if can_use_ai_feature("listening"):
        if st.button("🎙️ Tạo Podcast", type="primary", width='stretch'):
            # Try to get cached podcast script first
            cached_exercise = None
            exercise_id = None
            script_data = None
            script_from_cache = False
            
            if user_id:
                # Use topic for caching (same as Dictation and Comprehension)
                with st.spinner("Đang tìm podcast từ kho lưu trữ..."):
                    cached_exercise = get_unseen_exercise(user_id, "podcast_script", pod_level, pod_topic_english)
                    if cached_exercise:
                        exercise_id = cached_exercise.get('id')
                        script_data = cached_exercise.get('exercise_data', {})
                        # Ensure script_data is a list
                        if isinstance(script_data, list):
                            mark_exercise_seen(user_id, exercise_id)
                            script_from_cache = True  # Mark that we're using cached script
                        else:
                            script_data = None  # Invalid format, generate new
            
            # If no cache, generate new script
            if not script_data:
                with st.spinner(f"AI đang viết kịch bản podcast dài ({target_words}) và thu âm... (có thể mất 30-60 giây)"):
                    prompt = f"""
                    Create a professional, engaging podcast episode about: {pod_topic}.
                    
                    Requirements:
                    - Length: {target_words} (approximately {pod_duration})
                    - Level: {pod_level} (CEFR) - use appropriate vocabulary and sentence complexity
                    - Format: Structured podcast with clear segments
                    - Characters: Host (Alice - Female, professional and engaging) and Guest (Bob - Male, knowledgeable expert)
                    
                    Structure:
                    1. Introduction (Host welcomes listeners, introduces topic and guest)
                    2. Main Discussion (3-4 key points about the topic, with Host asking questions and Guest providing insights)
                    3. Examples/Case Studies (real-world applications or interesting facts)
                    4. Conclusion (Host summarizes key takeaways, thanks guest, closing remarks)
                    
                    Content Guidelines:
                    - Make it informative, engaging, and educational
                    - Include natural conversation flow with questions and answers
                    - Add interesting facts, examples, or anecdotes
                    - Use appropriate transitions between segments
                    - End with a memorable closing statement
                    
                    Format: JSON list of objects, each representing a speaking turn with BOTH English and Vietnamese:
                    [
                        {{"speaker": "Host", "text": "Welcome message and introduction in English...", "translation": "Bản dịch tiếng Việt tương ứng ở đây"}},
                        {{"speaker": "Guest", "text": "Response and insights in English...", "translation": "Bản dịch tiếng Việt tương ứng ở đây"}},
                        ...
                    ]
                    
                    CRITICAL REQUIREMENTS:
                    - Each object MUST include both "text" (English) and "translation" (Vietnamese) fields
                    - Vietnamese translation should be natural, accurate, and help Vietnamese learners understand
                    - Do not skip the translation field - it is required for all speaking turns
                    
                    Ensure the total dialogue is approximately {target_words} and covers the topic comprehensively.
                    """
                    
                    res = generate_response_with_fallback(prompt, ["ERROR"])
                    script_data = parse_json_response(res)
                    
                    # Save to cache if generation was successful
                    if script_data and isinstance(script_data, list) and user_id:
                        # Store topic for caching (same as Dictation and Comprehension)
                        exercise_id = save_exercise(
                            exercise_type="podcast_script",
                            level=pod_level,
                            topic=pod_topic_english,  # Use topic for caching
                            exercise_data=script_data,
                            user_id=user_id,
                            metadata={"duration": pod_duration, "target_words": target_words}
                        )
                        if exercise_id:
                            mark_exercise_seen(user_id, exercise_id)
                
                if script_data and isinstance(script_data, list):
                    # Only log AI usage if we generated new content (not from cache)
                    if not script_from_cache:
                        log_ai_usage("listening")
                    audio_chunks = []  # Store chunks in list instead of concatenating immediately
                    display_script = ""
                    word_count = 0
                    processed_count = 0  # Track successfully processed audio chunks
                    
                    # Progress bar for audio generation
                    progress_bar = st.progress(0)
                    total_turns = len([t for t in script_data if t.get("text", "").strip()])  # Count only non-empty turns
                    
                    for idx, turn in enumerate(script_data):
                        speaker = turn.get("speaker", "Host")
                        text = turn.get("text", "").strip()  # Strip whitespace
                        translation = turn.get("translation", "").strip()  # Get Vietnamese translation if available
                        
                        # Skip empty text to avoid missing audio chunks
                        if not text:
                            continue
                        
                        # Count words
                        word_count += len(text.split())
                        
                        # Display script with English and Vietnamese
                        icon = "👩" if "Host" in speaker or "Alice" in speaker else "👨"
                        speaker_name = "Alice (Host)" if "Host" in speaker or "Alice" in speaker else "Bob (Guest)"
                        if translation:
                            display_script += f"**{icon} {speaker_name}:**\n"
                            display_script += f"*{text}*\n"
                            display_script += f"🇻🇳 {translation}\n\n"
                        else:
                            display_script += f"**{icon} {speaker_name}:** {text}\n\n"
                        
                        # Select natural-sounding voices for podcast
                        # Using newer, more natural voices for better podcast quality
                        # Fallback to AriaNeural/GuyNeural if these don't work
                        if "Host" in speaker or "Alice" in speaker:
                            # Female voices (confirmed available):
                            # - en-US-JennyNeural: Very natural, warm, conversational (RECOMMENDED)
                            # - en-US-AriaNeural: Reliable fallback
                            voice = "en-US-JennyNeural"  # More natural female voice
                        else:
                            # Male voices (confirmed available):
                            # - en-US-BrianNeural: Clear and professional (RECOMMENDED)
                            # - en-US-ChristopherNeural: Natural, friendly alternative
                            # - en-US-GuyNeural: Reliable fallback
                            voice = "en-US-BrianNeural"  # More natural male voice
                        
                        # Generate audio for this chunk - use no-cache version for podcast to ensure completeness
                        try:
                            # Add small delay to avoid rate limiting
                            if processed_count > 0:
                                time.sleep(0.2)  # 200ms delay between requests
                            
                            chunk = get_tts_audio_no_cache(text, voice)
                            if chunk is not None and len(chunk) > 0:
                                # Store chunk in list instead of concatenating immediately
                                audio_chunks.append(chunk)
                                processed_count += 1
                            else:
                                # If primary voice fails, try fallback voice
                                fallback_voice = "en-US-AriaNeural" if "Host" in speaker or "Alice" in speaker else "en-US-GuyNeural"
                                time.sleep(0.5)
                                chunk_retry = get_tts_audio_no_cache(text, fallback_voice)
                                if chunk_retry is not None and len(chunk_retry) > 0:
                                    audio_chunks.append(chunk_retry)
                                    processed_count += 1
                                    print(f"Used fallback voice ({fallback_voice}) for turn {idx + 1}")
                                else:
                                    # Final retry with original voice and longer delay
                                    time.sleep(1.5)
                                    chunk_final = get_tts_audio_no_cache(text, voice)
                                    if chunk_final is not None and len(chunk_final) > 0:
                                        audio_chunks.append(chunk_final)
                                        processed_count += 1
                                    else:
                                        # Log warning if chunk is None or empty (but continue processing)
                                        print(f"Warning: Empty audio for turn {idx + 1} (tried {voice} and {fallback_voice}): '{text[:50]}...'")
                        except Exception as e:
                            print(f"Error generating audio for turn {idx + 1}: {str(e)[:100]}")
                        
                        # Update progress based on processed count
                        if total_turns > 0:
                            progress_bar.progress(processed_count / total_turns)
                    
                    # Concatenate all audio chunks at the end to ensure proper ordering
                    if audio_chunks:
                        full_audio = b"".join(audio_chunks)
                    else:
                        full_audio = b""
                        st.warning("Không tạo được audio. Vui lòng thử lại.")
                    
                    progress_bar.empty()
                    
                    st.session_state.podcast_script = display_script
                    st.session_state.podcast_audio = full_audio
                    st.session_state.podcast_word_count = word_count
                    st.session_state.podcast_generated_topic = selected_vietnamese_topic  # Store Vietnamese name for display
                    st.rerun()
                else:
                    st.error("Lỗi khi tạo kịch bản podcast. Vui lòng thử lại với chủ đề khác.")
    else:
        show_premium_upsell("Tạo Podcast", "listening")

    st.divider()

    if st.session_state.podcast_audio:
        topic_display = st.session_state.get('podcast_generated_topic', selected_vietnamese_topic)
        word_count = st.session_state.get('podcast_word_count', 0)
        
        st.markdown(f"### 📻 Podcast: {topic_display}")
        
        # Podcast metadata
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("📊 Số từ", f"{word_count:,}")
        with col_info2:
            estimated_minutes = round(word_count / 150)  # Average speaking rate: 150 words/min
            st.metric("⏱️ Thời lượng", f"~{estimated_minutes} phút")
        with col_info3:
            st.metric("🎙️ Người nói", "2 (Host + Guest)")
        
        st.audio(st.session_state.podcast_audio, format='audio/mp3')
        st.caption("💡 Mẹo: Bạn có thể điều chỉnh tốc độ phát trong trình phát audio để luyện nghe tốt hơn.")
        
        with st.expander("📜 Xem toàn bộ kịch bản (Full Script)", expanded=False):
            st.markdown(st.session_state.get('podcast_script', ''))
            
            # Download script option
            script_text = st.session_state.get('podcast_script', '')
            if script_text:
                st.download_button(
                    label="📥 Tải kịch bản (TXT)",
                    data=script_text,
                    file_name=f"podcast_{topic_display.replace(' ', '_')}.txt",
                    mime="text/plain"
                )
        
        # Learning tips
        with st.expander("💡 Mẹo học nghe hiệu quả"):
            st.markdown("""
            **Cách sử dụng podcast này để luyện nghe:**
            1. **Lần 1**: Nghe không xem script, cố gắng hiểu ý chính
            2. **Lần 2**: Nghe lại và xem script để kiểm tra những từ bạn nghe được
            3. **Lần 3**: Nghe lại không xem script, tập trung vào các chi tiết
            4. **Ghi chú**: Viết lại những từ vựng mới và cách diễn đạt hay
            5. **Lặp lại**: Nghe nhiều lần để quen với cách phát âm và ngữ điệu
            """)
    else:
        st.info("👈 Nhập chủ đề bạn muốn nghe, chọn trình độ và độ dài, sau đó bấm 'Tạo Podcast' để bắt đầu.")
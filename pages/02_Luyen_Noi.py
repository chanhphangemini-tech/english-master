import streamlit as st
import random
import time
import base64
import string
import pandas as pd
import logging
from core.theme_applier import apply_page_theme

logger = logging.getLogger(__name__)
from core.data import load_vocab_data
from core.tts import get_tts_audio
from core.llm import generate_response_with_fallback, parse_json_response
from core.stt import recognize_audio
from services.chat_service import get_chat_sessions, get_chat_messages, create_chat_session, add_chat_message
from core.debug_tools import render_debug_panel
from services.skill_tracking_service import track_skill_progress
from services.exercise_cache_service import get_unseen_exercise, save_exercise, mark_exercise_seen
from services.topic_service import get_vietnamese_topic_options, get_english_topic_from_vietnamese

# --- Auth Check ---
if not st.session_state.get("logged_in"):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth
st.title("🗣️ Phòng Luyện Nói (Speaking)")
st.caption("Luyện phát âm từ vựng và câu giao tiếp với phản hồi từ AI.")

# --- HELPER: AUDIO AUTOPLAY ---
def play_audio_autoplay(text):
    try:
        audio_bytes = get_tts_audio(text)
        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode()
            unique_id = int(time.time() * 1000)
            md = f"""<div id="audio_{unique_id}"><audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio></div>"""
            st.markdown(md, unsafe_allow_html=True)
    except: pass

# --- STATEFUL NAVIGATION (Fix lỗi nhảy tab) ---
# Sử dụng Radio button nằm ngang thay cho st.tabs để giữ trạng thái khi Rerun
# CSS giúp Radio trông giống Menu Tabs hơn
st.markdown("""
<style>
/* Custom Radio Button Styling */
div.row-widget.stRadio > div {flex-direction: row; gap: 10px; justify-content: center; margin-bottom: 20px;}
div.row-widget.stRadio > div > label {
    background-color: #ffffff; 
    padding: 8px 20px; 
    border-radius: 20px; 
    cursor: pointer; 
    border: 1px solid #e0e0e0;
    font-weight: 500;
    transition: all 0.3s;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
div.row-widget.stRadio > div > label[data-baseweb="radio"] {
    background-color: #e3f2fd; 
    border-color: #2196f3;
    color: #1565c0;
    font-weight: bold;
    box-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
}

/* Flashcard Styling */
.flashcard {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    padding: 40px 20px;
    border-radius: 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    text-align: center;
    margin-bottom: 25px;
    border: 1px solid #edf2f7;
}
.flashcard-word {
    font-size: 3.5em;
    font-weight: 800;
    background: -webkit-linear-gradient(45deg, #003366, #007BFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}
.flashcard-pron {
    font-size: 1.4em;
    color: #555;
    font-family: 'Courier New', monospace;
    background-color: #f1f3f5;
    padding: 5px 15px;
    border-radius: 20px;
    display: inline-block;
}
.flashcard-sentence {
    font-size: 1.8em;
    color: #2c3e50;
    line-height: 1.6;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

menu_options = ["🔡 Bảng IPA", "🔥 Luyện Từ", "💬 Luyện Câu", "🤖 Luyện Nói AI"]

PAGE_ID = "speaking_page"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.speaking_tab = menu_options[1] # Default to Luyện Từ
    st.session_state.ipa_selected = None
    if 'spk_word' in st.session_state: del st.session_state.spk_word
    st.session_state.active_chat_session = None
st.session_state.active_page = PAGE_ID
selected_tab = st.radio("Menu", menu_options, horizontal=True, label_visibility="collapsed", key="speaking_tab")
st.divider()

# --- TAB 1: BẢNG IPA ---
if selected_tab == "🔡 Bảng IPA":
    st.subheader("Bảng Phiên Âm Quốc Tế (IPA)")
    st.caption("Bấm vào ký hiệu để nghe âm thanh và luyện nói.")

    if 'ipa_selected' not in st.session_state: st.session_state.ipa_selected = None

    # Dữ liệu IPA (Ký hiệu, Từ ví dụ)
    vowels = [
        ("iː", "sheep"), ("ɪ", "ship"), ("ʊ", "good"), ("uː", "shoot"),
        ("e", "bed"), ("ə", "teacher"), ("ɜː", "bird"), ("ɔː", "door"),
        ("æ", "cat"), ("ʌ", "up"), ("ɑː", "far"), ("ɒ", "on")
    ]
    diphthongs = [
        ("ɪə", "here"), ("eɪ", "wait"), ("ʊə", "tour"), ("ɔɪ", "boy"),
        ("əʊ", "show"), ("eə", "hair"), ("aɪ", "my"), ("aʊ", "cow")
    ]
    consonants = [
        ("p", "pea"), ("b", "boat"), ("t", "tea"), ("d", "dog"), ("tʃ", "cheese"), ("dʒ", "june"), ("k", "car"), ("g", "go"),
        ("f", "fly"), ("v", "video"), ("θ", "think"), ("ð", "this"), ("s", "see"), ("z", "zoo"), ("ʃ", "shall"), ("ʒ", "vision"),
        ("m", "man"), ("n", "now"), ("ŋ", "sing"), ("h", "hat"), ("l", "love"), ("r", "red"), ("w", "wet"), ("j", "yes")
    ]

    def render_ipa_grid(items, key_prefix):
        cols = st.columns(8)
        for i, (sym, word) in enumerate(items):
            with cols[i % 8]:
                if st.button(f"{sym}", key=f"{key_prefix}_{i}", help=f"Ví dụ: {word}"):
                    st.session_state.ipa_selected = {"sym": sym, "word": word}
                    play_audio_autoplay(word)

    with st.container(border=True):
        st.markdown("##### 1. Nguyên âm (Vowels)")
        render_ipa_grid(vowels, "vow")
    with st.container(border=True):
        st.markdown("##### 2. Nguyên âm đôi (Diphthongs)")
        render_ipa_grid(diphthongs, "dip")
    with st.container(border=True):
        st.markdown("##### 3. Phụ âm (Consonants)")
        render_ipa_grid(consonants, "con")

    # Khu vực luyện tập khi chọn âm
    if st.session_state.ipa_selected:
        st.divider()
        sel = st.session_state.ipa_selected
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #e3f2fd; border-radius: 10px; border: 1px solid #90caf9;">
            <h1 style="margin:0; color: #1565c0; font-size: 3em;">/{sel['sym']}/</h1>
            <p style="font-size: 1.2em; color: #555;">Ví dụ: <b>{sel['word']}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🔊 Nghe lại"):
                play_audio_autoplay(sel['word'])
        with c2:
            if st.button("❌ Đóng"):
                st.session_state.ipa_selected = None
                st.rerun()

# --- TAB 2: LUYỆN TỪ (Đã phục hồi giao diện cũ) ---
elif selected_tab == "🔥 Luyện Từ":
    st.subheader("Luyện phát âm từ vựng")
    
    # Init Data
    user_level = st.session_state.user_info.get('current_level', 'A1')
    vocab_data = load_vocab_data(user_level)
    df = pd.DataFrame(vocab_data)
    if 'spk_word' not in st.session_state:
        st.session_state.spk_word = df.sample(1).iloc[0].to_dict() if not df.empty else {}

    word = st.session_state.spk_word

    if not word:
        st.warning("Kho từ vựng trống. Vui lòng nạp thêm từ.")
    else:
        # --- GIAO DIỆN FLASHCARD ---
        st.markdown(f"""
        <div class="flashcard">
            <div class="flashcard-word">{word.get('word')}</div>
            <div class="flashcard-pron">/{word.get('pronunciation', '')}/ • {word.get('type', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Controls
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("🔊 Nghe mẫu", key=f"spk_tts_{word.get('id')}"):
                play_audio_autoplay(word.get('word'))
        with c3:
            if st.button("🔄 Từ khác"):
                st.session_state.spk_word = df.sample(1).iloc[0].to_dict()
                st.rerun()
        
        # Sử dụng st.audio_input để ghi âm thực tế
        audio_val = st.audio_input("Ghi âm", key=f"rec_{word.get('id')}")
        
        if audio_val:
            with st.spinner("AI đang phân tích giọng nói..."):
                audio_bytes = audio_val.read()
                ok, text = recognize_audio(audio_bytes)
                
                if ok:
                    st.markdown(f"🗣️ Bạn đã nói: **{text}**")
                    user_id = st.session_state.get("user_info", {}).get("id")
                    # So sánh tương đối (bỏ qua viết hoa/thường và dấu câu)
                    if text.lower().strip().rstrip('.') == word['word'].lower().strip():
                        st.success("🎉 Chính xác! Phát âm rất chuẩn.")
                        st.balloons()
                        # Track skill progress
                        if user_id:
                            track_skill_progress(user_id, 'speaking', 1, 1)  # 1 exercise, 1 correct
                    else:
                        st.warning(f"Chưa chính xác lắm. AI nghe thấy: '{text}'. Hãy thử lại nhé!")
                        # Track skill progress (0 correct)
                        if user_id:
                            track_skill_progress(user_id, 'speaking', 1, 0)
                else:
                    st.error(f"Lỗi nhận dạng: {text}")
        
        # --- DEBUG --- (Disabled)
        # render_debug_panel("Speaking Word", {
        #     "target_word": word.get('word'),
        #     "recognized_text": text if audio_val and ok else "N/A"
        # })

# --- TAB 3: LUYỆN CÂU ---
elif selected_tab == "💬 Luyện Câu":
    st.subheader("Luyện đọc câu giao tiếp")
    
    user_id = st.session_state.get("user_info", {}).get("id")
    user_level = st.session_state.get("user_info", {}).get("current_level", "A1")
    
    # --- AI Generator ---
    with st.expander("✨ Tạo câu theo chủ đề (AI)", expanded=False):
        c_gen_1, c_gen_2, c_gen_3 = st.columns([2, 1, 1])
        # Hiển thị chủ đề bằng tiếng Việt (giống các phần khác)
        vietnamese_topics = get_vietnamese_topic_options()
        selected_vietnamese_topic = c_gen_1.selectbox("Chủ đề:", vietnamese_topics, index=0 if "Du lịch" in vietnamese_topics else 0, key="speaking_sentence_topic")
        topic_english = get_english_topic_from_vietnamese(selected_vietnamese_topic)
        topic_for_prompt = topic_english if topic_english else selected_vietnamese_topic
        level = c_gen_2.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=["A1", "A2", "B1", "B2", "C1", "C2"].index(user_level) if user_level in ["A1", "A2", "B1", "B2", "C1", "C2"] else 0, key="speaking_sentence_level")
        if c_gen_3.button("Tạo mới", type="primary"):
            # Try to get cached sentences first
            cached_exercise = None
            exercise_id = None
            sentences_from_cache = False
            
            if user_id:
                with st.spinner("Đang tìm câu từ kho lưu trữ..."):
                    cached_exercise = get_unseen_exercise(user_id, "speaking_sentence", level, topic_english)
                    if cached_exercise:
                        exercise_data = cached_exercise.get('exercise_data', {})
                        if isinstance(exercise_data, list) and len(exercise_data) > 0:
                            exercise_id = cached_exercise.get('id')
                            mark_exercise_seen(user_id, exercise_id)
                            st.session_state.speaking_sentences = exercise_data
                            sentences_from_cache = True
                            st.rerun()
            
            # If no cache, generate new sentences
            if not sentences_from_cache:
                with st.spinner("AI đang viết câu..."):
                    prompt = f"Generate 5 useful English sentences about '{topic_for_prompt}' for speaking practice (level {level}). Return JSON list of strings."
                    res = generate_response_with_fallback(prompt)
                    data = parse_json_response(res)
                    if data and isinstance(data, list):
                        st.session_state.speaking_sentences = data
                        # Save to cache
                        if user_id and topic_english:
                            try:
                                save_exercise(
                                    exercise_type="speaking_sentence",
                                    level=level,
                                    topic=topic_english,
                                    exercise_data=data,
                                    user_id=user_id
                                )
                            except Exception as e:
                                logger.warning(f"Error saving speaking sentences to cache: {e}")
                        st.rerun()

    if 'speaking_sentences' not in st.session_state:
        st.session_state.speaking_sentences = [
            "Hello, nice to meet you.", "Where are you from?", 
            "I am learning English with AI.", "Could you speak slower please?"
        ]
    
    s = st.selectbox("Chọn mẫu câu:", st.session_state.speaking_sentences)
    
    # --- GIAO DIỆN FLASHCARD ---
    st.markdown(f"""
    <div class="flashcard">
        <div class="flashcard-sentence">{s}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("🔊 Nghe mẫu", key="sen_tts"):
            play_audio_autoplay(s)
    
    # Ghi âm thực tế cho câu
    audio_val_sen = st.audio_input("Ghi âm câu này", key="rec_sentence")
    
    if audio_val_sen:
        with st.spinner("AI đang phân tích câu nói..."):
            audio_bytes_sen = audio_val_sen.read()
            ok, text = recognize_audio(audio_bytes_sen)
            
            if ok:
                st.markdown(f"🗣️ Bạn đã nói: **{text}**")
                user_id = st.session_state.get("user_info", {}).get("id")
                # Chuẩn hóa để so sánh (bỏ dấu câu, chữ thường)
                translator = str.maketrans('', '', string.punctuation)
                clean_user = text.lower().translate(translator).strip()
                clean_target = s.lower().translate(translator).strip()
                
                if clean_user == clean_target:
                    st.success("🎉 Tuyệt vời! Bạn nói trôi chảy như người bản xứ.")
                    st.balloons()
                    # Track skill progress
                    if user_id:
                        track_skill_progress(user_id, 'speaking', 1, 1)  # 1 exercise, 1 correct
                else:
                    st.warning(f"Gần đúng rồi. AI nghe thấy: '{text}'. Hãy thử lại nhé!")
                    # Track skill progress (0 correct)
                    if user_id:
                        track_skill_progress(user_id, 'speaking', 1, 0)
            else:
                st.error(f"Lỗi nhận dạng: {text}")

# --- TAB 4: LUYỆN NÓI AI ---
elif selected_tab == "🤖 Luyện Nói AI":
    st.subheader("🤖 Trò chuyện cùng AI (Roleplay)")
    st.caption("Chọn tình huống và bắt đầu hội thoại. AI sẽ phản hồi và sửa lỗi cho bạn.")

    # --- LAYOUT ---
    history_col, chat_col = st.columns([1, 2.5])

    # --- SIDEBAR: CHAT HISTORY ---
    with history_col:
        st.markdown("#### Lịch sử hội thoại")
        
        if st.button("➕ Cuộc trò chuyện mới"):
            st.session_state.active_chat_session = None
            st.rerun()

        st.divider()
        
        sessions = get_chat_sessions(st.session_state.user_info['id'])
        if not sessions:
            st.caption("Chưa có cuộc hội thoại nào.")
        else:
            for session in sessions:
                # Highlight active session
                btn_type = "primary" if st.session_state.active_chat_session and st.session_state.active_chat_session['id'] == session['id'] else "secondary"
                if st.button(f"💬 {session['title']}", key=f"session_{session['id']}", type=btn_type):
                    st.session_state.active_chat_session = session
                    st.rerun()

    # --- MAIN CHAT AREA ---
    with chat_col:
        active_session = st.session_state.get('active_chat_session')

        if not active_session:
            # --- NEW CHAT SETUP ---
            st.info("Hãy bắt đầu một cuộc trò chuyện mới từ menu bên trái.")
            scenarios = {
                "Coffee Shop": "You are a barista at a coffee shop. I am a customer ordering a drink.",
                "Job Interview": "You are an interviewer. I am a candidate applying for a software engineer job.",
                "Travel": "You are a local guide. I am a tourist asking for directions.",
                "Free Talk": "You are a friendly English tutor. We are just chatting about hobbies."
            }
            selected_scenario_title = st.selectbox("Chọn tình huống:", list(scenarios.keys()))
            
            if st.button("🚀 Bắt đầu trò chuyện", type="primary"):
                with st.spinner("AI đang khởi động..."):
                    # 1. Create session in DB
                    new_session = create_chat_session(st.session_state.user_info['id'], selected_scenario_title)
                    if new_session:
                        st.session_state.active_chat_session = new_session
                        
                        # 2. Get AI's first message
                        roleplay_context = scenarios[selected_scenario_title]
                        init_prompt = f"Act as defined: '{roleplay_context}'. Start the conversation with a short greeting question (max 20 words)."
                        first_msg = generate_response_with_fallback(init_prompt)
                        
                        # 3. Save AI's first message to DB
                        add_chat_message(new_session['id'], 'ai', first_msg)
                        st.rerun()
                    else:
                        st.error("Không thể tạo cuộc trò chuyện mới.")
        else:
            # --- ACTIVE CHAT INTERFACE ---
            messages = get_chat_messages(active_session['id'])
            
            # Display messages
            for msg in messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    if msg["role"] == "ai":
                        if st.button("🔊", key=f"tts_chat_{msg['id']}"):
                            play_audio_autoplay(msg["content"])
            
            # Chat input
            if user_msg := st.chat_input("Nhập tin nhắn hoặc dùng micro..."):
                # 1. Save user message
                add_chat_message(active_session['id'], 'user', user_msg)
                
                # 2. Get AI response
                with st.spinner("AI đang trả lời..."):
                    # Re-fetch messages to build history for prompt
                    current_messages = get_chat_messages(active_session['id'])
                    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in current_messages[-5:]])
                    
                    scenarios = {
                        "Coffee Shop": "You are a barista...", "Job Interview": "You are an interviewer...",
                        "Travel": "You are a local guide...", "Free Talk": "You are a friendly English tutor..."
                    }
                    roleplay_context = scenarios.get(active_session['title'], "You are a friendly English tutor.")

                    prompt = f"""
                    Context: {roleplay_context}
                    History: {history_text}
                    Task: Reply naturally (short). Then provide feedback on user's last grammar/vocab in Vietnamese wrapped in [Feedback] tag.
                    Format: [Reply] ... [Feedback] ...
                    """
                    res = generate_response_with_fallback(prompt)
                    
                    reply = res
                    feedback = ""
                    if "[Reply]" in res and "[Feedback]" in res:
                        parts = res.split("[Feedback]")
                        reply = parts[0].replace("[Reply]", "").strip()
                        feedback = parts[1].strip()
                    elif "[Feedback]" in res:
                        parts = res.split("[Feedback]")
                        reply = parts[0].strip()
                        feedback = parts[1].strip()
                    
                    # 3. Save AI messages
                    add_chat_message(active_session['id'], 'ai', reply)
                    if feedback:
                        add_chat_message(active_session['id'], 'assistant', f"💡 **Góp ý:** {feedback}")
                    
                    st.rerun()
        
        # --- DEBUG --- (Disabled)
        # render_debug_panel("AI Roleplay", {
        #     "session_id": active_session['id'] if active_session else None,
        #     "last_prompt": st.session_state.get('last_gemini_prompt')
        # })

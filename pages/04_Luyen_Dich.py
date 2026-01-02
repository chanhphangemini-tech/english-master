import streamlit as st
import re
import uuid
import string
from itertools import takewhile
import textwrap
from core.theme_applier import apply_page_theme

apply_page_theme()  # Apply theme + sidebar + auth (includes render_sidebar)
from core.llm import generate_response_with_fallback, parse_json_response
from core.premium import can_use_ai_feature, log_ai_usage, show_premium_upsell
from core.debug_tools import render_debug_panel
from services.vocab_service import add_word_to_srs_and_prioritize, load_progress

st.title("✍️ Luyện Dịch & Phân Tích (Translation Practice)")

# --- PAGE STATE ---
PAGE_ID = "translation_page"
if st.session_state.get('active_page') != PAGE_ID:
    st.session_state.trans_data = None
    st.session_state.trans_feedback = None
    st.session_state.selected_word = None
st.session_state.active_page = PAGE_ID

# --- UI: CONFIGURATION ---
st.subheader("1. Tạo bài dịch")
c1, c2, c3 = st.columns([1, 1, 1])
level = c1.selectbox("Trình độ:", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2) # Default B1
topic = c2.text_input("Nhập chủ đề bạn muốn dịch:", "My favorite hobby")

if can_use_ai_feature("translation"):
    if c3.button("✨ Tạo bài dịch mới", type="primary", width='stretch'):
        with st.spinner(f"AI đang phân tích chủ đề và viết bài..."):
            # NEW: Translate topic to English first
            translation_prompt = f"Translate this topic to English: '{topic}'. Return only the translated English topic."
            english_topic = generate_response_with_fallback(translation_prompt, [topic])

            st.info(f"Đang tạo bài về chủ đề: '{english_topic}'...")
            prompt = f"""
            Write a detailed English passage (about 200-250 words) about '{english_topic}' for CEFR Level {level}.
            Return strictly JSON format: {{"english_text": "...", "vietnamese_translation": "..."}}
            """
            res = generate_response_with_fallback(prompt, ["ERROR"])
            data = parse_json_response(res)
            if data and "english_text" in data:
                log_ai_usage("translation")
                st.session_state.trans_data = data
                st.session_state.trans_feedback = None
                st.session_state.selected_word = None
                st.rerun()
            else:
                st.error("Lỗi khi tạo nội dung. Vui lòng thử lại.")
else:
    with c3:
        show_premium_upsell("Tạo bài dịch", "translation")

st.divider()

# --- UI: TRANSLATION WORKSPACE ---
if st.session_state.get('trans_data'):
    data = st.session_state.trans_data
    english_text = data['english_text']

    st.subheader("2. Dịch đoạn văn sau sang Tiếng Việt")
    
    # --- PREPARE USER VOCABULARY FOR TOOLTIPS ---
    # Tải từ vựng đã học để hiển thị nghĩa khi hover
    user_vocab_map = {}
    try:
        uid = st.session_state.user_info['id']
        progress = load_progress(uid)
        for item in progress:
            v = item.get('Vocabulary', {})
            if v and v.get('word'):
                # Lưu word -> meaning (vietnamese)
                meaning = v.get('meaning', {}).get('vietnamese', '')
                user_vocab_map[v['word'].lower()] = meaning
    except: pass

    # --- WORD CLICK INTERACTION (ST.BUTTON METHOD - SAFE SESSION) ---
    # Sử dụng st.button với CSS tùy chỉnh để tránh reload trang gây mất session
    
    st.markdown("""
    <style>
        /* Style cho button giả lập text */
        .stButton button {
            background: none!important;
            border: none;
            padding: 0!important;
            color: black !important;
            text-decoration: none;
            cursor: pointer;
            border-bottom: 1px dotted #555 !important;
            margin-right: 4px;
            font-size: 1.1em;
            line-height: 1.8;
            display: inline;
        }
        .stButton button:hover {
            color: #007BFF !important;
            border-bottom: 2px solid #007BFF !important;
            background-color: #e3f2fd !important;
        }
        .stButton {
            display: inline-block;
            margin: 0;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        words_and_spaces = re.split(r'(\s+)', english_text)
        
        # Chúng ta sẽ render từng cụm từ. Streamlit không hỗ trợ inline button hoàn hảo trong 1 dòng văn bản dài.
        # Tuy nhiên, để đạt được yêu cầu "click không reload" và "hover hiện nghĩa", 
        # cách tốt nhất là dùng st.markdown với HTML tooltip, và hy sinh tính năng click-to-save một chút 
        # HOẶC dùng st.button cho từng từ (nhưng sẽ bị vỡ dòng nếu không CSS cực khéo).
        
        # GIẢI PHÁP TỐI ƯU: Dùng HTML thuần với Tooltip cho từ đã học.
        # Với từ chưa học, ta dùng thẻ <a> đặc biệt có onclick gọi hàm JS (nhưng Streamlit chặn JS).
        # Nên ta quay lại phương án: Hiển thị văn bản HTML có Tooltip. 
        # Bên dưới văn bản, có một ô nhập liệu "Tra từ nhanh" để người dùng nhập từ cần lưu.
        
        # Xử lý văn bản để thêm Tooltip
        html_content = []
        for word in words_and_spaces:
            clean_word = word.strip(string.punctuation).lower()
            meaning = user_vocab_map.get(clean_word)
            
            if meaning:
                # Từ đã học: Hiện màu xanh + Tooltip nghĩa
                html_content.append(f'<span title="{meaning}" style="color:#2e7d32; font-weight:500; border-bottom:1px dashed #2e7d32; cursor:help;">{word}</span>')
            else:
                # Từ chưa học: Bình thường
                html_content.append(word)
        
        final_html = "".join(html_content).replace("\n", "<br>")
        
        st.markdown(f"""
        <div style="font-size: 1.1em; line-height: 1.8; text-align: justify;">
            {final_html}
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("💡 **Mẹo:** Rê chuột vào các từ màu xanh để xem nghĩa (từ đã học).")

    # --- QUICK LOOKUP & SAVE ---
    c_look, c_save = st.columns([3, 1])
    lookup_word = c_look.text_input("Tra & Lưu từ mới:", placeholder="Nhập từ bạn muốn lưu vào SRS...", key="quick_lookup")
    
    if c_save.button("🔍 Tra & Lưu", type="primary", width='stretch'):
        if lookup_word:
            st.session_state.selected_word = lookup_word.strip()
            # Không cần rerun, logic popup bên dưới sẽ xử lý

    # --- POPUP/MODAL for selected word ---
    if st.session_state.get('selected_word'):
        word = st.session_state.selected_word
        with st.spinner(f"AI đang dịch nghĩa từ '{word}'..."):
            meaning_prompt = f"What is the Vietnamese meaning of the English word '{word}'? Return just the meaning, no extra text."
            meaning = generate_response_with_fallback(meaning_prompt, ["Không rõ"])

        st.info(f"**Từ đã chọn:** `{word}`\n\n**Nghĩa Tiếng Việt:** {meaning}")
        c1_pop, c2_pop, c3_pop = st.columns(3)
        if c1_pop.button("➕ Lưu vào SRS", key="save_word_srs", type="primary"):
            uid = st.session_state.user_info['id']
            if add_word_to_srs_and_prioritize(uid, word, "unknown", meaning):
                st.toast(f"Đã thêm '{word}' vào danh sách ưu tiên học!", icon="✅")
                st.session_state.selected_word = None
                st.rerun()
            else:
                st.error("Lỗi khi lưu từ.")
        if c2_pop.button("Đóng", key="close_popup"):
            st.session_state.selected_word = None
            st.rerun()

    # --- USER INPUT & GRADING ---
    user_translation = st.text_area("Nhập bài dịch của bạn vào đây:", height=200, key="user_trans_input")

    if st.button("Chấm điểm bài dịch", disabled=(not user_translation)):
        with st.spinner("AI đang chấm điểm và phân tích bài dịch của bạn..."):
            grading_prompt = f"""
            As an expert translator and examiner, evaluate a user's Vietnamese translation of an English text.
            
            Original English Text:
            '''{english_text}'''
            
            Official Vietnamese Translation (for reference):
            '''{data['vietnamese_translation']}'''
            
            User's Vietnamese Translation:
            '''{user_translation}'''
            
            Task: Provide feedback in Vietnamese. Return strictly JSON format:
            {{
                "score": "X/10",
                "overall_comment": "A general comment on the translation's accuracy, naturalness, and style.",
                "strengths": "What the user did well (e.g., good word choice, correct structure).",
                "areas_for_improvement": [
                    {{
                        "original_phrase": "The English phrase the user struggled with",
                        "user_translation": "The user's incorrect translation of that phrase",
                        "suggested_translation": "A better, more natural Vietnamese translation",
                        "explanation": "Why the suggestion is better (e.g., idiom, context, nuance)."
                    }}
                ]
            }}
            """
            res = generate_response_with_fallback(grading_prompt, ["ERROR"])
            feedback_data = parse_json_response(res)
            if feedback_data and "score" in feedback_data:
                st.session_state.trans_feedback = feedback_data
            else:
                st.error("Lỗi khi chấm điểm. Vui lòng thử lại.")
                st.session_state.trans_feedback = None

    # --- DISPLAY FEEDBACK ---
    if st.session_state.get('trans_feedback'):
        st.divider()
        st.subheader("3. Phân tích từ AI")
        feedback = st.session_state.trans_feedback
        
        score_val = 0
        try:
            score_val = int(feedback.get('score', '0/10').split('/')[0])
        except: pass

        st.progress(score_val / 10, text=f"Điểm dịch thuật: {feedback.get('score', 'N/A')}")
        
        st.markdown(f"** nhận xét chung:** {feedback.get('overall_comment')}")
        
        c_good, c_bad = st.columns(2)
        with c_good:
            with st.container(border=True):
                st.markdown("#### 👍 Điểm tốt")
                st.success(feedback.get('strengths'))
        with c_bad:
            with st.container(border=True):
                st.markdown("#### 📉 Cần cải thiện")
                improvements = feedback.get('areas_for_improvement', [])
                if not improvements:
                    st.info("Không có lỗi nào đáng kể!")
                else:
                    for item in improvements:
                        st.error(f"**Gốc:** `{item['original_phrase']}`")
                        st.warning(f"**Bạn dịch:** `{item['user_translation']}`")
                        st.info(f"**Gợi ý:** `{item['suggested_translation']}`")
                        st.caption(f"💡 {item['explanation']}")
                        st.markdown("---")

        with st.expander("Xem bản dịch tham khảo của AI"):
            st.write(data['vietnamese_translation'])

else:
    st.info("👈 Hãy chọn chủ đề và bấm 'Tạo bài dịch mới' để bắt đầu.")


# --- DEBUG PANEL --- (Disabled)
# render_debug_panel("Translation Page", {
#     "trans_data": st.session_state.get('trans_data'),
#     "trans_feedback": st.session_state.get('trans_feedback'),
#     "selected_word": st.session_state.get('selected_word'),
#     "token_analysis": locals().get('debug_tokens', "N/A")
# })
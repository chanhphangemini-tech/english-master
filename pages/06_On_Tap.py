import streamlit as st
import time
import pandas as pd
import random
from typing import Dict, Any

from core.theme_applier import apply_page_theme
from core.utils import play_sound
from core.debug_tools import render_debug_panel
from core.ui_styles import apply_vocab_card_styles
from services.vocab_service import (
    get_due_vocabulary, 
    get_daily_learning_batch, 
    update_srs_stats, 
    add_word_to_srs, 
    load_vocab_data, 
    load_progress
)
from services.user_service import log_activity, add_coins
from views.review_view import (
    render_study_config,
    render_word_card,
    render_quiz_question,
    render_quiz_result,
    normalize_meaning,
    calculate_quiz_score,
    render_quiz_score_summary
)

st.set_page_config(page_title="Học & Ôn Tập | English Master", page_icon="✍️", layout="wide")

# Theme is already applied via apply_page_theme() at the top
apply_vocab_card_styles()

if not st.session_state.get('logged_in'):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

uid: int = st.session_state.user_info['id']

# Admin luôn là Premium
is_admin = str(st.session_state.user_info.get('role', 'user')).lower() == 'admin'
account_type = 'premium' if is_admin else st.session_state.user_info.get('plan', 'free')

# --- UI ---
st.title("✍️ Học & Ôn Tập")

# Premium Export Feature
if account_type == 'premium':
    with st.expander("💎 Premium: Xuất dữ liệu từ vựng", expanded=False):
        st.caption("Xuất danh sách từ vựng đã học với progress và SRS stats (CSV/Excel)")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Xuất CSV", key="export_csv"):
                from services.export_service import export_vocabulary_csv
                csv_data = export_vocabulary_csv(uid)
                if csv_data:
                    st.download_button(
                        label="⬇️ Tải file CSV",
                        data=csv_data,
                        file_name=f"vocabulary_export_{uid}_{time.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
                else:
                    st.warning("Không có dữ liệu để xuất.")
        with col2:
            if st.button("📊 Xuất Excel", key="export_excel"):
                from services.export_service import export_vocabulary_excel
                excel_data = export_vocabulary_excel(uid)
                if excel_data:
                    st.download_button(
                        label="⬇️ Tải file Excel",
                        data=excel_data,
                        file_name=f"vocabulary_export_{uid}_{time.strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_excel"
                    )
                else:
                    st.warning("Không có dữ liệu để xuất.")

# --- SESSION STATE INITIALIZATION ---
if 'quiz_mode' not in st.session_state: st.session_state.quiz_mode = False
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = pd.DataFrame()
if 'quiz_submitted' not in st.session_state: st.session_state.quiz_submitted = False
if 'attempt_count' not in st.session_state: st.session_state.attempt_count = 0
if 'quiz_type' not in st.session_state: st.session_state.quiz_type = "meaning"
if 'saved_quiz_answers' not in st.session_state: st.session_state.saved_quiz_answers = {}

progress_df = pd.DataFrame(load_progress(uid))

def render_learning_view(uid: int, progress_df: pd.DataFrame, account_type: str) -> None:
    """Render the main learning view with vocabulary cards."""
    # Initialize variables outside expander to ensure they're always defined
    all_levels = [f"A{i}" for i in range(1, 3)] + [f"B{i}" for i in range(1, 3)] + [f"C{i}" for i in range(1, 3)]
    target_level = all_levels[0]  # Default to first level
    daily_limit = 10  # Default value
    vocab_df_temp = pd.DataFrame()
    selected_topics = []
    
    # Configuration section (using existing logic for now, can be moved to view later)
    with st.expander("⚙️ Cấu hình nội dung học", expanded=True):
        target_level = st.selectbox("1. Chọn trình độ:", options=all_levels, index=0)
        
        # Logic Premium - Check if user has premium subscription (basic/premium/pro)
        from services.premium_usage_service import has_premium_subscription
        user_plan = st.session_state.user_info.get('plan', 'free')
        is_admin_user = str(st.session_state.user_info.get('role', 'user')).lower() == 'admin'
        is_premium_user = has_premium_subscription(user_plan=user_plan) or is_admin_user
        
        # Premium users (Basic/Premium/Pro) have no limit, Free users are limited to 20
        max_words = 999 if is_premium_user else 20
        daily_limit = st.number_input("2. Số từ mới mỗi ngày:", min_value=5, max_value=max_words, value=min(10, max_words), step=5)
        if not is_premium_user:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"🔒 Free: Tối đa 20 từ.")
            with col2:
                if st.button("⭐ Premium", key="upgrade_premium_config"):
                    st.switch_page("pages/15_Premium.py")

        # Lấy danh sách chủ đề
        vocab_data = load_vocab_data(target_level)
        vocab_df_temp = pd.DataFrame(vocab_data)
        topic_options = []
        topic_map = {}

        if not vocab_df_temp.empty:
            raw_topics = sorted(list(set(vocab_df_temp['topic'].dropna().unique())))
            user_learned_words = set(progress_df['Vocabulary'].apply(lambda x: x.get('word') if isinstance(x, dict) else None).dropna().unique()) if not progress_df.empty else set()

            for t in raw_topics:
                words_in_topic = vocab_df_temp[vocab_df_temp['topic'] == t]['word'].unique()
                total_w = len(words_in_topic)
                learned_w = len([w for w in words_in_topic if w in user_learned_words])
                
                display_name = f"{t} ({learned_w}/{total_w})"
                topic_options.append(display_name)
                topic_map[display_name] = t

            selected_display_topics = st.multiselect("3. Chọn chủ đề (Tùy chọn):", options=topic_options, default=[], key=f"topic_select_{target_level}")
            selected_topics = [topic_map[t] for t in selected_display_topics]
        else:
            selected_topics = []
            st.warning(f"Không có từ vựng cho cấp độ {target_level}")
    
    # Đảm bảo vocab_df và selected_topics được định nghĩa bên ngoài expander block
    vocab_df = vocab_df_temp if 'vocab_df_temp' in locals() else pd.DataFrame(load_vocab_data(target_level))
    if 'selected_topics' not in locals():
        selected_topics = []

    # Lấy kế hoạch học tập - Lấy TẤT CẢ từ chưa học từ các chủ đề đã chọn
    if selected_topics:
        # Lấy tất cả từ chưa học từ các topic đã chọn (không giới hạn per topic)
        from core.database import supabase
        
        # 1. Lấy danh sách ID các từ đã học
        learned_res = supabase.table("UserVocabulary").select("vocab_id").eq("user_id", int(uid)).execute()
        learned_ids = [item['vocab_id'] for item in learned_res.data] if learned_res.data else []
        
        # 2. Lấy tất cả từ vựng từ vocab_df (đã filter theo level) và filter theo topics
        all_vocab = vocab_df[vocab_df['topic'].isin(selected_topics)].copy()
        
        # 3. Loại bỏ các từ đã học
        if learned_ids:
            all_vocab = all_vocab[~all_vocab['id'].isin(learned_ids)]
        
        # 4. Convert to list of dicts và giới hạn số lượng
        all_new_words = all_vocab.to_dict('records')
        
        # 5. Giới hạn số lượng theo daily_limit
        new_words_df = all_new_words[:daily_limit] if len(all_new_words) > daily_limit else all_new_words
    else:
        new_words_df = get_daily_learning_batch(uid, target_level, daily_limit, "General")
    
    review_df = get_due_vocabulary(uid)

    st.divider()
    st.info(f"🔥 Từ mới hôm nay: **{len(new_words_df)}** từ | 📝 Cần ôn tập: **{len(review_df)}** từ")

    st.subheader("📖 Phần 1: Học Từ Mới & Ôn Tập")
    st.caption("Hãy học kỹ các từ dưới đây trước khi làm bài kiểm tra.")

    # Gộp và hiển thị
    new_words_df = pd.DataFrame(new_words_df).assign(type='new')
    review_df = pd.DataFrame(review_df).assign(type='review')
    
    # Trong review_df, dữ liệu từ vựng nằm trong cột 'Vocabulary'
    if not review_df.empty and 'Vocabulary' in review_df.columns:
        review_vocab_data = pd.json_normalize(review_df['Vocabulary'])
        review_df = pd.concat([review_df.drop(columns=['Vocabulary']), review_vocab_data], axis=1)

    combined_view = pd.concat([new_words_df, review_df]).drop_duplicates(subset=['word'])
    
    if not combined_view.empty and 'meaning' in combined_view.columns:
        combined_view['meaning'] = combined_view['meaning'].apply(normalize_meaning)

    if combined_view.empty:
        st.success("🎉 Bạn không có bài tập nào theo cấu hình này.")
        return

    # Hiển thị danh sách gọn gàng thay vì cards
    st.markdown("#### 📋 Danh sách từ vựng")
    
    # Cache audio trong session_state để tránh reload
    audio_cache_key_prefix = 'vocab_audio_'
    if audio_cache_key_prefix not in st.session_state:
        st.session_state[audio_cache_key_prefix] = {}
    
    # Render tất cả vocabulary items cùng lúc (không blocking)
    for idx, row in combined_view.iterrows():
        is_new = row.get('type') == 'new'
        word = row['word']
        meaning = row.get('meaning', {})
        if isinstance(meaning, dict):
            vietnamese_meaning = meaning.get('vietnamese', 'Không có nghĩa')
        else:
            vietnamese_meaning = str(meaning)
        
        pronunciation = row.get('pronunciation', '')
        
        # Hiển thị gọn gàng trong một dòng với expander
        with st.expander(f"{'🆕 ' if is_new else '📝 '}**{word}** - *{vietnamese_meaning}*{f' ({pronunciation})' if pronunciation else ''}", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Nghĩa:** {vietnamese_meaning}")
                if pronunciation:
                    st.markdown(f"**Phát âm:** `{pronunciation}`")
                example = row.get('example', '')
                example_translation = row.get('example_translation', '')
                if example and example != 'N/A':
                    st.markdown(f"**Ví dụ:** {example}")
                    if example_translation and example_translation != 'N/A':
                        st.markdown(f"*{example_translation}*")
                
                # Additional details
                collocations = row.get('collocations')
                phrasal_verbs = row.get('phrasal_verbs')
                word_forms = row.get('word_forms')
                synonyms = row.get('synonyms')
                usage_notes = row.get('usage_notes')
                
                has_details = bool(collocations or phrasal_verbs or word_forms or synonyms or usage_notes)
                if has_details:
                    with st.expander("📚 Chi tiết từ vựng", expanded=False):
                        # Collocations
                        if collocations and isinstance(collocations, list) and len(collocations) > 0:
                            st.markdown("**🔗 Từ đi kèm:**")
                            for colloc in collocations[:3]:  # Show max 3 in compact view
                                st.markdown(f"- {colloc}")
                            st.markdown("")  # Spacing
                        
                        # Phrasal Verbs
                        if phrasal_verbs and phrasal_verbs.strip():
                            st.markdown(f"**⚡ Cụm động từ:** `{phrasal_verbs}`")
                            st.markdown("")  # Spacing
                        
                        # Word Forms
                        if word_forms and isinstance(word_forms, dict):
                            forms_list = []
                            if word_forms.get('noun'):
                                forms_list.append(f"Danh từ: {word_forms['noun']}")
                            if word_forms.get('verb'):
                                forms_list.append(f"Động từ: {word_forms['verb']}")
                            if word_forms.get('adjective'):
                                forms_list.append(f"Tính từ: {word_forms['adjective']}")
                            if word_forms.get('adverb'):
                                forms_list.append(f"Trạng từ: {word_forms['adverb']}")
                            
                            if forms_list:
                                st.markdown(f"**🔤 Dạng từ:** {', '.join(forms_list)}")
                                st.markdown("")  # Spacing
                        
                        # Synonyms
                        if synonyms and isinstance(synonyms, list) and len(synonyms) > 0:
                            syns_text = ", ".join(synonyms[:3])  # Show max 3
                            st.markdown(f"**🔀 Từ đồng nghĩa:** *{syns_text}*")
                            st.markdown("")  # Spacing
                        
                        # Usage Notes
                        if usage_notes and usage_notes.strip():
                            from core.translator import translate_usage_notes
                            translated_notes = translate_usage_notes(usage_notes)
                            st.markdown("**💡 Ghi chú cách dùng:**")
                            st.info(translated_notes)
            with col2:
                # Sử dụng cached audio URL trực tiếp (nhanh - chỉ query metadata, không download bytes)
                from services.tts_cache_service import get_cached_audio_url
                audio_url = get_cached_audio_url(word)
                
                if audio_url:
                    # Audio đã có trong cache - sử dụng URL trực tiếp (nhanh hơn nhiều)
                    # st.audio() có thể nhận URL string
                    try:
                        st.audio(audio_url, format='audio/mp3')
                    except Exception:
                        # Fallback: Nếu st.audio không hỗ trợ URL, dùng HTML audio tag
                        st.markdown(f"""
                            <audio controls style="width: 100%;">
                                <source src="{audio_url}" type="audio/mpeg">
                                Your browser does not support the audio element.
                            </audio>
                        """, unsafe_allow_html=True)
                else:
                    # Audio chưa có trong cache - có thể generate
                    audio_cache_key = f"{audio_cache_key_prefix}{word}"
                    
                    # Check session cache first (đã generate trước đó trong session này)
                    if audio_cache_key in st.session_state[audio_cache_key_prefix]:
                        audio_bytes = st.session_state[audio_cache_key_prefix][audio_cache_key]
                        if audio_bytes:
                            st.audio(audio_bytes, format='audio/mp3')
                    else:
                        # Button để generate audio nếu chưa có
                        if st.button("🔊 Tạo audio", key=f"audio_btn_{idx}_{word}", help="Tạo audio cho từ này (sẽ được cache tự động)"):
                            with st.spinner("Đang tạo audio..."):
                                from core.tts import get_tts_audio
                                audio_bytes = get_tts_audio(word)
                                if audio_bytes:
                                    # Cache audio bytes trong session (sẽ được cache trong DB tự động bởi TTS service)
                                    st.session_state[audio_cache_key_prefix][audio_cache_key] = audio_bytes
                                    st.rerun()
                        else:
                            st.caption("Click để tạo audio")

    st.divider()
    st.markdown("### 🎯 Sẵn sàng kiểm tra?")
    c_mode, c_btn = st.columns([2, 1])
    with c_mode:
        mode_selection = st.selectbox("Chọn chế độ kiểm tra:", ["Kiểm tra nghĩa (Điền nghĩa tiếng Việt)", "Kiểm tra từ (Điền từ tiếng Anh)"])
        st.session_state.quiz_type = "meaning" if "nghĩa" in mode_selection else "word"
    with c_btn:
        st.write("")
        st.write("")
        if st.button("🚀 BẮT ĐẦU LÀM BÀI", type="primary"):
            st.session_state.quiz_data = combined_view.sample(frac=1).reset_index(drop=True)
            st.session_state.quiz_submitted = False
            st.session_state.attempt_count += 1
            st.session_state.quiz_mode = True
            st.rerun()

def render_quiz_view(uid: int) -> None:
    """Render quiz interface and handle submission."""
    if st.session_state.quiz_submitted:
        for index, row in st.session_state.quiz_data.iterrows():
            k = f"q_{index}_attempt_{st.session_state.attempt_count}"
            if k not in st.session_state and k in st.session_state.saved_quiz_answers:
                st.session_state[k] = st.session_state.saved_quiz_answers[k]

    st.warning("🔒 ĐANG KIỂM TRA: Hãy chọn đáp án đúng cho mỗi câu.")
    quiz_df = st.session_state.quiz_data

    if quiz_df.empty:
        st.error("Dữ liệu bài thi trống. Vui lòng quay lại.")
        if st.button("Quay lại"):
            st.session_state.quiz_mode = False
            st.rerun()
        return

    with st.form("quiz_form"):
        for index, row in quiz_df.iterrows():
            render_quiz_question(index, row, st.session_state.quiz_type, st.session_state.attempt_count, quiz_df)
        
        if not st.session_state.quiz_submitted:
            if st.form_submit_button("📤 NỘP BÀI", type="primary"):
                for index, row in quiz_df.iterrows():
                    k = f"q_{index}_attempt_{st.session_state.attempt_count}"
                    st.session_state.saved_quiz_answers[k] = st.session_state.get(k, "")
                st.session_state.quiz_submitted = True
                st.rerun()

    if st.session_state.quiz_submitted:
        score_quiz(uid, quiz_df)

def score_quiz(uid: int, quiz_df: pd.DataFrame) -> None:
    """Score the quiz and display results."""
    st.subheader("📊 Kết quả chi tiết")
    correct_count = 0
    total_q = len(quiz_df)

    for index, row in quiz_df.iterrows():
        input_key = f"q_{index}_attempt_{st.session_state.attempt_count}"
        u_ans = st.session_state.saved_quiz_answers.get(input_key, "")
        
        meaning_dict = row.get('meaning', {}) if isinstance(row.get('meaning'), dict) else {}
        correct_meaning = meaning_dict.get('vietnamese', 'N/A')
        
        is_right = False
        if st.session_state.quiz_type == "meaning":
            # Normalize answers for comparison (case-insensitive, strip whitespace)
            u_ans_normalized = normalize_meaning_text(u_ans.strip().lower() if u_ans else "")
            correct_normalized = normalize_meaning_text(correct_meaning.strip().lower() if correct_meaning else "")
            is_right = (u_ans_normalized == correct_normalized)
        else:  # quiz_type == "word"
            # Normalize word answers (case-insensitive, strip whitespace)
            u_ans_normalized = u_ans.strip().lower() if u_ans else ""
            correct_word_normalized = row['word'].strip().lower() if row.get('word') else ""
            is_right = (u_ans_normalized == correct_word_normalized)

        quality = 5 if is_right else 1
        
        # Update database
        word_type = row.get('type')
        if word_type == 'review':
            vid = row.get('vocab_id')
            if vid: update_srs_stats(uid, vid, quality)
        elif word_type == 'new' and is_right:
            add_word_to_srs(uid, row['id'])

        if is_right:
            correct_count += 1
        
        # Render result
        render_quiz_result(index, row, u_ans, st.session_state.quiz_type, is_right)

    final_score = (correct_count / total_q) * 100 if total_q > 0 else 0
    st.progress(final_score / 100)
    st.metric("Điểm số", f"{correct_count}/{total_q}", f"{final_score:.1f}%")

    if final_score == 100:
        play_sound("success")
        st.balloons()
    else:
        play_sound("fail")

    log_activity(uid, "quiz_complete", correct_count)
    
    # Thưởng coin
    coin_reward = correct_count * 2
    if coin_reward > 0:
        add_coins(uid, coin_reward)
        st.toast(f"💰 Bạn nhận được {coin_reward} coins!", icon="💰")

    c_save, c_retry = st.columns(2)
    with c_save:
        if st.button("💾 TIẾP TỤC HỌC", type="primary"):
            st.session_state.quiz_mode = False
            st.session_state.quiz_submitted = False
            st.session_state.quiz_data = pd.DataFrame()
            st.rerun()
    with c_retry:
        if st.button("🔄 Làm lại bài này"):
            st.session_state.quiz_submitted = False
            st.session_state.attempt_count += 1
            st.rerun()

# --- MAIN LOGIC ---
if not st.session_state.quiz_mode:
    render_learning_view(uid, progress_df, account_type)
else:
    render_quiz_view(uid)

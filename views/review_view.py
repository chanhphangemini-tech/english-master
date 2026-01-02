"""View components for Review/Study page."""
import streamlit as st
import pandas as pd
import random
from typing import Dict, List, Any, Optional, Tuple
import logging

from core.vocab_utils import normalize_meaning, get_vietnamese_meaning, format_pronunciation

logger = logging.getLogger(__name__)


def render_study_config(account_type: str, vocab_df: pd.DataFrame, progress_df: pd.DataFrame, target_level: str) -> Tuple[str, int, List[str]]:
    """Render study configuration section.
    
    Returns:
        Tuple of (target_level, daily_limit, selected_topics)
    """
    with st.expander("⚙️ Cấu hình nội dung học", expanded=True):
        all_levels = [f"A{i}" for i in range(1, 3)] + [f"B{i}" for i in range(1, 3)] + [f"C{i}" for i in range(1, 3)]
        target_level = st.selectbox("1. Chọn trình độ:", options=all_levels, index=0)
        
        # Logic Premium
        max_words = 50 if account_type == 'premium' else 20
        daily_limit = st.number_input("2. Số từ mới mỗi ngày:", min_value=5, max_value=max_words, value=min(10, max_words), step=5)
        if account_type != 'premium':
            st.caption(f"🔒 Free: Tối đa 20 từ.")
            if st.button("⭐ Nâng cấp Premium", key="upgrade_premium_review", type="secondary"):
                st.switch_page("pages/15_Premium.py")

        # Topic selection
        topic_options = []
        topic_map = {}

        if not vocab_df.empty:
            raw_topics = sorted(list(set(vocab_df['topic'].dropna().unique())))
            user_learned_words = set(progress_df['Vocabulary'].apply(lambda x: x.get('word') if isinstance(x, dict) else None).dropna().unique()) if not progress_df.empty else set()

            for t in raw_topics:
                words_in_topic = vocab_df[vocab_df['topic'] == t]['word'].unique()
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

    return target_level, daily_limit, selected_topics


def render_word_card(row: pd.Series, index: int) -> None:
    """Render a simple, readable vocabulary word card."""
    is_new = row.get('type') == 'new'
    from core.tts import get_tts_audio
    import base64
    
    # Pre-load audio for instant playback
    audio_bytes = get_tts_audio(row['word'])
    
    # Get data
    pronunciation = row.get('pronunciation', '')
    meaning = normalize_meaning(row.get('meaning', {}))
    vietnamese_meaning = meaning.get('vietnamese', 'Không có nghĩa')
    example = row.get('example', '')
    example_translation = row.get('example_translation', '')
    
    # Simple, readable card with Streamlit components
    with st.container(border=True):
        # Word with NEW badge
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"# {row['word']}")
        with col2:
            if is_new:
                st.markdown("🆕 **MỚI**")
        
        # Pronunciation
        if pronunciation:
            st.markdown(f"**Phát âm:** `{pronunciation}`")
        
        # Meaning in larger, bold font
        st.markdown(f"### *{vietnamese_meaning}*")
        
        st.divider()
        
        # TTS Button - Working with fallback
        if audio_bytes:
            unique_id = f"tts_{abs(hash(row['word']))}"
            
            # Use native st.audio for guaranteed playback
            st.audio(audio_bytes, format='audio/mp3')
        
        # Example
        if example and example != 'N/A':
            with st.expander("📖 Ví dụ minh họa"):
                st.markdown(f"**EN:** {example}")
                if example_translation and example_translation != 'N/A':
                    st.markdown(f"**VI:** {example_translation}")
        
        # Additional details (collocations, word_forms, synonyms, usage_notes)
        has_details = False
        collocations = row.get('collocations')
        phrasal_verbs = row.get('phrasal_verbs')
        word_forms = row.get('word_forms')
        synonyms = row.get('synonyms')
        usage_notes = row.get('usage_notes')
        
        if collocations or phrasal_verbs or word_forms or synonyms or usage_notes:
            has_details = True
        
        if has_details:
            with st.expander("📚 Chi tiết từ vựng", expanded=False):
                # Collocations
                if collocations and isinstance(collocations, list) and len(collocations) > 0:
                    st.markdown("**🔗 Từ đi kèm:**")
                    for colloc in collocations[:5]:  # Show max 5
                        st.markdown(f"- {colloc}")
                    st.markdown("")
                
                # Phrasal Verbs
                if phrasal_verbs and phrasal_verbs.strip():
                    st.markdown(f"**⚡ Cụm động từ:** `{phrasal_verbs}`")
                    st.markdown("")
                
                # Word Forms
                if word_forms and isinstance(word_forms, dict):
                    forms = []
                    if word_forms.get('noun'):
                        forms.append(f"**Danh từ:** {word_forms['noun']}")
                    if word_forms.get('verb'):
                        forms.append(f"**Động từ:** {word_forms['verb']}")
                    if word_forms.get('adjective'):
                        forms.append(f"**Tính từ:** {word_forms['adjective']}")
                    if word_forms.get('adverb'):
                        forms.append(f"**Trạng từ:** {word_forms['adverb']}")
                    
                    if forms:
                        st.markdown("**🔤 Dạng từ:**")
                        for form in forms:
                            st.markdown(f"- {form}")
                        st.markdown("")
                
                # Synonyms
                if synonyms and isinstance(synonyms, list) and len(synonyms) > 0:
                    st.markdown("**🔀 Từ đồng nghĩa:**")
                    syns_text = ", ".join(synonyms[:5])  # Show max 5
                    st.markdown(f"*{syns_text}*")
                    st.markdown("")
                
                # Usage Notes
                if usage_notes and usage_notes.strip():
                    from core.translator import translate_usage_notes
                    translated_notes = translate_usage_notes(usage_notes)
                    st.markdown("**💡 Ghi chú cách dùng:**")
                    st.info(translated_notes)


def render_quiz_question(index: int, row: pd.Series, quiz_type: str, attempt_count: int, all_words: pd.DataFrame) -> None:
    """Render a single quiz question."""
    meaning_dict = row.get('meaning', {}) if isinstance(row.get('meaning'), dict) else {}
    correct_meaning = meaning_dict.get('vietnamese', 'N/A')
    
    # Generate options
    other_meanings = all_words['meaning'].apply(lambda x: x.get('vietnamese') if isinstance(x, dict) else None).dropna().unique().tolist()
    if correct_meaning in other_meanings:
        other_meanings.remove(correct_meaning)
    options = random.sample(other_meanings, min(3, len(other_meanings))) + [correct_meaning]
    random.shuffle(options)

    if quiz_type == "meaning":
        st.markdown(f"##### Câu {index + 1}: Từ **{row['word']}** có nghĩa là gì?")
        st.radio("Chọn nghĩa đúng:", options, key=f"q_{index}_attempt_{attempt_count}", index=None)
    else:  # quiz_type == "word"
        st.markdown(f"##### Câu {index + 1}: Nghĩa **'{correct_meaning}'** là của từ nào?")
        word_options = random.sample(all_words['word'].tolist(), min(3, len(all_words)-1)) + [row['word']]
        random.shuffle(word_options)
        st.radio("Chọn từ đúng:", word_options, key=f"q_{index}_attempt_{attempt_count}", index=None)
    
    st.divider()


def render_quiz_result(index: int, row: pd.Series, user_answer: str, quiz_type: str, is_correct: bool) -> None:
    """Render quiz result for a single question."""
    meaning_dict = row.get('meaning', {}) if isinstance(row.get('meaning'), dict) else {}
    correct_meaning = meaning_dict.get('vietnamese', 'N/A')
    
    if quiz_type == "meaning":
        correct_ans_display = correct_meaning
    else:
        correct_ans_display = row['word']

    if is_correct:
        st.success(f"**Câu {index+1}:** ✅ Chính xác! ({user_answer})")
    else:
        st.error(f"**Câu {index+1}:** ❌ Sai. Bạn chọn: '{user_answer}' | Đáp án đúng: '{correct_ans_display}'")


# normalize_meaning is now imported from core.vocab_utils


def calculate_quiz_score(quiz_df: pd.DataFrame, quiz_type: str, saved_answers: Dict[str, str], attempt_count: int) -> tuple:
    """Calculate quiz score and collect results.
    
    Args:
        quiz_df: Quiz DataFrame
        quiz_type: Type of quiz ("meaning" or "word")
        saved_answers: Dictionary of saved user answers
        attempt_count: Current attempt count
        
    Returns:
        Tuple of (correct_count, total_questions, results_list)
    """
    correct_count = 0
    total_q = len(quiz_df)
    results = []
    
    for index, row in quiz_df.iterrows():
        input_key = f"q_{index}_attempt_{attempt_count}"
        u_ans = saved_answers.get(input_key, "")
        
        meaning_dict = row.get('meaning', {}) if isinstance(row.get('meaning'), dict) else {}
        correct_meaning = meaning_dict.get('vietnamese', 'N/A')
        
        if quiz_type == "meaning":
            is_right = (u_ans == correct_meaning)
            correct_ans_display = correct_meaning
        else:
            is_right = (u_ans == row['word'])
            correct_ans_display = row['word']
        
        quality = 5 if is_right else 1
        word_type = row.get('type')
        
        results.append({
            'index': index,
            'is_right': is_right,
            'user_answer': u_ans,
            'correct_answer': correct_ans_display,
            'quality': quality,
            'word_type': word_type,
            'vocab_id': row.get('vocab_id') if word_type == 'review' else None,
            'new_vocab_id': row.get('id') if word_type == 'new' else None
        })
        
        if is_right:
            correct_count += 1
    
    return correct_count, total_q, results


def render_quiz_score_summary(correct_count: int, total_q: int) -> None:
    """Render quiz score summary.
    
    Args:
        correct_count: Number of correct answers
        total_q: Total number of questions
    """
    final_score = (correct_count / total_q) * 100 if total_q > 0 else 0
    st.progress(final_score / 100)
    st.metric("Điểm số", f"{correct_count}/{total_q}", f"{final_score:.1f}%")


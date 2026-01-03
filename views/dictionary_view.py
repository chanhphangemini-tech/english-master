"""View components for Dictionary page - Full vocabulary library."""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging

from core.tts import get_tts_audio
from core.vocab_utils import normalize_meaning, get_vietnamese_meaning, format_pronunciation

logger = logging.getLogger(__name__)


def transform_vocabulary_to_dataframe(vocab_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Transform vocabulary data to DataFrame format.
    
    Args:
        vocab_data: Raw vocabulary data from database
        
    Returns:
        DataFrame with vocabulary data
    """
    flattened_data = []
    for item in vocab_data:
        meaning = normalize_meaning(item.get('meaning', {}))
        vietnamese_meaning = meaning.get('vietnamese', 'Không có nghĩa')
        
        flattened_data.append({
            "id": item.get('id'),
            "word": item.get('word', ''),
            "pronunciation": item.get('pronunciation', ''),
            "meaning": vietnamese_meaning,
            "type": item.get('type', ''),
            "level": item.get('level', ''),
            "topic": item.get('topic', ''),
            "example": item.get('example', ''),
            "example_translation": item.get('example_translation', ''),
            "collocations": item.get('collocations'),
            "phrasal_verbs": item.get('phrasal_verbs'),
            "word_forms": item.get('word_forms'),
            "synonyms": item.get('synonyms'),
            "usage_notes": item.get('usage_notes')
        })
    
    return pd.DataFrame(flattened_data)


def render_dictionary_stats(df: pd.DataFrame) -> None:
    """Render dictionary statistics (optimized - cache unique counts)."""
    # Cache stats computation to avoid recalculating on every render
    stats_cache_key = f'vocab_stats_{len(df)}'
    if stats_cache_key not in st.session_state:
        stats = {
            'total': len(df),
            'levels': df['level'].nunique() if not df.empty else 0,
            'topics': df['topic'].nunique() if not df.empty else 0,
            'types': df['type'].nunique() if not df.empty else 0
        }
        st.session_state[stats_cache_key] = stats
    else:
        stats = st.session_state[stats_cache_key]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📖 Tổng số từ", stats['total'])
    
    if stats['total'] > 0:
        c2.metric("🎯 Cấp độ", f"{stats['levels']} levels")
        c3.metric("📑 Chủ đề", f"{stats['topics']} topics")
        c4.metric("🔤 Loại từ", f"{stats['types']} types")


def render_dictionary_filters(topics: List[str], levels: List[str]) -> tuple:
    """Render advanced search and filter controls.
    
    Returns:
        Tuple of (search_term, level_filter, topic_filter, word_type_filter)
    """
    st.markdown("### 🔍 Tìm Kiếm & Lọc")
    
    # Row 1: Search
    search_term = st.text_input(
        "Tìm từ vựng",
        placeholder="Nhập từ tiếng Anh hoặc nghĩa tiếng Việt...",
        help="Tìm kiếm trong cả từ tiếng Anh và nghĩa tiếng Việt"
    )
    
    # Row 2: Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        level_filter = st.multiselect(
            "Cấp độ",
            options=levels,
            default=[],
            help="Chọn một hoặc nhiều cấp độ"
        )
    
    with col2:
        topic_filter = st.multiselect(
            "Chủ đề",
            options=topics,
            default=[],
            help="Chọn một hoặc nhiều chủ đề"
        )
    
    with col3:
        # Get unique word types from current data (will be filtered later)
        word_type_filter = st.text_input(
            "Loại từ",
            placeholder="noun, verb, adjective...",
            help="Nhập loại từ để lọc"
        )
    
    return search_term, level_filter, topic_filter, word_type_filter


def apply_dictionary_filters(
    df: pd.DataFrame, 
    search_term: str, 
    level_filter: List[str], 
    topic_filter: List[str],
    word_type_filter: str
) -> pd.DataFrame:
    """Apply all filters to dictionary DataFrame.
    
    Args:
        df: Vocabulary DataFrame
        search_term: Search keyword
        level_filter: List of selected levels
        topic_filter: List of selected topics
        word_type_filter: Word type filter
        
    Returns:
        Filtered DataFrame
    """
    # Level filter
    if level_filter:
        df = df[df['level'].isin(level_filter)]
    
    # Topic filter
    if topic_filter:
        df = df[df['topic'].isin(topic_filter)]
    
    # Word type filter
    if word_type_filter:
        df = df[df['type'].str.contains(word_type_filter, case=False, na=False)]
    
    # Search filter (search in both word and meaning)
    if search_term:
        mask = (
            df['word'].str.contains(search_term, case=False, na=False) |
            df['meaning'].str.contains(search_term, case=False, na=False)
        )
        df = df[mask]
    
    return df


def render_word_detail_card(word_data: Dict[str, Any], index: int) -> None:
    """Render detailed word card with all information.
    
    Args:
        word_data: Dictionary containing word information
        index: Index for unique keys
    """
    with st.container(border=True):
        # Word and pronunciation
        col_word, col_audio = st.columns([5, 1])
        
        with col_word:
            pronunciation = word_data.get('pronunciation', '')
            if pronunciation:
                st.markdown(f"### {word_data['word']} `{pronunciation}`")
            else:
                st.markdown(f"### {word_data['word']}")
            
            # Word type and level
            badges = f"**{word_data.get('type', 'N/A')}** • Level: **{word_data.get('level', 'N/A')}**"
            if word_data.get('topic'):
                badges += f" • Topic: **{word_data['topic']}**"
            st.caption(badges)
        
        with col_audio:
            # Audio button - TTS is already cached, so rerun is fast
            if st.button("🔊", key=f"audio_{index}_{word_data.get('id', index)}", help="Phát âm"):
                # TTS uses cache internally, so this is fast
                audio_bytes = get_tts_audio(word_data['word'])
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/mp3', autoplay=True)
        
        # Meaning
        st.markdown(f"**Nghĩa:** *{word_data['meaning']}*")
        
        # Example
        example = word_data.get('example', '')
        example_translation = word_data.get('example_translation', '')
        
        if example and example.strip():
            with st.expander("📖 Xem ví dụ"):
                st.markdown(f"**EN:** {example}")
                if example_translation and example_translation.strip():
                    st.markdown(f"**VI:** {example_translation}")
        
        # Additional details
        collocations = word_data.get('collocations')
        phrasal_verbs = word_data.get('phrasal_verbs')
        word_forms = word_data.get('word_forms')
        synonyms = word_data.get('synonyms')
        usage_notes = word_data.get('usage_notes')
        
        has_details = bool(collocations or phrasal_verbs or word_forms or synonyms or usage_notes)
        if has_details:
            with st.expander("📚 Chi tiết từ vựng", expanded=False):
                # Collocations
                if collocations and isinstance(collocations, list) and len(collocations) > 0:
                    st.markdown("**🔗 Từ đi kèm:**")
                    for colloc in collocations[:5]:
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
                        forms_list.append(f"**Danh từ:** {word_forms['noun']}")
                    if word_forms.get('verb'):
                        forms_list.append(f"**Động từ:** {word_forms['verb']}")
                    if word_forms.get('adjective'):
                        forms_list.append(f"**Tính từ:** {word_forms['adjective']}")
                    if word_forms.get('adverb'):
                        forms_list.append(f"**Trạng từ:** {word_forms['adverb']}")
                    
                    if forms_list:
                        st.markdown("**🔤 Dạng từ:**")
                        for form in forms_list:
                            st.markdown(f"- {form}")
                        st.markdown("")  # Spacing
                
                # Synonyms
                if synonyms and isinstance(synonyms, list) and len(synonyms) > 0:
                    syns_text = ", ".join(synonyms[:5])
                    st.markdown(f"**🔀 Từ đồng nghĩa:** *{syns_text}*")
                    st.markdown("")  # Spacing
                
                # Usage Notes
                if usage_notes and usage_notes.strip():
                    from core.translator import translate_usage_notes
                    translated_notes = translate_usage_notes(usage_notes)
                    st.markdown("**💡 Ghi chú cách dùng:**")
                    st.info(translated_notes)
        
        # Action button - process click and show result
        vocab_id = word_data.get('id', index)
        button_key = f"add_{index}_{vocab_id}"
        button_state_key = f"button_state_{vocab_id}"
        
        # Initialize button state if not exists
        if button_state_key not in st.session_state:
            st.session_state[button_state_key] = None
        
        # Show success/warning message if button was previously clicked
        if st.session_state[button_state_key] == 'success':
            st.success("✅ Đã thêm vào danh sách học!")
        elif st.session_state[button_state_key] == 'warning':
            st.warning("⚠️ Từ này đã có trong danh sách học của bạn.")
        
        # Button click handler - process immediately when clicked
        if st.button("➕ Thêm vào học", key=button_key):
            from services.vocab_service import add_word_to_srs
            uid = st.session_state.user_info['id']
            success = add_word_to_srs(uid, vocab_id)
            if success:
                st.session_state[button_state_key] = 'success'
                st.success("✅ Đã thêm vào danh sách học!")
            else:
                st.session_state[button_state_key] = 'warning'
                st.warning("⚠️ Từ này đã có trong danh sách học của bạn.")
            # Rerun is necessary to show the message, but all data is cached so it's fast
            st.rerun()


def render_dictionary_grid(df: pd.DataFrame, page_size: int = 12) -> None:
    """Render dictionary as a grid of word cards with pagination.
    
    Args:
        df: Filtered DataFrame
        page_size: Number of words per page
    """
    if df.empty:
        st.info("🔍 Không tìm thấy từ vựng nào phù hợp với bộ lọc.")
        return
    
    # Pagination - use session_state to persist page number
    # Use a stable key based on filter state to reset page when filters change
    filter_hash = hash((tuple(df.index[:10]) if len(df) > 0 else ()))
    pagination_key = f'dict_page_{filter_hash}'
    
    if pagination_key not in st.session_state:
        st.session_state[pagination_key] = 1
    
    total_pages = (len(df) - 1) // page_size + 1 if len(df) > 0 else 1
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Use selectbox instead of number_input for better performance
            page_options = list(range(1, total_pages + 1))
            page = st.selectbox(
                f"Trang (1-{total_pages})",
                options=page_options,
                index=st.session_state[pagination_key] - 1 if st.session_state[pagination_key] <= total_pages else 0,
                key=f"dict_page_select_{filter_hash}"
            )
            st.session_state[pagination_key] = page
    else:
        page = 1
        st.session_state[pagination_key] = 1
    
    # Calculate slice
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_df = df.iloc[start_idx:end_idx]
    
    # Display count
    st.caption(f"Hiển thị {start_idx + 1}-{min(end_idx, len(df))} trong tổng số {len(df)} từ")
    
    # Render grid (3 columns) - only render current page
    cols = st.columns(3)
    for i, (_, row) in enumerate(page_df.iterrows()):
        col = cols[i % 3]
        with col:
            render_word_detail_card(row.to_dict(), start_idx + i)


def render_dictionary_table_view(df: pd.DataFrame) -> None:
    """Render dictionary as a compact table view.
    
    Args:
        df: Filtered DataFrame
    """
    if df.empty:
        st.info("🔍 Không tìm thấy từ vựng nào phù hợp với bộ lọc.")
        return
    
    st.caption(f"Tìm thấy {len(df)} từ")
    
    # Display table
    display_df = df[['word', 'pronunciation', 'meaning', 'type', 'level', 'topic']].copy()
    display_df.columns = ['Từ', 'Phiên âm', 'Nghĩa', 'Loại', 'Cấp độ', 'Chủ đề']
    
    st.dataframe(
        display_df,
        hide_index=True,
        height=600,
        width='stretch'
    )


def render_quick_reference(df: pd.DataFrame) -> None:
    """Render quick reference section with statistics by category.
    
    Args:
        df: Full vocabulary DataFrame
    """
    with st.expander("📊 Thống kê chi tiết", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Theo Cấp Độ", "Theo Chủ Đề", "Theo Loại Từ"])
        
        with tab1:
            if not df.empty:
                level_counts = df['level'].value_counts().sort_index()
                st.bar_chart(level_counts)
                for level, count in level_counts.items():
                    st.write(f"**{level}**: {count} từ")
        
        with tab2:
            if not df.empty:
                topic_counts = df['topic'].value_counts().head(10)
                st.bar_chart(topic_counts)
                st.caption("Top 10 chủ đề")
        
        with tab3:
            if not df.empty:
                type_counts = df['type'].value_counts().head(10)
                st.bar_chart(type_counts)
                st.caption("Top 10 loại từ")


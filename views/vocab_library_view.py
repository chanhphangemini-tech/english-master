"""View components for Vocabulary Library page."""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging

from core.vocab_utils import normalize_meaning, get_vietnamese_meaning, format_pronunciation

logger = logging.getLogger(__name__)


def transform_progress_to_dataframe(progress_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Transform progress data to DataFrame format.
    
    Args:
        progress_data: Raw progress data from database
        
    Returns:
        DataFrame with flattened vocabulary data
    """
    flattened_data = []
    for item in progress_data:
        vocab = item.get('Vocabulary') or {}
        raw_meaning = vocab.get('meaning') or {}
        meaning_json = normalize_meaning(raw_meaning)
        
        flattened_data.append({
            "Word": vocab.get('word'),
            "Meaning": meaning_json.get('vietnamese', 'N/A'),
            "Level": vocab.get('level'),
            "Status": item.get('status'),
            "Streak": item.get('streak'),
            "Next Review": item.get('due_date'),
            "vocab_id": item.get('vocab_id')
        })
    
    return pd.DataFrame(flattened_data)


def render_vocab_stats(df: pd.DataFrame) -> None:
    """Render vocabulary statistics."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số từ", len(df))
    c2.metric("Đang học (Learning)", len(df[df['Status'] == 'learning']))
    c3.metric("Đã thuộc (Mastered)", len(df[df['Status'] == 'mastered']))


def render_vocab_filters() -> tuple:
    """Render search and filter controls.
    
    Returns:
        Tuple of (search_term, status_filter)
    """
    col_search, col_filter = st.columns([2, 1])
    search_term = col_search.text_input(
        "🔍 Tìm kiếm từ vựng...", 
        placeholder="Nhập từ tiếng Anh..."
    )
    status_filter = col_filter.selectbox(
        "Trạng thái", 
        ["Tất cả", "Learning", "Review", "Mastered"]
    )
    return search_term, status_filter


def apply_filters(df: pd.DataFrame, search_term: str, status_filter: str) -> pd.DataFrame:
    """Apply search and status filters to DataFrame.
    
    Args:
        df: Vocabulary DataFrame
        search_term: Search keyword
        status_filter: Status filter selection
        
    Returns:
        Filtered DataFrame
    """
    if status_filter != "Tất cả":
        df = df[df['Status'] == status_filter.lower()]
    
    if search_term:
        df = df[df['Word'].str.contains(search_term, case=False, na=False)]
    
    return df


def render_vocab_table(df: pd.DataFrame) -> None:
    """Render vocabulary data table.
    
    Args:
        df: Vocabulary DataFrame to display
    """
    st.dataframe(
        df[['Word', 'Meaning', 'Level', 'Status', 'Streak', 'Next Review']],
        width='stretch',
        hide_index=True,
        column_config={
            "Next Review": st.column_config.DatetimeColumn(
                "Ôn tập tiếp theo", 
                format="D/M/YYYY HH:mm"
            ),
            "Streak": st.column_config.ProgressColumn(
                "Độ nhớ", 
                min_value=0, 
                max_value=10, 
                format="%d"
            ),
            "Status": st.column_config.TextColumn(
                "Trạng thái", 
                help="Learning: Đang học, Review: Cần ôn, Mastered: Đã thuộc"
            )
        }
    )


def render_empty_state() -> None:
    """Render empty state when no vocabulary exists."""
    st.info("Bạn chưa học từ vựng nào. Hãy vào mục 'Học & Ôn Tập' để bắt đầu nhé!")
    if st.button("🚀 Bắt đầu học ngay"):
        st.switch_page("pages/06_On_Tap.py")


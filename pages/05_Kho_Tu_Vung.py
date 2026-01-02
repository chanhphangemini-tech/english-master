import streamlit as st
from typing import Dict, Any
import pandas as pd

from core.theme_applier import apply_page_theme
from core.vocab_preloader import (
    get_preloaded_vocabulary, 
    get_preloaded_topics, 
    get_preloaded_levels,
    preload_vocabulary_data
)
from views.dictionary_view import (
    transform_vocabulary_to_dataframe,
    render_dictionary_stats,
    render_dictionary_filters,
    apply_dictionary_filters,
    render_dictionary_grid,
    render_dictionary_table_view,
    render_quick_reference
)

st.set_page_config(page_title="Kho Từ Vựng | English Master", page_icon="📚", layout="wide")

if not st.session_state.get('logged_in'):
    st.switch_page("home.py")

apply_page_theme()  # Apply theme + sidebar + auth

# Page header
st.title("📚 Kho Từ Vựng - English Dictionary")
st.caption("Tra cứu và khám phá toàn bộ từ vựng từ A1 đến C2")

# Force reload if cache is stale (clear old cache if count is 1000)
if st.session_state.get('vocab_data_count', 0) == 1000:
    # Clear old cache from session_state
    from core.vocab_preloader import clear_preloaded_vocabulary
    clear_preloaded_vocabulary()
    # Also clear DataFrame cache
    if 'vocab_dataframe_cache' in st.session_state:
        del st.session_state['vocab_dataframe_cache']
    if 'vocab_data_count' in st.session_state:
        del st.session_state['vocab_data_count']
    if 'vocab_page_loaded' in st.session_state:
        del st.session_state['vocab_page_loaded']
    # Force reload by calling with force_reload=True
    preload_vocabulary_data(force_reload=True)
else:
    # Pre-load vocabulary data in background (non-blocking)
    preload_vocabulary_data()

# Get preloaded data (instant if already loaded, otherwise will trigger load)
vocab_data = get_preloaded_vocabulary()

# If data is still loading, show loading indicator
if not vocab_data and st.session_state.get('vocab_loading_in_progress', False):
    with st.spinner("Đang tải từ điển... (Lần đầu có thể mất vài giây)"):
        # Wait a bit for preload to complete
        import time
        time.sleep(0.5)
        vocab_data = get_preloaded_vocabulary()

if not vocab_data:
    # Fallback: try direct load
    from core.data import load_all_vocabulary
    with st.spinner("Đang tải từ điển..."):
        vocab_data = load_all_vocabulary()
    
    if not vocab_data:
        st.error("⚠️ Không thể tải dữ liệu từ vựng. Vui lòng thử lại sau.")
        st.stop()

# Cache DataFrame transformation in session_state
DF_CACHE_KEY = 'vocab_dataframe_cache'
if DF_CACHE_KEY not in st.session_state or len(vocab_data) != st.session_state.get('vocab_data_count', 0):
    df = transform_vocabulary_to_dataframe(vocab_data)
    st.session_state[DF_CACHE_KEY] = df
    st.session_state['vocab_data_count'] = len(vocab_data)
else:
    df = st.session_state[DF_CACHE_KEY]

# Show success message with count (only if not already shown)
if not st.session_state.get('vocab_page_loaded', False):
    st.success(f"✅ Đã tải thành công **{len(vocab_data):,}** từ vựng!")
    st.session_state['vocab_page_loaded'] = True

# Get filters data (preloaded)
topics = get_preloaded_topics()
levels = get_preloaded_levels()

# If topics/levels not loaded yet, get them
if not topics or not levels:
    from core.data import get_vocabulary_topics, get_vocabulary_levels
    if not topics:
        topics = get_vocabulary_topics()
    if not levels:
        levels = get_vocabulary_levels()

# Statistics (lazy load - only compute if needed)
with st.container():
    render_dictionary_stats(df)

st.divider()

# Filters
search_term, level_filter, topic_filter, word_type_filter = render_dictionary_filters(topics, levels)

# Apply filters (cache filtered result if filters haven't changed)
filter_cache_key = f'vocab_filtered_{hash((search_term, tuple(level_filter or []), tuple(topic_filter or []), word_type_filter))}'
if filter_cache_key not in st.session_state:
    df_filtered = apply_dictionary_filters(df, search_term, level_filter, topic_filter, word_type_filter)
    st.session_state[filter_cache_key] = df_filtered
else:
    df_filtered = st.session_state[filter_cache_key]

st.divider()

# View mode selection
view_mode = st.radio(
    "Chế độ hiển thị",
    options=["🎴 Card View (Chi tiết)", "📋 Table View (Danh sách)"],
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# Render based on view mode (only render current page)
if "Card" in view_mode:
    render_dictionary_grid(df_filtered, page_size=12)
else:
    render_dictionary_table_view(df_filtered)

# Quick reference (lazy load - in expander)
st.divider()
with st.expander("📊 Thống kê chi tiết", expanded=False):
    render_quick_reference(df)


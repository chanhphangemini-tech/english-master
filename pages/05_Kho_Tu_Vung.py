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

# Optimized vocabulary loading - only load/reload when necessary
# Check if we need to force reload (old cache with 1000 items)
needs_reload = st.session_state.get('vocab_data_count', 0) == 1000

if needs_reload:
    # Clear old cache from session_state
    from core.vocab_preloader import clear_preloaded_vocabulary
    clear_preloaded_vocabulary()
    # Also clear DataFrame cache and related state
    for key in ['vocab_dataframe_cache', 'vocab_data_count', 'vocab_page_loaded', 'last_filter_key']:
        if key in st.session_state:
            del st.session_state[key]
    # Clear filter cache
    for key in list(st.session_state.keys()):
        if key.startswith('vocab_filtered_'):
            del st.session_state[key]
    # Force reload
    preload_vocabulary_data(force_reload=True)
else:
    # Pre-load vocabulary data (only if not already loaded)
    preload_vocabulary_data()

# Get preloaded data (instant if already loaded)
vocab_data = get_preloaded_vocabulary()

# If data is still loading, show loading indicator (only once)
if not vocab_data and st.session_state.get('vocab_loading_in_progress', False):
    with st.spinner("Đang tải từ điển... (Lần đầu có thể mất vài giây)"):
        import time
        time.sleep(0.5)
        vocab_data = get_preloaded_vocabulary()

# Fallback: try direct load only if preload failed
if not vocab_data:
    from core.data import load_all_vocabulary
    with st.spinner("Đang tải từ điển..."):
        vocab_data = load_all_vocabulary()
    
    if not vocab_data:
        st.error("⚠️ Không thể tải dữ liệu từ vựng. Vui lòng thử lại sau.")
        st.stop()

# Cache DataFrame transformation in session_state (only transform if needed)
DF_CACHE_KEY = 'vocab_dataframe_cache'
VOCAB_COUNT_KEY = 'vocab_data_count'

# Only transform if cache is missing or data count changed
if DF_CACHE_KEY not in st.session_state or len(vocab_data) != st.session_state.get(VOCAB_COUNT_KEY, 0):
    df = transform_vocabulary_to_dataframe(vocab_data)
    st.session_state[DF_CACHE_KEY] = df
    st.session_state[VOCAB_COUNT_KEY] = len(vocab_data)
else:
    # Use cached DataFrame - this is the fast path
    df = st.session_state[DF_CACHE_KEY]

# Show success message with count (only once per session, not on every rerun)
if not st.session_state.get('vocab_page_loaded', False) and vocab_data:
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
# Use a more stable cache key based on filter values
filter_key_parts = (
    search_term or '',
    tuple(sorted(level_filter or [])),
    tuple(sorted(topic_filter or [])),
    word_type_filter or ''
)
filter_cache_key = f'vocab_filtered_{hash(filter_key_parts)}'

# Check if filters changed by comparing with last filter state
last_filter_key = st.session_state.get('last_filter_key')
if filter_cache_key != last_filter_key or filter_cache_key not in st.session_state:
    # Filters changed or cache miss - recalculate
    df_filtered = apply_dictionary_filters(df, search_term, level_filter, topic_filter, word_type_filter)
    st.session_state[filter_cache_key] = df_filtered
    st.session_state['last_filter_key'] = filter_cache_key
    # Reset pagination when filters change
    if 'dict_page' in st.session_state:
        # Clear all pagination states
        for key in list(st.session_state.keys()):
            if key.startswith('dict_page_'):
                del st.session_state[key]
else:
    # Use cached filtered result
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


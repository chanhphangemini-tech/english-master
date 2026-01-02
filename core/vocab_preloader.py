"""
Vocabulary pre-loader module để pre-load vocabulary data vào session_state.
Giúp tăng tốc độ load trang vocabulary bằng cách load data sớm.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
import logging
from services.vocab_service import load_all_vocabulary, get_vocabulary_topics, get_vocabulary_levels

logger = logging.getLogger(__name__)

# Cache keys
VOCAB_DATA_KEY = 'preloaded_vocab_data'
VOCAB_TOPICS_KEY = 'preloaded_vocab_topics'
VOCAB_LEVELS_KEY = 'preloaded_vocab_levels'
VOCAB_LOADING_KEY = 'vocab_loading_in_progress'
VOCAB_LOADED_KEY = 'vocab_data_loaded'

def preload_vocabulary_data(force_reload: bool = False) -> None:
    """
    Pre-load vocabulary data vào session_state.
    Chỉ load một lần, sau đó reuse từ cache.
    
    NOTE: This function is now called on-demand (lazy loading) rather than 
    blocking during login for better performance.
    
    Args:
        force_reload: Nếu True, force reload ngay cả khi đã có data
    """
    # Check if already loaded (but allow reload if count is 1000 - old cache)
    if not force_reload and st.session_state.get(VOCAB_LOADED_KEY, False):
        # Check if we have old cache (1000 items) - if so, force reload
        cached_data = st.session_state.get(VOCAB_DATA_KEY, [])
        if len(cached_data) == 1000:
            logger.info("Detected old cache (1000 items), forcing reload...")
            force_reload = True
            clear_preloaded_vocabulary()
        else:
            logger.debug("Vocabulary data already loaded, skipping preload")
            return
    
    # Check if loading is in progress
    if st.session_state.get(VOCAB_LOADING_KEY, False):
        logger.debug("Vocabulary loading already in progress, skipping")
        return
    
    try:
        st.session_state[VOCAB_LOADING_KEY] = True
        
        # Load vocabulary data (this will use @st.cache_data internally)
        logger.info("Pre-loading vocabulary data...")
        vocab_data = load_all_vocabulary()
        
        if vocab_data:
            st.session_state[VOCAB_DATA_KEY] = vocab_data
            st.session_state[VOCAB_LOADED_KEY] = True
            logger.info(f"Pre-loaded {len(vocab_data)} vocabulary items")
        
        # Load topics and levels (also cached)
        topics = get_vocabulary_topics()
        levels = get_vocabulary_levels()
        
        if topics:
            st.session_state[VOCAB_TOPICS_KEY] = topics
        if levels:
            st.session_state[VOCAB_LEVELS_KEY] = levels
            
    except Exception as e:
        logger.error(f"Error pre-loading vocabulary: {e}")
    finally:
        st.session_state[VOCAB_LOADING_KEY] = False

def get_preloaded_vocabulary() -> List[Dict[str, Any]]:
    """
    Lấy vocabulary data từ session_state.
    Nếu chưa có, sẽ trigger preload.
    
    Returns:
        List of vocabulary items
    """
    if VOCAB_DATA_KEY not in st.session_state:
        # Trigger preload if not already loading
        if not st.session_state.get(VOCAB_LOADING_KEY, False):
            preload_vocabulary_data()
        return []
    
    return st.session_state.get(VOCAB_DATA_KEY, [])

def get_preloaded_topics() -> List[str]:
    """Lấy topics từ session_state."""
    if VOCAB_TOPICS_KEY not in st.session_state:
        # Trigger preload if not already loading
        if not st.session_state.get(VOCAB_LOADING_KEY, False):
            preload_vocabulary_data()
        return []
    
    return st.session_state.get(VOCAB_TOPICS_KEY, [])

def get_preloaded_levels() -> List[str]:
    """Lấy levels từ session_state."""
    if VOCAB_LEVELS_KEY not in st.session_state:
        return ["A1", "A2", "B1", "B2", "C1", "C2"]
    
    return st.session_state.get(VOCAB_LEVELS_KEY, ["A1", "A2", "B1", "B2", "C1", "C2"])

def clear_preloaded_vocabulary():
    """Xóa preloaded vocabulary data (dùng khi logout)."""
    for key in [VOCAB_DATA_KEY, VOCAB_TOPICS_KEY, VOCAB_LEVELS_KEY, VOCAB_LOADING_KEY, VOCAB_LOADED_KEY]:
        if key in st.session_state:
            del st.session_state[key]
    logger.debug("Cleared preloaded vocabulary data")

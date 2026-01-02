"""
Data caching module để tối ưu performance khi navigate giữa các pages.
Cache data vào session_state để tránh reload mỗi lần chuyển page.
"""
import streamlit as st
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Cache TTLs (seconds)
CACHE_TTL = {
    'user_stats': 60,  # 1 minute - stats change frequently (increased from 30s for better performance)
    'user_info': 600,  # 10 minutes - user info rarely changes (increased from 5min)
    'vocabulary': 7200,  # 2 hours - vocabulary changes infrequently (increased from 1h)
    'inventory': 300,  # 5 minutes - inventory changes when user buys items
    'level_progress': 120,  # 2 minutes - progress changes when user learns (increased from 1min)
    'leaderboard': 300,  # 5 minutes - leaderboard updates periodically
    'quests': 60,  # 1 minute - quests update daily
    'theme': 600,  # 10 minutes - theme rarely changes
}

def get_cached_data(
    cache_key: str,
    loader_func: Callable,
    *args,
    ttl: Optional[int] = None,
    **kwargs
) -> Any:
    """
    Lấy data từ cache hoặc load mới nếu cache expired.
    
    Args:
        cache_key: Key để lưu trong session_state (format: 'cache_{type}_{id}')
        loader_func: Function để load data nếu cache miss
        ttl: Time to live (seconds), nếu None thì dùng CACHE_TTL
        *args, **kwargs: Arguments để pass vào loader_func
    
    Returns:
        Cached data hoặc newly loaded data
    """
    if ttl is None:
        # Extract cache type from key (format: 'cache_{type}_{id}')
        cache_type = cache_key.split('_')[1] if '_' in cache_key else 'default'
        ttl = CACHE_TTL.get(cache_type, 60)
    
    # Check if data exists in cache and is still valid
    cache_entry_key = f"{cache_key}_entry"
    timestamp_key = f"{cache_key}_timestamp"
    
    if cache_entry_key in st.session_state:
        cache_timestamp = st.session_state.get(timestamp_key, 0)
        elapsed = (datetime.now().timestamp() - cache_timestamp)
        
        if elapsed < ttl:
            # Cache hit - return cached data
            logger.debug(f"Cache hit for {cache_key} (elapsed: {elapsed:.1f}s < {ttl}s)")
            return st.session_state[cache_entry_key]
        else:
            # Cache expired - clear it
            logger.debug(f"Cache expired for {cache_key} (elapsed: {elapsed:.1f}s >= {ttl}s)")
            del st.session_state[cache_entry_key]
            if timestamp_key in st.session_state:
                del st.session_state[timestamp_key]
    
    # Cache miss - load new data
    try:
        logger.debug(f"Cache miss for {cache_key}, loading new data...")
        data = loader_func(*args, **kwargs)
        
        # Store in cache
        st.session_state[cache_entry_key] = data
        st.session_state[timestamp_key] = datetime.now().timestamp()
        
        return data
    except Exception as e:
        logger.error(f"Error loading data for {cache_key}: {e}")
        # Return cached data even if expired if load fails
        if cache_entry_key in st.session_state:
            logger.warning(f"Using expired cache for {cache_key} due to load error")
            return st.session_state[cache_entry_key]
        raise

def invalidate_cache(cache_key: str):
    """Xóa cache entry."""
    cache_entry_key = f"{cache_key}_entry"
    timestamp_key = f"{cache_key}_timestamp"
    
    if cache_entry_key in st.session_state:
        del st.session_state[cache_entry_key]
    if timestamp_key in st.session_state:
        del st.session_state[timestamp_key]
    
    logger.debug(f"Cache invalidated for {cache_key}")

def clear_all_caches():
    """Xóa tất cả caches (dùng khi logout)."""
    keys_to_remove = [
        key for key in st.session_state.keys()
        if key.startswith('cache_') and (key.endswith('_entry') or key.endswith('_timestamp'))
    ]
    
    # Also clear sidebar stats cache, vocabulary preload, and feature flags cache
    keys_to_remove.extend([
        key for key in st.session_state.keys()
        if key.startswith('sidebar_stats_') or key.startswith('preloaded_vocab') or key.startswith('vocab_') or key.startswith('feature_flags')
    ])
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    # Also clear feature flags cache using the service function
    try:
        from services.feature_flag_service import clear_feature_flags_cache
        clear_feature_flags_cache()
    except Exception:
        pass  # Ignore errors during cleanup
    
    logger.info(f"Cleared {len(keys_to_remove)} cache entries")

# Convenience functions for common data types
def get_cached_user_stats(user_id: int):
    """Get cached user stats."""
    from services.user_service import get_user_stats
    
    return get_cached_data(
        f"cache_user_stats_{user_id}",
        get_user_stats,
        user_id,  # Pass as positional argument
        ttl=CACHE_TTL['user_stats']
    )

def get_cached_user_info(user_id: int):
    """Get cached user info."""
    from core.database import supabase
    
    def load_user_info(user_id):
        if not supabase:
            return {}
        try:
            res = supabase.table("Users").select("*").eq("id", int(user_id)).single().execute()
            return res.data if res.data else {}
        except Exception as e:
            logger.error(f"Error loading user info: {e}")
            return {}
    
    return get_cached_data(
        f"cache_user_info_{user_id}",
        load_user_info,
        user_id,  # Pass as positional argument
        ttl=CACHE_TTL['user_info']
    )

def get_cached_inventory(user_id: int):
    """Get cached user inventory."""
    from services.shop_service import get_user_inventory
    
    return get_cached_data(
        f"cache_inventory_{user_id}",
        get_user_inventory,
        user_id,  # Pass as positional argument
        ttl=CACHE_TTL['inventory']
    )

def get_cached_level_progress(user_id: int):
    """Get cached level progress."""
    from services.vocab_service import get_user_level_progress
    
    return get_cached_data(
        f"cache_level_progress_{user_id}",
        get_user_level_progress,
        user_id,  # Pass as positional argument
        ttl=CACHE_TTL['level_progress']
    )

def get_cached_vocabulary(level: Optional[str] = None):
    """Get cached vocabulary."""
    from services.vocab_service import load_vocab_data
    
    cache_key = f"cache_vocabulary_{level or 'all'}"
    return get_cached_data(
        cache_key,
        load_vocab_data,
        level,  # Pass as positional argument (can be None)
        ttl=CACHE_TTL['vocabulary']
    )

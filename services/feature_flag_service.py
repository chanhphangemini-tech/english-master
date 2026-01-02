"""Service for managing feature flags"""
import streamlit as st
from core.database import supabase
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Session state key for feature flags cache
FEATURE_FLAGS_CACHE_KEY = 'feature_flags_cache'
FEATURE_FLAGS_LOADED_KEY = 'feature_flags_loaded'

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def _load_all_feature_flags() -> Dict[str, Dict[str, Any]]:
    """Load all feature flags from database in one query.
    
    Returns:
        Dict mapping feature_key -> {is_enabled: bool, maintenance_message: str}
    """
    flags = {}
    try:
        if not supabase:
            return flags
        
        result = supabase.table("featureflags").select("feature_key, is_enabled, maintenance_message").execute()
        if result.data:
            for item in result.data:
                feature_key = item.get("feature_key")
                if feature_key:
                    flags[feature_key] = {
                        "is_enabled": item.get("is_enabled", True),
                        "maintenance_message": item.get("maintenance_message", "Tính năng đang được bảo trì")
                    }
        logger.debug(f"Loaded {len(flags)} feature flags from database")
    except Exception as e:
        logger.error(f"Error loading feature flags: {e}")
    
    return flags

def get_all_feature_flags() -> Dict[str, Dict[str, Any]]:
    """Get all feature flags, cached in session_state for faster access.
    
    Returns:
        Dict mapping feature_key -> {is_enabled: bool, maintenance_message: str}
    """
    # Check session_state first (fastest)
    if FEATURE_FLAGS_CACHE_KEY in st.session_state:
        return st.session_state[FEATURE_FLAGS_CACHE_KEY]
    
    # Load from database (uses @st.cache_data internally)
    flags = _load_all_feature_flags()
    
    # Cache in session_state for this session
    st.session_state[FEATURE_FLAGS_CACHE_KEY] = flags
    st.session_state[FEATURE_FLAGS_LOADED_KEY] = True
    
    return flags

def is_feature_enabled(feature_key: str) -> bool:
    """Check if a feature is enabled.
    
    Uses cached feature flags from session_state to avoid multiple queries.
    """
    try:
        flags = get_all_feature_flags()
        if feature_key in flags:
            return flags[feature_key].get("is_enabled", True)
        # Default to enabled if not found
        return True
    except Exception as e:
        logger.error(f"Error checking feature flag {feature_key}: {e}")
        return True  # Default to enabled on error

def get_feature_maintenance_message(feature_key: str) -> str:
    """Get maintenance message for a disabled feature.
    
    Uses cached feature flags from session_state to avoid multiple queries.
    """
    try:
        flags = get_all_feature_flags()
        if feature_key in flags:
            return flags[feature_key].get("maintenance_message", "Tính năng đang được bảo trì")
        return "Tính năng đang được bảo trì"
    except Exception as e:
        logger.error(f"Error getting maintenance message for {feature_key}: {e}")
        return "Tính năng đang được bảo trì"

def clear_feature_flags_cache():
    """Clear feature flags cache (useful for testing or forcing refresh)."""
    if FEATURE_FLAGS_CACHE_KEY in st.session_state:
        del st.session_state[FEATURE_FLAGS_CACHE_KEY]
    if FEATURE_FLAGS_LOADED_KEY in st.session_state:
        del st.session_state[FEATURE_FLAGS_LOADED_KEY]


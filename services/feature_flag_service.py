"""Service for managing feature flags"""
import streamlit as st
from core.database import supabase

@st.cache_data(ttl=60)  # Cache for 1 minute
def is_feature_enabled(feature_key: str) -> bool:
    """Check if a feature is enabled"""
    try:
        if not supabase:
            return True  # Default to enabled if DB unavailable
        
        result = supabase.table("featureflags").select("is_enabled").eq("feature_key", feature_key).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("is_enabled", True)
        return True  # Default to enabled if not found
    except Exception:
        return True  # Default to enabled on error

def get_feature_maintenance_message(feature_key: str) -> str:
    """Get maintenance message for a disabled feature"""
    try:
        if not supabase:
            return "Tính năng đang được bảo trì"
        
        result = supabase.table("featureflags").select("maintenance_message").eq("feature_key", feature_key).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("maintenance_message", "Tính năng đang được bảo trì")
        return "Tính năng đang được bảo trì"
    except Exception:
        return "Tính năng đang được bảo trì"


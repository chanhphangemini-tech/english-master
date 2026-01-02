"""
Translation utilities for converting English text to Vietnamese.
"""
import logging
from typing import Optional
import streamlit as st

logger = logging.getLogger(__name__)


def is_vietnamese_text(text: str) -> bool:
    """Check if text contains Vietnamese characters."""
    if not text:
        return False
    vietnamese_chars = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')
    return any(char in vietnamese_chars for char in text.lower())


@st.cache_data(ttl=86400)  # Cache for 24 hours
def _translate_text_cached(text: str, _cache_key: str) -> str:
    """
    Internal cached translation function.
    Uses @st.cache_data to cache translations across sessions.
    """
    if not text or not text.strip():
        return text
    
    try:
        from core.llm import generate_response_with_fallback
        
        prompt = f"""Dịch đoạn văn sau từ tiếng Anh sang tiếng Việt. 
Giữ nguyên ý nghĩa, dịch tự nhiên và dễ hiểu. Chỉ trả về bản dịch tiếng Việt, không giải thích thêm.

English:
{text}

Vietnamese:"""
        
        translated = generate_response_with_fallback(prompt, [text], feature_type='general')
        
        if translated and translated.strip():
            # Clean up response
            translated = translated.strip().strip('"').strip("'")
            return translated
        else:
            logger.warning(f"Translation failed, returning original text")
            return text
            
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return text  # Return original on error


def translate_usage_notes(usage_notes: Optional[str]) -> str:
    """
    Translate usage notes from English to Vietnamese.
    If text is already in Vietnamese, returns as-is.
    Uses caching to avoid repeated API calls.
    
    Args:
        usage_notes: Usage notes text (English or Vietnamese)
        
    Returns:
        Vietnamese translation (or original if already Vietnamese)
    """
    if not usage_notes or not usage_notes.strip():
        return usage_notes or ""
    
    # Check if already in Vietnamese
    if is_vietnamese_text(usage_notes):
        return usage_notes
    
    # Need to translate - use cached translation function
    # Use first 200 chars as cache key (unique enough for most cases)
    cache_key = usage_notes[:200] if len(usage_notes) > 200 else usage_notes
    return _translate_text_cached(usage_notes, _cache_key=cache_key)

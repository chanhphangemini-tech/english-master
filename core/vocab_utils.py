"""Vocabulary utilities for text normalization and processing."""
import re
import unicodedata
from typing import Dict, Any, Optional

def normalize_meaning_text(text: str) -> str:
    """
    Normalize Vietnamese text for comparison (remove extra spaces, convert to lowercase).
    This is used for comparing user input with correct answers in quiz.
    
    Args:
        text: Input text to normalize
    
    Returns:
        Normalized text (lowercase, stripped, single spaces)
    """
    if not text:
        return ""
    
    # Convert to lowercase and strip
    normalized = text.lower().strip()
    
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def normalize_meaning(meaning: Any) -> Dict[str, str]:
    """
    Normalize meaning dictionary from vocabulary data.
    Handles both dict and string formats.
    
    Args:
        meaning: Meaning data (dict or string)
    
    Returns:
        Dict with 'vietnamese' and 'english' keys
    """
    if isinstance(meaning, dict):
        return {
            'vietnamese': meaning.get('vietnamese', ''),
            'english': meaning.get('english', '')
        }
    elif isinstance(meaning, str):
        return {
            'vietnamese': meaning,
            'english': ''
        }
    else:
        return {
            'vietnamese': '',
            'english': ''
        }

def get_vietnamese_meaning(meaning: Any) -> str:
    """
    Extract Vietnamese meaning from meaning data.
    
    Args:
        meaning: Meaning data (dict or string)
    
    Returns:
        Vietnamese meaning string
    """
    if isinstance(meaning, dict):
        return meaning.get('vietnamese', '')
    elif isinstance(meaning, str):
        return meaning
    else:
        return ''

def format_pronunciation(pronunciation: Optional[str]) -> str:
    """
    Format pronunciation string for display.
    
    Args:
        pronunciation: Pronunciation string (e.g., "/həˈloʊ/")
    
    Returns:
        Formatted pronunciation string
    """
    if not pronunciation:
        return ''
    
    # Ensure pronunciation is wrapped in slashes if not already
    pronunciation = pronunciation.strip()
    if not pronunciation.startswith('/'):
        pronunciation = '/' + pronunciation
    if not pronunciation.endswith('/'):
        pronunciation = pronunciation + '/'
    
    return pronunciation

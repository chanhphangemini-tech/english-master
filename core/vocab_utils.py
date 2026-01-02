"""
Vocabulary Utilities - Shared helper functions for vocabulary processing

This module provides utility functions used across multiple views
to ensure consistency and reduce code duplication.

Author: AI Assistant  
Date: 2025-12-30
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def normalize_meaning(raw_meaning: Any) -> Dict[str, str]:
    """
    Normalize meaning field to dict format.
    
    Handles multiple input formats:
    - Dict: Return as-is
    - JSON string: Parse and return
    - Plain text: Wrap in {"vietnamese": text}
    - None/empty: Return default fallback
    
    Args:
        raw_meaning: Raw meaning value from database (dict, str, or None)
        
    Returns:
        Dict with at least {"vietnamese": "..."} key
        
    Examples:
        >>> normalize_meaning({"vietnamese": "xin chào"})
        {"vietnamese": "xin chào"}
        
        >>> normalize_meaning('{"vietnamese": "xin chào"}')
        {"vietnamese": "xin chào"}
        
        >>> normalize_meaning("xin chào")
        {"vietnamese": "xin chào"}
        
        >>> normalize_meaning(None)
        {"vietnamese": "Không có nghĩa"}
    """
    # Case 1: Already a dict
    if isinstance(raw_meaning, dict): 
        return raw_meaning
    
    # Case 2: String (could be JSON or plain text)
    if isinstance(raw_meaning, str):
        # Try parse as JSON first
        try: 
            parsed = json.loads(raw_meaning)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError: 
            pass
        except Exception as e:
            logger.warning(f"Unexpected error parsing meaning as JSON: {e}")
        
        # Treat as plain text Vietnamese meaning
        if raw_meaning.strip():
            return {"vietnamese": raw_meaning.strip()}
    
    # Case 3: None, empty, or unsupported type
    logger.debug(f"normalize_meaning received unsupported type: {type(raw_meaning)}")
    return {"vietnamese": "Không có nghĩa"}


def get_vietnamese_meaning(raw_meaning: Any, default: str = "Không có nghĩa") -> str:
    """
    Extract Vietnamese meaning string from raw meaning data.
    
    Args:
        raw_meaning: Raw meaning value from database
        default: Default value if no meaning found
        
    Returns:
        Vietnamese meaning string
        
    Example:
        >>> get_vietnamese_meaning({"vietnamese": "xin chào"})
        "xin chào"
        
        >>> get_vietnamese_meaning(None)
        "Không có nghĩa"
    """
    normalized = normalize_meaning(raw_meaning)
    return normalized.get("vietnamese", default)


def format_pronunciation(pronunciation: Optional[str]) -> str:
    """
    Format pronunciation for display.
    
    Args:
        pronunciation: Raw pronunciation string from database
        
    Returns:
        Formatted pronunciation or empty string if N/A
        
    Example:
        >>> format_pronunciation("/həˈloʊ/")
        "/həˈloʊ/"
        
        >>> format_pronunciation("N/A")
        ""
        
        >>> format_pronunciation(None)
        ""
    """
    if not pronunciation:
        return ""
    
    pronunciation = pronunciation.strip()
    
    # Filter out N/A or empty
    if pronunciation.upper() == "N/A" or not pronunciation:
        return ""
    
    return pronunciation


def should_display_pronunciation(pronunciation: Optional[str]) -> bool:
    """
    Check if pronunciation should be displayed.
    
    Args:
        pronunciation: Pronunciation string
        
    Returns:
        True if pronunciation should be shown, False otherwise
    """
    formatted = format_pronunciation(pronunciation)
    return bool(formatted)


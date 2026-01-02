"""
Topic Service - Helper functions để hiển thị topics bằng tiếng Việt trong UI
"""
from services.exercise_cache_service import VALID_TOPICS, get_topic_display_name

def get_vietnamese_topics():
    """
    Lấy danh sách topics với Vietnamese display names cho UI.
    
    Returns:
        List of tuples: [(english_name, vietnamese_name), ...]
    """
    return [(topic, get_topic_display_name(topic)) for topic in VALID_TOPICS]

def get_vietnamese_topic_options():
    """
    Lấy danh sách Vietnamese names cho selectbox.
    
    Returns:
        List of Vietnamese names (sorted)
    """
    return sorted([get_topic_display_name(topic) for topic in VALID_TOPICS])

def get_english_topic_from_vietnamese(vietnamese_name):
    """
    Convert Vietnamese display name về English topic name (để lưu vào DB).
    
    Args:
        vietnamese_name: Vietnamese display name
    
    Returns:
        English topic name hoặc None nếu không tìm thấy
    """
    # Reverse lookup
    for english_topic in VALID_TOPICS:
        if get_topic_display_name(english_topic) == vietnamese_name:
            return english_topic
    return None

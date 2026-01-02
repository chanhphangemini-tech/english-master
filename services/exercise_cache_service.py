"""
Exercise Cache Service
Service để cache và quản lý bài tập AI-generated
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from core.database import supabase
from core.timezone_utils import get_vn_now_utc, VN_TIMEZONE
import random

logger = logging.getLogger(__name__)

# Predefined topic list (English names for database storage)
# UI sẽ hiển thị Vietnamese names từ TOPIC_DISPLAY_MAPPING
VALID_TOPICS = [
    # Daily Life (10)
    "Daily Life", "Family", "Friends", "Housing", "Food & Cooking",
    "Shopping", "Fashion", "Health", "Sports & Fitness", "Hobbies",
    # Education & Work (10)
    "Education", "School", "Work", "Career", "Business",
    "Skills", "Study Abroad", "Exams", "Projects", "Achievements",
    # Travel & Culture (10)
    "Travel", "Destinations", "Transportation", "Hotels", "Culture",
    "Festivals", "Traditions", "History", "Art", "Music",
    # Technology & Science (10)
    "Technology", "Internet", "Mobile Phones", "Computers", "Science",
    "Nature", "Environment", "Climate", "Medicine", "Research",
    # Entertainment & Media (10)
    "Movies", "Books", "Games", "TV", "News",
    "Social Media", "Blogs", "Podcasts", "Radio", "Journalism",
    # Society & Relationships (10)
    "Love", "Dating", "Marriage", "Children", "Elderly",
    "Community", "Volunteering", "Helping", "Friendship", "Relationships",
    # Finance & Economy (5)
    "Money", "Banking", "Investment", "Savings", "Trade",
    # Others (5)
    "Weather", "Animals", "Plants", "Exploration", "Random"
]

# Mapping từ English (database) sang Vietnamese (display)
TOPIC_DISPLAY_MAPPING = {
    # Daily Life
    "Daily Life": "Cuộc sống hàng ngày",
    "Family": "Gia đình",
    "Friends": "Bạn bè",
    "Housing": "Nhà ở",
    "Food & Cooking": "Đồ ăn và nấu ăn",
    "Shopping": "Mua sắm",
    "Fashion": "Thời trang",
    "Health": "Sức khỏe",
    "Sports & Fitness": "Thể thao và tập luyện",
    "Hobbies": "Sở thích",
    # Education & Work
    "Education": "Học tập",
    "School": "Trường học",
    "Work": "Công việc",
    "Career": "Nghề nghiệp",
    "Business": "Kinh doanh",
    "Skills": "Kỹ năng",
    "Study Abroad": "Du học",
    "Exams": "Thi cử",
    "Projects": "Dự án",
    "Achievements": "Thành tựu",
    # Travel & Culture
    "Travel": "Du lịch",
    "Destinations": "Điểm đến",
    "Transportation": "Phương tiện đi lại",
    "Hotels": "Khách sạn",
    "Culture": "Văn hóa",
    "Festivals": "Lễ hội",
    "Traditions": "Truyền thống",
    "History": "Lịch sử",
    "Art": "Nghệ thuật",
    "Music": "Âm nhạc",
    # Technology & Science
    "Technology": "Công nghệ",
    "Internet": "Internet",
    "Mobile Phones": "Điện thoại",
    "Computers": "Máy tính",
    "Science": "Khoa học",
    "Nature": "Thiên nhiên",
    "Environment": "Môi trường",
    "Climate": "Khí hậu",
    "Medicine": "Y học",
    "Research": "Nghiên cứu",
    # Entertainment & Media
    "Movies": "Phim ảnh",
    "Books": "Sách",
    "Games": "Trò chơi",
    "TV": "Truyền hình",
    "News": "Tin tức",
    "Social Media": "Mạng xã hội",
    "Blogs": "Blog",
    "Podcasts": "Podcast",
    "Radio": "Radio",
    "Journalism": "Báo chí",
    # Society & Relationships
    "Love": "Tình yêu",
    "Dating": "Hẹn hò",
    "Marriage": "Hôn nhân",
    "Children": "Trẻ em",
    "Elderly": "Người cao tuổi",
    "Community": "Cộng đồng",
    "Volunteering": "Tình nguyện",
    "Helping": "Giúp đỡ",
    "Friendship": "Tình bạn",
    "Relationships": "Mối quan hệ",
    # Finance & Economy
    "Money": "Tiền bạc",
    "Banking": "Ngân hàng",
    "Investment": "Đầu tư",
    "Savings": "Tiết kiệm",
    "Trade": "Mua bán",
    # Others
    "Weather": "Thời tiết",
    "Animals": "Động vật",
    "Plants": "Thực vật",
    "Exploration": "Khám phá",
    "Random": "Ngẫu nhiên",
}

def get_topic_display_name(english_topic):
    """Lấy Vietnamese display name từ English topic."""
    return TOPIC_DISPLAY_MAPPING.get(english_topic, english_topic)

def get_unseen_exercise(
    user_id: int,
    exercise_type: str,
    level: str,
    topic: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Lấy 1 bài tập chưa thấy từ cache, hoặc None nếu user đã thấy hết.
    
    Logic: 
    - Loại bỏ bài tập đã completed=TRUE (đã hoàn thành)
    - Loại bỏ bài tập completed=FALSE nhưng seen_at < 1 ngày (mới thấy gần đây, tránh học vẹt)
    - Cho phép bài tập completed=FALSE và seen_at >= 1 ngày (đã thấy lâu, có thể làm lại)
    
    Args:
        user_id: User ID
        exercise_type: 'dictation', 'comprehension', 'grammar_question', 'reading_question', 'podcast_script'
        level: 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'
        topic: Topic name (must be from VALID_TOPICS) hoặc None
    
    Returns:
        Dict với keys: 'id', 'exercise_data', 'metadata' hoặc None
    """
    if not supabase or not user_id or not exercise_type or not level:
        return None
    
    try:
        # Build query: Get exercises matching type, level, topic
        query = supabase.table("AIExercises").select(
            "id, exercise_data, metadata, usage_count"
        ).eq("exercise_type", exercise_type).eq("level", level)
        
        # Topic filter: exact match or NULL
        if topic and topic in VALID_TOPICS:
            query = query.eq("topic", topic)
        elif topic is None:
            query = query.is_("topic", "null")
        else:
            # Invalid topic, fallback to NULL
            query = query.is_("topic", "null")
        
        # Calculate 1 day ago in UTC (for comparison with seen_at)
        one_day_ago = (datetime.now(VN_TIMEZONE) - timedelta(days=1)).astimezone(timezone.utc).isoformat()
        
        # Exclude exercises user should not see again:
        # 1. Completed exercises (completed=TRUE)
        # 2. Incomplete exercises seen within last 24 hours (completed=FALSE AND seen_at >= one_day_ago)
        # This prevents users from "memorizing" exercises by repeating them too quickly
        
        # Get exercise_ids to exclude
        history_query = supabase.table("UserExerciseHistory").select("exercise_id, completed, seen_at").eq("user_id", user_id)
        history_result = history_query.execute()
        
        exclude_ids = []
        if history_result.data:
            for record in history_result.data:
                exercise_id = record.get('exercise_id')
                completed = record.get('completed', False)
                seen_at = record.get('seen_at')
                
                # Always exclude completed exercises
                if completed:
                    exclude_ids.append(exercise_id)
                # Exclude incomplete exercises seen within last 24 hours
                elif seen_at and seen_at >= one_day_ago:
                    exclude_ids.append(exercise_id)
        
        if exclude_ids:
            query = query.not_.in_("id", exclude_ids)
        
        # Get all matching exercises
        result = query.execute()
        
        if result.data and len(result.data) > 0:
            # Random select 1 exercise
            exercise = random.choice(result.data)
            
            # Update usage_count
            try:
                supabase.table("AIExercises").update({
                    "usage_count": (exercise.get('usage_count', 0) + 1),
                    "updated_at": get_vn_now_utc()
                }).eq("id", exercise['id']).execute()
            except Exception as e:
                logger.warning(f"Failed to update usage_count: {e}")
            
            return {
                'id': exercise['id'],
                'exercise_data': exercise['exercise_data'],
                'metadata': exercise.get('metadata', {})
            }
        
        # No unseen exercises found
        return None
        
    except Exception as e:
        logger.error(f"Error getting unseen exercise: {e}")
        return None

def save_exercise(
    exercise_type: str,
    level: str,
    topic: Optional[str],
    exercise_data: Dict[str, Any],
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Lưu bài tập mới vào database.
    
    Args:
        exercise_type: 'dictation', 'comprehension', etc.
        level: 'A1', 'A2', etc.
        topic: Topic name (must be from VALID_TOPICS) hoặc None
        exercise_data: Nội dung bài tập (JSON structure)
        user_id: User tạo bài tập này (optional)
        metadata: Thông tin thêm (optional)
    
    Returns:
        exercise_id nếu thành công, None nếu fail
    """
    if not supabase or not exercise_type or not level or not exercise_data:
        return None
    
    try:
        # Validate topic
        if topic and topic not in VALID_TOPICS:
            logger.warning(f"Invalid topic '{topic}', setting to None")
            topic = None
        
        # Prepare data
        data = {
            "exercise_type": exercise_type,
            "level": level,
            "topic": topic,
            "exercise_data": exercise_data,
            "metadata": metadata or {},
            "usage_count": 0,
            "created_at": get_vn_now_utc(),
            "updated_at": get_vn_now_utc()
        }
        
        if user_id:
            data["created_by_user_id"] = user_id
        
        # Insert
        result = supabase.table("AIExercises").insert(data).execute()
        
        if result.data and len(result.data) > 0:
            exercise_id = result.data[0]['id']
            logger.debug(f"Saved exercise {exercise_id} (type={exercise_type}, level={level}, topic={topic})")
            return exercise_id
        
        return None
        
    except Exception as e:
        logger.error(f"Error saving exercise: {e}")
        return None

def mark_exercise_seen(user_id: int, exercise_id: int) -> bool:
    """
    Đánh dấu user đã thấy bài tập này.
    
    Args:
        user_id: User ID
        exercise_id: Exercise ID
    
    Returns:
        True nếu thành công
    """
    if not supabase or not user_id or not exercise_id:
        return False
    
    try:
        # Upsert (insert or update if exists)
        supabase.table("UserExerciseHistory").upsert({
            "user_id": user_id,
            "exercise_id": exercise_id,
            "seen_at": get_vn_now_utc(),
            "completed": False
        }, on_conflict="user_id,exercise_id").execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Error marking exercise as seen: {e}")
        return False

def mark_exercise_completed(user_id: int, exercise_id: int, score: Optional[int] = None) -> bool:
    """
    Đánh dấu user đã hoàn thành bài tập này.
    
    Args:
        user_id: User ID
        exercise_id: Exercise ID
        score: Điểm (0-100, optional)
    
    Returns:
        True nếu thành công
    """
    if not supabase or not user_id or not exercise_id:
        return False
    
    try:
        # Update existing record or insert new
        data = {
            "user_id": user_id,
            "exercise_id": exercise_id,
            "completed": True
        }
        
        if score is not None:
            data["score"] = max(0, min(100, score))  # Clamp to 0-100
        
        supabase.table("UserExerciseHistory").upsert(
            data,
            on_conflict="user_id,exercise_id"
        ).execute()
        
        return True
        
    except Exception as e:
        logger.error(f"Error marking exercise as completed: {e}")
        return False

def get_exercise_stats(exercise_id: int) -> Optional[Dict[str, Any]]:
    """
    Lấy thống kê của 1 bài tập (usage_count, số user đã thấy, etc.)
    
    Args:
        exercise_id: Exercise ID
    
    Returns:
        Dict với stats hoặc None
    """
    if not supabase or not exercise_id:
        return None
    
    try:
        # Get exercise
        exercise = supabase.table("AIExercises").select("usage_count").eq("id", exercise_id).single().execute()
        
        if not exercise.data:
            return None
        
        # Count users who have seen this exercise
        history = supabase.table("UserExerciseHistory").select("id", count="exact").eq("exercise_id", exercise_id).execute()
        seen_count = history.count if hasattr(history, 'count') else 0
        
        # Count users who completed this exercise
        completed = supabase.table("UserExerciseHistory").select("id", count="exact").eq("exercise_id", exercise_id).eq("completed", True).execute()
        completed_count = completed.count if hasattr(completed, 'count') else 0
        
        return {
            "usage_count": exercise.data.get('usage_count', 0),
            "seen_count": seen_count,
            "completed_count": completed_count
        }
        
    except Exception as e:
        logger.error(f"Error getting exercise stats: {e}")
        return None

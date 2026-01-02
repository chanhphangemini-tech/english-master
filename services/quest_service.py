import random
from datetime import datetime, timezone, timedelta
from core.data import get_user_stats
from core.database import supabase
from services.user_service import add_coins
import logging
from core.timezone_utils import get_vn_start_of_day_utc, get_vn_start_of_week_utc, get_vn_now_utc

logger = logging.getLogger(__name__)

def generate_daily_quests(user_id):
    """
    Tạo danh sách nhiệm vụ hàng ngày ngẫu nhiên cho người dùng.
    """
    stats = get_user_stats(user_id)
    
    # Đếm số từ đã review hôm nay (dùng VN timezone)
    review_count_today = 0
    try:
        start_of_day_utc = get_vn_start_of_day_utc()
        
        if supabase:
            # Đếm số từ có last_reviewed_at trong ngày
            review_res = supabase.table("UserVocabulary")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("last_reviewed_at", start_of_day_utc)\
                .not_.is_("last_reviewed_at", "null")\
                .execute()
            review_count_today = review_res.count or 0
    except Exception:
        pass
    
    # --- Ngân hàng nhiệm vụ (Quest Pool) ---
    all_quests = [
        # Nhiệm vụ học tập
        {"id": "learn_10_new", "desc": "Học 10 từ vựng mới", "target": 10, "current": stats.get('words_today', 0), "reward": 10},
        {"id": "review_15_srs", "desc": "Ôn tập 15 từ SRS", "target": 15, "current": review_count_today, "reward": 15},
        {"id": "complete_1_grammar", "desc": "Hoàn thành 1 bài ngữ pháp", "target": 1, "current": 0, "reward": 20}, # Cần logic đếm grammar
        
        # Nhiệm vụ kỹ năng
        {"id": "do_1_listening", "desc": "Làm 1 bài luyện nghe", "target": 1, "current": 0, "reward": 15},
        {"id": "do_1_speaking", "desc": "Làm 1 bài luyện nói", "target": 1, "current": 0, "reward": 15},
        {"id": "do_1_reading", "desc": "Làm 1 bài luyện đọc", "target": 1, "current": 0, "reward": 15},
        {"id": "do_1_writing", "desc": "Làm 1 bài luyện viết", "target": 1, "current": 0, "reward": 15},
    ]

    # --- Logic lựa chọn nhiệm vụ ---
    # 1. Luôn có nhiệm vụ học từ mới
    daily_quests = [q for q in all_quests if q['id'] == 'learn_10_new']
    
    # 2. Chọn ngẫu nhiên 2 nhiệm vụ khác
    other_quests = [q for q in all_quests if q['id'] != 'learn_10_new']
    
    # Tùy chỉnh lựa chọn dựa trên tiến độ (ví dụ)
    # Nếu user chưa chơi pvp, ưu tiên nhiệm vụ pvp
    # (Logic này có thể mở rộng sau)
    
    if len(other_quests) >= 2:
        chosen_quests = random.sample(other_quests, 2)
        daily_quests.extend(chosen_quests)

    # Thêm nhiệm vụ tổng hợp
    daily_quests.append({"id": "complete_all", "desc": "Hoàn thành tất cả nhiệm vụ ngày", "target": len(daily_quests), "current": 0, "reward": 50})

    return daily_quests

def has_received_daily_quest_reward(user_id: int, quest_id: str) -> bool:
    """
    Kiểm tra xem user đã nhận reward cho quest này hôm nay chưa.
    
    Args:
        user_id: ID của user
        quest_id: ID của quest
    
    Returns:
        bool: True nếu đã nhận reward, False nếu chưa
    """
    if not supabase:
        return False
    
    try:
        # Lấy start of day (VN timezone -> UTC)
        start_of_day_utc = get_vn_start_of_day_utc()
        
        # Kiểm tra trong ActivityLog
        res = supabase.table("ActivityLog")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .eq("action_type", "quest_reward_daily")\
            .gte("created_at", start_of_day_utc)\
            .execute()
        
        # Filter results in Python to check metadata->quest_id
        if res.data:
            for log in res.data:
                metadata = log.get('metadata', {})
                if isinstance(metadata, dict) and metadata.get('quest_id') == quest_id:
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking daily quest reward: {e}")
        return False

def complete_daily_quest(user_id: int, quest_id: str, reward_amount: int) -> bool:
    """
    Thưởng coin khi hoàn thành daily quest.
    Tránh double reward bằng cách check ActivityLog.
    
    Args:
        user_id: ID của user
        quest_id: ID của quest
        reward_amount: Số coin thưởng
    
    Returns:
        bool: True nếu thành công, False nếu đã nhận reward rồi hoặc có lỗi
    """
    if not supabase or not user_id or reward_amount <= 0:
        return False
    
    # Kiểm tra xem đã nhận reward chưa
    if has_received_daily_quest_reward(user_id, quest_id):
        return False
    
    try:
        # Thưởng coin
        success = add_coins(user_id, reward_amount)
        if not success:
            return False
        
        # Log vào ActivityLog để track
        supabase.table("ActivityLog").insert({
            "user_id": user_id,
            "action_type": "quest_reward_daily",
            "value": reward_amount,
            "metadata": {
                "quest_id": quest_id,
                "reward_type": "daily_quest",
                "rewarded_at": get_vn_now_utc()
            }
        }).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error completing daily quest reward: {e}")
        return False

def generate_weekly_quests(user_id):
    """
    Tạo danh sách nhiệm vụ hàng tuần ngẫu nhiên cho người dùng.
    """
    stats = get_user_stats(user_id)
    
    # Đếm số từ học trong tuần này (dùng VN timezone)
    words_this_week = 0
    reviews_this_week = 0
    try:
        start_of_week_utc = get_vn_start_of_week_utc()
        
        if supabase:
            # Đếm từ mới trong tuần
            words_res = supabase.table("UserVocabulary")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", start_of_week_utc)\
                .execute()
            words_this_week = words_res.count or 0
            
            # Đếm reviews trong tuần
            review_res = supabase.table("UserVocabulary")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("last_reviewed_at", start_of_week_utc)\
                .not_.is_("last_reviewed_at", "null")\
                .execute()
            reviews_this_week = review_res.count or 0
    except Exception:
        pass
    
    # --- Ngân hàng nhiệm vụ tuần (Quest Pool) ---
    all_weekly_quests = [
        {"id": "learn_50_new", "desc": "Học 50 từ vựng mới trong tuần", "target": 50, "current": words_this_week, "reward": 100},
        {"id": "review_100_srs", "desc": "Ôn tập 100 từ SRS trong tuần", "target": 100, "current": reviews_this_week, "reward": 150},
        {"id": "complete_5_grammar", "desc": "Hoàn thành 5 bài ngữ pháp", "target": 5, "current": 0, "reward": 200},  # TODO: Implement tracking
        {"id": "do_10_listening", "desc": "Làm 10 bài luyện nghe", "target": 10, "current": 0, "reward": 150},  # TODO: Implement tracking
        {"id": "do_10_speaking", "desc": "Làm 10 bài luyện nói", "target": 10, "current": 0, "reward": 150},  # TODO: Implement tracking
        {"id": "maintain_7_streak", "desc": "Duy trì streak 7 ngày liên tiếp", "target": 7, "current": stats.get('streak', 0), "reward": 200},
        {"id": "win_5_pvp", "desc": "Thắng 5 trận PvP", "target": 5, "current": 0, "reward": 250},  # TODO: Implement tracking
    ]
    
    # Chọn ngẫu nhiên 3-4 quests
    if len(all_weekly_quests) >= 3:
        chosen_quests = random.sample(all_weekly_quests, min(4, len(all_weekly_quests)))
        return chosen_quests
    
    return all_weekly_quests

def has_received_weekly_quest_reward(user_id: int, quest_id: str) -> bool:
    """
    Kiểm tra xem user đã nhận reward cho weekly quest này tuần này chưa.
    
    Args:
        user_id: ID của user
        quest_id: ID của quest
    
    Returns:
        bool: True nếu đã nhận reward, False nếu chưa
    """
    if not supabase:
        return False
    
    try:
        # Lấy start of week (Monday, VN timezone -> UTC)
        start_of_week_utc = get_vn_start_of_week_utc()
        
        # Kiểm tra trong ActivityLog
        res = supabase.table("ActivityLog")\
            .select("id, metadata")\
            .eq("user_id", user_id)\
            .eq("action_type", "quest_reward_weekly")\
            .gte("created_at", start_of_week_utc)\
            .execute()
        
        # Filter results in Python to check metadata->quest_id
        if res.data:
            for log in res.data:
                metadata = log.get('metadata', {})
                if isinstance(metadata, dict) and metadata.get('quest_id') == quest_id:
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking weekly quest reward: {e}")
        return False

def complete_weekly_quest(user_id: int, quest_id: str, reward_amount: int) -> bool:
    """
    Thưởng coin khi hoàn thành weekly quest.
    Tránh double reward bằng cách check ActivityLog.
    
    Args:
        user_id: ID của user
        quest_id: ID của quest
        reward_amount: Số coin thưởng
    
    Returns:
        bool: True nếu thành công, False nếu đã nhận reward rồi hoặc có lỗi
    """
    if not supabase or not user_id or reward_amount <= 0:
        return False
    
    # Kiểm tra xem đã nhận reward chưa
    if has_received_weekly_quest_reward(user_id, quest_id):
        return False
    
    try:
        # Thưởng coin
        success = add_coins(user_id, reward_amount)
        if not success:
            return False
        
        # Log vào ActivityLog để track
        supabase.table("ActivityLog").insert({
            "user_id": user_id,
            "action_type": "quest_reward_weekly",
            "value": reward_amount,
            "metadata": {
                "quest_id": quest_id,
                "reward_type": "weekly_quest",
                "rewarded_at": get_vn_now_utc()
            }
        }).execute()
        
        # Check quest achievements
        try:
            from services.achievement_service import check_achievements
            # Count total completed quests (daily + weekly)
            # Count daily quests
            daily_res = supabase.table("ActivityLog").select("id", count="exact").eq("user_id", user_id).eq("action_type", "quest_reward_daily").execute()
            daily_count = daily_res.count if hasattr(daily_res, 'count') and daily_res.count else 0
            
            # Count weekly quests
            weekly_res = supabase.table("ActivityLog").select("id", count="exact").eq("user_id", user_id).eq("action_type", "quest_reward_weekly").execute()
            weekly_count = weekly_res.count if hasattr(weekly_res, 'count') and weekly_res.count else 0
            
            total_quests = daily_count + weekly_count
            check_achievements(user_id, 'quest', total_quests)
        except Exception as e:
            logger.warning(f"Error checking quest achievements: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error completing weekly quest reward: {e}")
        return False
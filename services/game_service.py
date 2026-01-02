from core.database import supabase
from datetime import datetime, timezone
from core.timezone_utils import get_vn_now_utc

def save_mock_test_result(user_id, level, score):
    """Lưu kết quả bài thi thử."""
    if not supabase or not user_id: 
        return False
    try:
        # Ensure score is properly formatted for numeric type
        score_value = float(score) if score is not None else None
        
        result = supabase.table("MockTestResults").insert({
            "user_id": int(user_id),
            "level": str(level) if level else None,
            "score": score_value,
            "completed_at": get_vn_now_utc()
        }).execute()
        # Check if insert was successful
        if result.data and len(result.data) > 0:
            return True
        return False
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        error_msg = str(e)
        logger.error(f"Error saving mock test result for user {user_id}, level={level}, score={score}: {error_msg}")
        # Log specific error types for easier debugging
        if 'RLS' in error_msg or 'policy' in error_msg.lower():
            logger.warning(f"RLS policy blocking insert: {error_msg}")
        elif 'violates' in error_msg.lower() or 'constraint' in error_msg.lower():
            logger.warning(f"Database constraint violation: {error_msg}")
        elif 'foreign key' in error_msg.lower():
            logger.warning(f"Foreign key violation - user {user_id} may not exist in Users table: {error_msg}")
        # Return False instead of raising - let bot tester handle the False case
        return False

def create_pvp_challenge(user_id, level, topic, bet, questions):
    """Tạo phòng thách đấu."""
    if not supabase: return None, "No DB"
    try:
        res = supabase.rpc("create_challenge", {
            "p_creator_id": int(user_id),
            "p_level": level,
            "p_topic": topic,
            "p_bet": int(bet),
            "p_questions": questions # List of dicts
        }).execute()
        
        # Security Monitor: Log successful challenge creation
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'pvp_create', success=True, metadata={'level': level, 'topic': topic, 'bet': bet})
        except Exception:
            pass
        
        return res.data, "Success"
    except Exception as e:
        error_msg = str(e)
        
        # Security Monitor: Log failed challenge creation
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'pvp_create', success=False, metadata={'level': level, 'topic': topic, 'bet': bet, 'error': error_msg})
        except Exception:
            pass
        
        return None, error_msg

def get_open_challenges(current_user_id):
    """Lấy danh sách phòng đang mở (trừ phòng của mình)."""
    if not supabase: return []
    try:
        # Lấy challenges status='open' và creator_id != current_user_id
        # Cần join với Users để lấy tên người tạo
        res = supabase.table("PvPChallenges").select("*, Users:creator_id(name, avatar_url)").eq("status", "open").neq("creator_id", int(current_user_id)).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Get challenges error: {e}")
        return []

def get_active_challenge(user_id):
    """Kiểm tra xem user có đang trong trận đấu nào không (status='active')."""
    if not supabase: return None
    try:
        # Tìm trận đấu mà user tham gia và đang diễn ra
        res = supabase.table("PvPChallenges").select("*, Users!creator_id(name), Opponent:Users!challenger_id(name)") \
            .or_(f"creator_id.eq.{user_id},challenger_id.eq.{user_id}") \
            .eq("status", "active") \
            .maybe_single() \
            .execute()
        return res.data
    except Exception as e:
        return None

def join_pvp_challenge(challenge_id, user_id):
    """Tham gia phòng."""
    if not supabase: return "No DB"
    try:
        res = supabase.rpc("join_challenge", {
            "p_challenge_id": str(challenge_id),
            "p_user_id": int(user_id)
        }).execute()
        return res.data # 'Success' or error msg
    except Exception as e:
        return str(e)

def submit_pvp_score(challenge_id, user_id, score, is_creator):
    """Nộp điểm và kiểm tra kết thúc trận đấu."""
    if not supabase: return "No DB"
    try:
        # Cập nhật điểm số trực tiếp
        col = "creator_score" if is_creator else "challenger_score"
        supabase.table("PvPChallenges").update({col: int(score)}).eq("id", challenge_id).execute()
        
        # Kiểm tra xem cả 2 đã nộp điểm chưa để kết thúc trận đấu
        # (Logic này có thể chuyển vào Database Trigger/RPC để an toàn hơn, nhưng làm ở đây cho nhanh)
        match = supabase.table("PvPChallenges").select("*").eq("id", challenge_id).single().execute().data
        
        if match['creator_score'] is not None and match['challenger_score'] is not None:
            # Cả 2 đã xong -> Tính người thắng
            winner_id = None
            if match['creator_score'] > match['challenger_score']: winner_id = match['creator_id']
            elif match['challenger_score'] > match['creator_score']: winner_id = match['challenger_id']
            # Nếu hòa thì winner_id = None
            
            supabase.table("PvPChallenges").update({
                "status": "finished",
                "winner_id": winner_id
            }).eq("id", challenge_id).execute()
            
            # Check PvP achievements for the winner
            if winner_id:
                try:
                    from services.achievement_service import check_achievements
                    # Get total PvP wins for the winner
                    wins_res = supabase.table("PvPChallenges").select("id", count="exact").eq("winner_id", int(winner_id)).execute()
                    current_wins_count = wins_res.count or 0
                    check_achievements(int(winner_id), 'pvp', current_wins_count)
                except Exception as e:
                    logger.warning(f"Error checking PvP achievements for user {winner_id}: {e}")
            
        return "Success"
    except Exception as e:
        return str(e)

def get_all_pvp_challenges():
    """Lấy lịch sử đấu PvP cho Admin."""
    if not supabase: return []
    try:
        # Fetch challenges with creator and challenger names
        # Sử dụng cú pháp !foreign_key để phân biệt 2 quan hệ tới bảng Users
        res = supabase.table("PvPChallenges").select(
            "*, creator:Users!creator_id(name), challenger:Users!challenger_id(name)"
        ).order("created_at", desc=True).limit(50).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Error getting pvp history: {e}")
        return []

import streamlit as st
import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=60, show_spinner=False)  # Cache for 1 minute  
def get_leaderboard_english():
    """Lấy bảng xếp hạng top học viên.
    
    Cached for 60 seconds to dramatically improve performance.
    """
    if not supabase:
        logger.warning("Supabase client not initialized")
        return []
    
    try:
        res = supabase.rpc('get_leaderboard_english').execute()
        return res.data if res.data else []
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return []

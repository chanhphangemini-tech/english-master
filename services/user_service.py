import streamlit as st
from core.database import supabase
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
import logging
import json
import re
from core.timezone_utils import get_vn_start_of_day_utc, get_vn_now_utc

logger = logging.getLogger(__name__)

@st.cache_data(ttl=30, show_spinner=False)  # Cache 30s - balance between freshness and performance
def _get_user_stats_cached(user_id: int, start_of_day_utc: str) -> Dict[str, Any]:
    """
    Internal cached function for stats (excluding coins which change frequently).
    Coins are fetched separately and merged.
    """
    default_stats = {
        "streak": 0,
        "words_learned": 0,
        "words_today": 0,
        "latest_test_score": None
    }
    
    if not supabase or not user_id: 
        return default_stats
    
    try:
        # Try RPC first
        try:
            res = supabase.rpc("get_dashboard_stats", {
                "p_user_id": int(user_id),
                "p_start_of_day": start_of_day_utc
            }).execute()
            
            if res.data and len(res.data) > 0:
                data = res.data[0]
                latest_score_str = None
                if data.get('latest_score') is not None:
                    latest_score_str = f"{data.get('latest_score')}/10 ({data.get('latest_level', '')})"
                
                return {
                    "streak": data.get('streak', 0),
                    "words_learned": data.get('words_learned', 0),
                    "words_today": data.get('words_today', 0),
                    "latest_test_score": latest_score_str
                }
        except Exception as rpc_error:
            logger.debug(f"RPC get_dashboard_stats failed, using direct queries: {rpc_error}")
        
        # Fallback: Direct queries (optimized - only check MockTestResults)
        try:
            words_res = supabase.table("UserVocabulary").select("id", count="exact").eq("user_id", int(user_id)).execute()
            default_stats["words_learned"] = words_res.count if hasattr(words_res, 'count') else 0
            
            words_today_res = supabase.table("UserVocabulary").select("id", count="exact").eq("user_id", int(user_id)).gte("created_at", start_of_day_utc).execute()
            default_stats["words_today"] = words_today_res.count if hasattr(words_today_res, 'count') else 0
            
            # Only check MockTestResults (most common test table)
            try:
                test_res = supabase.table("MockTestResults").select("score, level").eq("user_id", int(user_id)).order("completed_at", desc=True).limit(1).execute()
                if test_res.data and len(test_res.data) > 0:
                    test_data = test_res.data[0]
                    score = test_data.get('score', 0)
                    level = test_data.get('level', '')
                    if score is not None:
                        default_stats["latest_test_score"] = f"{score}/10 ({level})"
            except:
                pass
        except Exception as fallback_error:
            logger.warning(f"Error in fallback stats query: {fallback_error}")
        
        return default_stats
    except Exception as e:
        logger.error(f"Error in _get_user_stats_cached: {e}")
        return default_stats

def get_user_stats(user_id: int) -> Dict[str, Any]:
    """
    Lấy toàn bộ chỉ số Dashboard thông qua 1 hàm RPC duy nhất.
    Gồm: Streak, Coin, Số từ đã học, Số từ hôm nay, Điểm thi gần nhất.
    Coin được lấy trực tiếp từ Users table để đảm bảo cập nhật ngay lập tức.
    """
    default_stats = {
        "streak": 0,
        "words_learned": 0,
        "words_today": 0,
        "coins": 0,
        "latest_test_score": None
    }
    
    if not supabase or not user_id: 
        return default_stats
    
    try:
        # 1. Lấy coin trực tiếp từ Users table (không qua cache/RPC để đảm bảo cập nhật ngay)
        try:
            user_res = supabase.table("Users").select("coins").eq("id", int(user_id)).single().execute()
            if user_res.data:
                default_stats["coins"] = user_res.data.get("coins", 0) or 0
        except Exception as coin_error:
            logger.warning(f"Error fetching coins directly: {coin_error}")
        
        # 2. Chuẩn bị thời gian bắt đầu ngày mới (Giờ Việt Nam -> UTC)
        start_of_day_utc = get_vn_start_of_day_utc()
        
        # 3. Thử gọi hàm RPC 'get_dashboard_stats' để lấy các stats khác
        # Nếu RPC không tồn tại, sẽ fallback về lấy dữ liệu trực tiếp từ các bảng
        try:
            res = supabase.rpc("get_dashboard_stats", {
                "p_user_id": int(user_id),
                "p_start_of_day": start_of_day_utc
            }).execute()
            
            if res.data and len(res.data) > 0:
                data = res.data[0]
                
                # Format điểm thi (nếu có)
                latest_score_str = None
                if data.get('latest_score') is not None:
                    latest_score_str = f"{data.get('latest_score')}/10 ({data.get('latest_level', '')})"
                
                # Sử dụng coin từ Users table (đã lấy ở trên), không dùng từ RPC
                return {
                    "streak": data.get('streak', 0),
                    "coins": default_stats["coins"],  # Dùng coin từ Users table
                    "words_learned": data.get('words_learned', 0),
                    "words_today": data.get('words_today', 0),
                    "latest_test_score": latest_score_str
                }
        except Exception as rpc_error:
            # RPC không tồn tại hoặc có lỗi, fallback về lấy dữ liệu trực tiếp
            # Only log at debug level to reduce noise (RPC may not exist, which is OK)
            logger.debug(f"RPC get_dashboard_stats failed, using direct queries: {rpc_error}")
        
        # 4. Fallback: Lấy dữ liệu trực tiếp từ các bảng
        # Note: streak không có trong Users table, nó được tính qua RPC process_daily_streak
        # Nếu RPC không có, streak sẽ mặc định là 0 (đã set trong default_stats)
        try:
            # Lấy số từ đã học (tổng số từ trong UserVocabulary)
            try:
                words_res = supabase.table("UserVocabulary").select("id", count="exact").eq("user_id", int(user_id)).execute()
                default_stats["words_learned"] = words_res.count if hasattr(words_res, 'count') else 0
            except:
                pass
            
            # Lấy số từ học hôm nay (UserVocabulary được tạo hôm nay)
            try:
                words_today_res = supabase.table("UserVocabulary").select("id", count="exact").eq("user_id", int(user_id)).gte("created_at", start_of_day_utc).execute()
                default_stats["words_today"] = words_today_res.count if hasattr(words_today_res, 'count') else 0
            except:
                pass
            
            # Lấy điểm thi gần nhất (chỉ query MockTestResults - table duy nhất tồn tại)
            try:
                test_res = supabase.table("MockTestResults").select("score, level").eq("user_id", int(user_id)).order("completed_at", desc=True).limit(1).execute()
                if test_res.data and len(test_res.data) > 0:
                    test_data = test_res.data[0]
                    score = test_data.get('score', 0)
                    level = test_data.get('level', '')
                    if score is not None:
                        default_stats["latest_test_score"] = f"{score}/10 ({level})"
            except Exception as test_error:
                logger.debug(f"Error querying MockTestResults: {test_error}")
                pass
                    
        except Exception as fallback_error:
            logger.warning(f"Error in fallback stats query: {fallback_error}")
        
        # Trả về stats với dữ liệu đã lấy được
        return default_stats
            
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        # Vẫn trả về coin từ Users table nếu có lỗi
        return default_stats

def log_activity(user_id: int, action: str, value: int = 0) -> None:
    """Ghi nhật ký hoạt động của người dùng."""
    if not supabase: return
    try:
        supabase.table("ActivityLog").insert({
            "user_id": int(user_id),
            "action_type": action,
            "value": int(value),
            "created_at": get_vn_now_utc()
        }).execute()
    except Exception as e:
        logger.error(f"Log activity error: {e}")

def get_user_badges(user_id: int) -> list:
    """Lấy danh sách huy hiệu của user"""
    if not supabase: return []
    try:
        res = supabase.table("UserBadges").select("*, Badges(name, description, icon)").eq("user_id", int(user_id)).execute()
        return res.data if res.data else []
    except Exception as e:
        logger.error(f"Get user badges error: {e}")
        return []

def check_and_award_badge(user_id: int, badge_criteria: Dict[str, Any]) -> bool:
    """Kiểm tra và trao huy hiệu nếu đủ điều kiện"""
    if not supabase: return False
    try:
        # Kiểm tra xem user đã có badge này chưa
        res = supabase.table("UserBadges").select("id").eq("user_id", int(user_id)).eq("badge_id", badge_criteria['badge_id']).execute()
        if not res.data:  # Chưa có badge
            # Logic kiểm tra điều kiện (giản lược)
            supabase.table("UserBadges").insert({
                "user_id": int(user_id),
                "badge_id": badge_criteria['badge_id'],
                "earned_at": get_vn_now_utc()
            }).execute()
            return True
    except: pass
    return False

def add_coins(user_id: int, amount_to_add: int) -> bool:
    """
    Cộng coin cho người dùng một cách an toàn.
    Sử dụng RPC để tránh race condition.
    
    Returns:
        bool: True nếu thành công, False nếu thất bại
    """
    if not supabase or not user_id or amount_to_add == 0:
        return False
    try:
        supabase.rpc('increment_coins', {
            'p_user_id': int(user_id),
            'p_amount': int(amount_to_add)
        }).execute()
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error adding coins for user {user_id}: {error_msg}")
        # Check if RPC function doesn't exist
        if 'does not exist' in error_msg.lower() or 'function' in error_msg.lower():
            logger.warning(f"RPC function 'increment_coins' may not exist in database. Please run db_create_rpc_functions.sql")
        return False

def process_daily_streak(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Xử lý logic tính streak hàng ngày.
    Gọi RPC 'process_daily_streak' để đảm bảo tính đúng đắn.
    Sau đó check streak milestones và award rewards nếu có.
    
    Returns:
        Dict với keys: current_streak, words_today, status, message, milestones (if any)
        None nếu có lỗi
    """
    if not supabase or not user_id: return None
    try:
        res = supabase.rpc('process_daily_streak', {'p_user_id': int(user_id)}).execute()
        if res.data:
            # Convert JSONB response to dict if needed
            streak_result = None
            if isinstance(res.data, dict):
                streak_result = res.data
            elif isinstance(res.data, list) and len(res.data) > 0:
                streak_result = res.data[0]
            
            if streak_result:
                # Check streak milestones after streak is updated
                current_streak = streak_result.get('current_streak', 0)
                if current_streak and current_streak > 0:
                    try:
                        from services.streak_service import check_streak_milestones
                        achieved_milestones = check_streak_milestones(user_id, current_streak)
                        if achieved_milestones:
                            # Add milestones to result
                            streak_result['milestones'] = achieved_milestones
                            logger.info(f"User {user_id} achieved {len(achieved_milestones)} streak milestone(s)")
                    except Exception as milestone_error:
                        # Don't fail streak processing if milestone check fails
                        logger.warning(f"Error checking streak milestones: {milestone_error}")
                
                return streak_result
        return None
    except Exception as e:
        # Error can be a dict or Exception object - check before converting to string
        error_msg_str = str(e)
        error_dict = e if isinstance(e, dict) else None
        
        # Check if it's a JSON parsing error (RPC returns JSON string in error details)
        # Error format: {'message': '...', 'code': 200, 'details': "b'...'"}
        if error_dict:
            details = str(error_dict.get('details', ''))
            message = str(error_dict.get('message', ''))
            if 'JSON could not be generated' in message or ('status' in details and 'current_streak' in details):
                try:
                    # Extract JSON from details (format: "b'{...}'" or just "{...}")
                    json_match = re.search(r"b?'({.*?})'", details)
                    if json_match:
                        json_str = json_match.group(1).replace('\\"', '"')
                        parsed_json = json.loads(json_str)
                        # If it's a valid response with current_streak or status, return it
                        if 'current_streak' in parsed_json or 'status' in parsed_json:
                            current_streak = parsed_json.get('current_streak', parsed_json.get('streak', 0))
                            # Check streak milestones if streak > 0
                            if current_streak and current_streak > 0:
                                try:
                                    from services.streak_service import check_streak_milestones
                                    achieved_milestones = check_streak_milestones(user_id, current_streak)
                                    if achieved_milestones:
                                        parsed_json['milestones'] = achieved_milestones
                                except:
                                    pass
                            return parsed_json
                except Exception as parse_error:
                    logger.debug(f"Failed to parse JSON from error: {parse_error}")
        else:
            # Handle string error format (when exception is not a dict)
            if 'JSON could not be generated' in error_msg_str:
                try:
                    # Try to extract JSON from string
                    json_match = re.search(r"details.*b?'({.*?})'", error_msg_str)
                    if json_match:
                        json_str = json_match.group(1).replace('\\"', '"')
                        parsed_json = json.loads(json_str)
                        if 'current_streak' in parsed_json or 'status' in parsed_json:
                            current_streak = parsed_json.get('current_streak', parsed_json.get('streak', 0))
                            if current_streak and current_streak > 0:
                                try:
                                    from services.streak_service import check_streak_milestones
                                    achieved_milestones = check_streak_milestones(user_id, current_streak)
                                    if achieved_milestones:
                                        parsed_json['milestones'] = achieved_milestones
                                except:
                                    pass
                            logger.debug(f"RPC returned JSON in error string (parsed successfully): {parsed_json}")
                            return parsed_json
                except Exception as parse_error:
                    logger.debug(f"Failed to parse JSON from error string: {parse_error}")
        
        # Only log as error if it's not a handled JSON parsing case
        if 'JSON could not be generated' not in error_msg_str:
            logger.error(f"Error processing streak for user {user_id}: {error_msg_str}")
        # Check if RPC function doesn't exist
        if 'does not exist' in error_msg_str.lower() or 'function' in error_msg_str.lower():
            logger.warning(f"RPC function 'process_daily_streak' may not exist in database. Please run db_create_rpc_functions.sql")
        return None

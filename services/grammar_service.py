from core.database import supabase
from core.llm import generate_grammar_test_questions as llm_generate_test
from datetime import datetime, timezone
from core.timezone_utils import get_vn_now_utc

def load_grammar_progress(user_id):
    """
    Lấy danh sách các bài ngữ pháp đã hoàn thành của user.
    Trả về set các unit_id (dạng 'LEVEL_UNITKEY', ví dụ 'A1_U1').
    Note: unit_id được lưu trong cột lesson_code của UserGrammarProgress.
    """
    if not supabase: return set()
    try:
        # Sử dụng bảng UserGrammarProgress, lấy từ cột lesson_code (lưu unit_id)
        res = supabase.table("UserGrammarProgress").select("lesson_code").eq("user_id", int(user_id)).not_.is_("lesson_code", "null").execute()
        return {item['lesson_code'] for item in res.data if item.get('lesson_code')} if res.data else set()
    except Exception as e:
        # print(f"Load grammar progress error: {e}")
        return set()

def save_grammar_progress(user_id, unit_id):
    """
    Lưu trạng thái hoàn thành bài học.
    Note: unit_id được lưu vào cột lesson_code của UserGrammarProgress.
    """
    if not supabase: return False
    try:
        # Lưu unit_id vào cột lesson_code (vì bảng không có cột unit_id)
        # Tìm lesson_id từ GrammarLessons nếu có thể (optional)
        lesson_id = None
        try:
            # Extract level và topic từ unit_id nếu có format 'LEVEL_TOPIC'
            if '_' in unit_id:
                parts = unit_id.split('_', 1)
                if len(parts) == 2:
                    level, topic_part = parts
                    # Try to find matching lesson
                    lesson_res = supabase.table("GrammarLessons").select("id").eq("level", level).limit(1).execute()
                    if lesson_res.data:
                        lesson_id = lesson_res.data[0]['id']
        except:
            pass
        
        data = {
            "user_id": int(user_id),
            "lesson_code": unit_id,  # Lưu unit_id vào lesson_code
            "completed_at": get_vn_now_utc(),
            "status": "completed"
        }
        if lesson_id:
            data["lesson_id"] = lesson_id
        
        # Check if record exists (by user_id and lesson_code)
        try:
            existing = supabase.table("UserGrammarProgress").select("id").eq("user_id", int(user_id)).eq("lesson_code", unit_id).execute()
            if existing.data:
                # Update existing record
                supabase.table("UserGrammarProgress").update(data).eq("id", existing.data[0]['id']).execute()
            else:
                # Insert new record
                supabase.table("UserGrammarProgress").insert(data).execute()
        except Exception as upsert_error:
            # Fallback: try simple insert (ignore duplicates if any)
            try:
                supabase.table("UserGrammarProgress").insert(data).execute()
            except:
                pass
        
        # Check grammar level achievements (when a unit is completed)
        try:
            # Extract level from unit_id (format: 'LEVEL_UNITKEY', e.g., 'A1_U1')
            if '_' in unit_id:
                level = unit_id.split('_')[0]  # Extract 'A1' from 'A1_U1'
                
                # Check if all lessons in this level are completed
                # Get all lessons for this level
                lessons_res = supabase.table("GrammarLessons").select("topic").eq("level", level).execute()
                if lessons_res.data:
                    total_lessons = len(lessons_res.data)
                    # Get completed lessons for this level (dùng lesson_code thay vì unit_id)
                    completed_res = supabase.table("UserGrammarProgress").select("lesson_code").eq("user_id", int(user_id)).like("lesson_code", f"{level}_%").execute()
                    completed_lessons = len(completed_res.data) if completed_res.data else 0
                    
                    # If all lessons completed, check achievements
                    if completed_lessons >= total_lessons:
                        from services.achievement_service import check_grammar_level_achievements
                        check_grammar_level_achievements(user_id, level, is_complete=True)
        except Exception as e:
            import logging
            logging.warning(f"Error checking grammar achievements: {e}")
        
        return True
    except Exception as e:
        print(f"Save grammar progress error: {e}")
        return False

def get_theory_cache(level, unit_key):
    """Lấy nội dung bài giảng AI đã cache từ bảng TheoryCache."""
    if not supabase: return None
    try:
        res = supabase.table("TheoryCache").select("content").eq("level", level).eq("unit_key", unit_key).maybe_single().execute()
        if res.data:
            return res.data['content']
    except Exception as e:
        print(f"Get theory cache error: {e}")
    return None

def save_theory_cache(level, unit_key, content):
    """Lưu nội dung bài giảng AI vào bảng TheoryCache."""
    if not supabase: return False
    try:
        data = {
            "level": level,
            "unit_key": unit_key,
            "content": content,
            "updated_at": get_vn_now_utc()
        }
        # Upsert dựa trên level và unit_key
        supabase.table("TheoryCache").upsert(data, on_conflict="level, unit_key").execute()
        return True
    except Exception as e:
        print(f"Save theory cache error: {e}")
        return False

def generate_grammar_test_questions(level, topic, num_questions=10):
    """Wrapper để gọi hàm tạo câu hỏi từ core.llm"""
    return llm_generate_test(level, topic, num_questions)

def get_user_grammar_progress(user_id):
    """
    Lấy tiến độ chi tiết (dùng cho trang Hồ Sơ).
    Trả về dict: { 'A1_U1': 'completed', ... }
    Note: unit_id được lưu trong cột lesson_code của UserGrammarProgress.
    """
    if not supabase: return {}
    try:
        res = supabase.table("UserGrammarProgress").select("lesson_code").eq("user_id", int(user_id)).not_.is_("lesson_code", "null").execute()
        return {item['lesson_code']: 'completed' for item in res.data if item.get('lesson_code')} if res.data else {}
    except:
        return {}

def load_grammar_lessons_from_db(level_code):
    """
    Lấy toàn bộ bài học ngữ pháp của một level từ DB.
    Trả về dict dạng: {'U1': {'title': ..., 'content': ...}, 'U2': ...}
    """
    if not supabase: return None
    try:
        res = supabase.table("GrammarLessons").select("topic, content").eq("level", level_code).execute()
        if not res.data:
            return None
        
        # Chuyển đổi list of dicts thành dict of dicts, với key là 'topic' (U1, U2...)
        lessons_dict = {lesson.get('topic'): lesson.get('content') for lesson in res.data if lesson.get('topic')}
                
        return lessons_dict if lessons_dict else None
    except Exception as e:
        print(f"Load grammar lessons from DB error: {e}")
        return None

# ============================================
# Comments & Votes Functions
# ============================================

def get_lesson_comments(level: str, unit_key: str):
    """Lấy danh sách comments cho một lesson."""
    if not supabase:
        return []
    try:
        # Join với Users table để lấy name và username
        res = supabase.table("GrammarLessonComments").select(
            "id, user_id, comment_text, created_at, updated_at, Users:user_id(name, username)"
        ).eq("level", level).eq("unit_key", unit_key).eq("is_deleted", False).order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        import logging
        logging.error(f"Error getting lesson comments: {e}")
        return []

def save_lesson_comment(level: str, unit_key: str, user_id: int, comment_text: str):
    """Lưu hoặc cập nhật comment của user."""
    if not supabase or not user_id or not comment_text.strip():
        return False
    try:
        data = {
            "level": level,
            "unit_key": unit_key,
            "user_id": int(user_id),
            "comment_text": comment_text.strip(),
            "is_deleted": False,
            "updated_at": get_vn_now_utc()
        }
        # Upsert (mỗi user chỉ có 1 comment, có thể edit)
        supabase.table("GrammarLessonComments").upsert(data, on_conflict="level, unit_key, user_id").execute()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error saving lesson comment: {e}")
        return False

def get_user_comment(level: str, unit_key: str, user_id: int):
    """Lấy comment của user hiện tại (nếu có)."""
    if not supabase or not user_id:
        return None
    try:
        res = supabase.table("GrammarLessonComments").select(
            "id, comment_text, created_at, updated_at"
        ).eq("level", level).eq("unit_key", unit_key).eq("user_id", int(user_id)).eq("is_deleted", False).maybe_single().execute()
        # Check if result exists and has data
        if res and hasattr(res, 'data') and res.data:
            return res.data
        return None
    except Exception as e:
        import logging
        logging.error(f"Error getting user comment: {e}")
        return None

def get_lesson_votes(level: str, unit_key: str):
    """Lấy tổng số votes (like/dislike) cho một lesson."""
    if not supabase:
        return {"like": 0, "dislike": 0}
    try:
        # Get all votes for this lesson
        res = supabase.table("GrammarLessonVotes").select("vote_type").eq("level", level).eq("unit_key", unit_key).execute()
        like_count = sum(1 for row in (res.data or []) if row.get('vote_type') == 'like')
        dislike_count = sum(1 for row in (res.data or []) if row.get('vote_type') == 'dislike')
        return {"like": like_count, "dislike": dislike_count}
    except Exception as e:
        import logging
        logging.error(f"Error getting lesson votes: {e}")
        return {"like": 0, "dislike": 0}

def get_user_vote(level: str, unit_key: str, user_id: int):
    """Lấy vote của user hiện tại (nếu có)."""
    if not supabase or not user_id:
        return None
    try:
        res = supabase.table("GrammarLessonVotes").select("vote_type").eq("level", level).eq("unit_key", unit_key).eq("user_id", int(user_id)).maybe_single().execute()
        # Check if result exists and has data
        if res and hasattr(res, 'data') and res.data:
            return res.data.get('vote_type')
        return None
    except Exception as e:
        import logging
        logging.error(f"Error getting user vote: {e}")
        return None

def save_lesson_vote(level: str, unit_key: str, user_id: int, vote_type: str):
    """Lưu hoặc cập nhật vote của user (like/dislike)."""
    if not supabase or not user_id or vote_type not in ['like', 'dislike']:
        return False
    try:
        data = {
            "level": level,
            "unit_key": unit_key,
            "user_id": int(user_id),
            "vote_type": vote_type,
            "updated_at": get_vn_now_utc()
        }
        # Upsert (mỗi user chỉ có 1 vote, có thể thay đổi)
        supabase.table("GrammarLessonVotes").upsert(data, on_conflict="level, unit_key, user_id").execute()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error saving lesson vote: {e}")
        return False
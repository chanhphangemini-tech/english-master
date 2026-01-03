from core.database import supabase
from core.srs import calculate_review_schedule
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import streamlit as st
import logging
from core.timezone_utils import get_vn_now_utc

logger = logging.getLogger(__name__)

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def load_vocab_data(level: str = None) -> List[Dict[str, Any]]:
    """Lấy danh sách từ vựng theo level. Nếu level=None, lấy tất cả.
    
    Cached for 1 hour to improve performance.
    """
    if not supabase: 
        logger.warning("Supabase client not initialized")
        return []
    try:
        # Use batch processing to avoid Supabase 1000 row limit
        all_vocab = []
        batch_size = 2000
        offset = 0
        
        while True:
            query = supabase.table("Vocabulary").select("*")
            if level:
                query = query.eq("level", level)
            res = query.order("word").range(offset, offset + batch_size - 1).execute()
            
            if not res.data:
                break
            
            all_vocab.extend(res.data)
            
            if len(res.data) < batch_size:
                break
            
            offset += batch_size
        
        return all_vocab
    except Exception as e:
        logger.error(f"Error loading vocab data (level={level}): {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes (reduced for faster updates and to avoid stale 1000-item cache)
def load_all_vocabulary(_cache_version: int = 3) -> List[Dict[str, Any]]:
    """Lấy toàn bộ từ vựng từ database (cho dictionary).
    
    Sử dụng pagination để lấy hết tất cả từ (không bị giới hạn 1000 rows).
    Cached for 5 minutes to improve performance while allowing updates.
    Optimized: Only select necessary columns to reduce data transfer.
    
    Args:
        _cache_version: Internal parameter to invalidate cache when changed (default: 2)
    """
    if not supabase: return []
    try:
        all_vocab = []
        batch_size = 1000  # Supabase has a default limit of 1000 rows per query
        offset = 0
        
        while True:
            # Fetch batch - select all columns including new vocabulary details
            # Use .limit() before .range() to ensure we get the full batch
            res = supabase.table("Vocabulary")\
                .select("id, word, pronunciation, meaning, type, level, topic, example, example_translation, collocations, phrasal_verbs, word_forms, synonyms, usage_notes")\
                .order("word")\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            if not res.data:
                break
            
            all_vocab.extend(res.data)
            
            # If we got less than batch_size, we've reached the end
            if len(res.data) < batch_size:
                break
            
            offset += batch_size
        
        logger.info(f"Loaded {len(all_vocab)} vocabulary items")
        return all_vocab
    except Exception as e:
        logger.error(f"Error loading vocabulary: {e}")
        return []


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_vocabulary_topics() -> List[str]:
    """Lấy danh sách các chủ đề có sẵn.
    
    Lấy từ toàn bộ vocabulary để đảm bảo có hết tất cả topics.
    Cached for 1 hour to improve performance.
    """
    if not supabase: return []
    try:
        # Fetch all topics in batches
        all_topics = set()
        batch_size = 1000
        offset = 0
        
        while True:
            res = supabase.table("Vocabulary")\
                .select("topic")\
                .range(offset, offset + batch_size - 1)\
                .execute()
            
            if not res.data:
                break
            
            # Add topics to set (auto deduplication)
            for item in res.data:
                if item.get('topic'):
                    all_topics.add(item['topic'])
            
            if len(res.data) < batch_size:
                break
            
            offset += batch_size
        
        return sorted(list(all_topics))
    except Exception as e:
        print(f"Error loading topics: {e}")
        return []


def get_vocabulary_levels() -> List[str]:
    """Lấy danh sách các cấp độ có sẵn."""
    return ["A1", "A2", "B1", "B2", "C1", "C2"]

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def get_total_vocabulary_count() -> int:
    """Lấy tổng số từ vựng trong database.
    
    Cached for 1 hour to improve performance.
    """
    if not supabase: return 0
    try:
        res = supabase.table("Vocabulary").select("id", count="exact").execute()
        return res.count if hasattr(res, 'count') and res.count else 0
    except Exception as e:
        logger.error(f"Error getting total vocabulary count: {e}")
        return 0

def load_progress(user_id: int) -> List[Dict[str, Any]]:
    """Lấy tiến độ học từ vựng của user."""
    if not supabase: return []
    try:
        # Join với bảng Vocabulary để lấy chi tiết từ
        res = supabase.table("UserVocabulary").select("*, Vocabulary(*)").eq("user_id", int(user_id)).execute()
        return res.data if res.data else []
    except: return []

def get_due_vocabulary(user_id: int) -> List[Dict[str, Any]]:
    """Lấy danh sách từ cần ôn tập (SRS)."""
    if not supabase: return []
    try:
        now_utc = get_vn_now_utc()
        # Lấy các từ có due_date <= hiện tại
        res = supabase.table("UserVocabulary").select("*, Vocabulary(*)").eq("user_id", int(user_id)).lte("due_date", now_utc).order("due_date").execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Error getting due vocab: {e}")
        return []

def update_srs_stats(user_id: int, vocab_id: int, quality: int) -> bool:
    """
    Cập nhật trạng thái SRS sau khi học.
    quality: 0-5 (0=Quên, 3=Khó, 5=Thuộc làu)
    """
    if not supabase: return False
    try:
        # 1. Lấy thông tin hiện tại
        res = supabase.table("UserVocabulary").select("*").eq("user_id", int(user_id)).eq("vocab_id", vocab_id).single().execute()
        if not res.data: return False
        
        current = res.data
        
        # 2. Tính toán lịch mới
        new_stats = calculate_review_schedule(
            quality=quality,
            last_interval=current.get('interval', 0),
            last_ease=current.get('ease_factor', 2.5),
            last_streak=current.get('streak', 0)
        )
        
        # 3. Cập nhật DB
        update_data = {
            "due_date": new_stats['next_review'].isoformat(),
            "interval": new_stats['interval'],
            "ease_factor": new_stats['ease_factor'],
            "streak": new_stats['streak'],
            "status": new_stats['status'],
            "last_reviewed_at": get_vn_now_utc()
        }
        
        supabase.table("UserVocabulary").update(update_data).eq("id", current['id']).execute()
        
        # Security Monitor: Log action
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'vocab_review', success=True, metadata={'vocab_id': vocab_id, 'quality': quality})
        except Exception:
            pass
        
        # Priority 3: Thưởng coin nhỏ khi review từ vựng thành công (quality >= 3)
        if quality >= 3:
            try:
                from services.user_service import add_coins
                # Thưởng 1 coin mỗi từ review thành công (quality >= 3)
                add_coins(user_id, 1)
            except Exception:
                pass  # Fail silently if coin reward fails
        
        return True
    except Exception as e:
        print(f"Error updating SRS: {e}")
        # Security Monitor: Log failed action
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'vocab_review', success=False, metadata={'vocab_id': vocab_id, 'error': str(e)})
        except Exception:
            pass
        return False

def add_word_to_srs(user_id: int, vocab_id: int) -> bool:
    """Thêm từ mới vào danh sách học (trạng thái learning)."""
    if not supabase: return False
    try:
        # Ensure vocab_id is int (may come as float from pandas/numpy)
        vocab_id = int(vocab_id)
        # Kiểm tra xem đã có chưa
        existing = supabase.table("UserVocabulary").select("id").eq("user_id", int(user_id)).eq("vocab_id", vocab_id).execute()
        if existing.data: return True 
        
        data = {
            "user_id": int(user_id),
            "vocab_id": vocab_id,
            "status": "learning",
            "streak": 0,
            "interval": 0,
            "ease_factor": 2.5,
            "due_date": get_vn_now_utc(),
            "last_reviewed_at": get_vn_now_utc()
        }
        supabase.table("UserVocabulary").insert(data).execute()
        
        # Check vocabulary achievements
        try:
            from services.achievement_service import check_achievements
            # Get total vocabulary count
            vocab_count_res = supabase.table("UserVocabulary")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            vocab_count = vocab_count_res.count or 0
            
            # Check achievements
            check_achievements(user_id, 'vocab', vocab_count)
        except Exception as e:
            logger.debug(f"Error checking vocab achievements: {e}")
        
        # Security Monitor: Log action
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'vocab_learn', success=True, metadata={'vocab_id': vocab_id, 'action': 'add_to_srs'})
        except Exception:
            pass
        
        # Priority 3: Thưởng coin nhỏ khi thêm từ mới vào SRS
        try:
            from services.user_service import add_coins
            # Thưởng 1 coin mỗi từ mới thêm vào SRS
            add_coins(user_id, 1)
        except Exception:
            pass  # Fail silently if coin reward fails
        
        return True
    except Exception as e:
        print(f"Error adding word to SRS: {e}")
        # Security Monitor: Log failed action
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'vocab_learn', success=False, metadata={'vocab_id': vocab_id, 'error': str(e)})
        except Exception:
            pass
        return False

def add_word_to_srs_and_prioritize(user_id, word_text, word_type, meaning):
    """
    Thêm từ mới (dạng text) vào DB và đặt ưu tiên học ngay.
    Hàm này sẽ tự tìm hoặc tạo từ trong bảng Vocabulary.
    """
    if not supabase: return None
    try:
        # 1. Tìm hoặc tạo từ trong bảng Vocabulary
        vocab_entry = supabase.table("Vocabulary").upsert({
            "word": word_text,
            "type": word_type,
            "meaning": {"vietnamese": meaning}
        }, on_conflict="word").select("id").single().execute().data

        if not vocab_entry: return None
        vocab_id = vocab_entry['id']

        # 2. Thêm vào UserVocab với next_review là thời gian hiện tại để ưu tiên
        add_word_to_srs(user_id, vocab_id)

        return vocab_id

    except Exception as e:
        print(f"Error prioritizing word: {e}")
        return None

def mark_learned(user_id, vocab_id):
    """Đánh dấu từ đã thuộc (Mastered) thủ công."""
    if not supabase: return False
    try:
        supabase.table("UserVocabulary").update({
            "status": "mastered",
            "streak": 10,
            "interval": 30,
            "due_date": (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) + timedelta(days=30)).isoformat()
        }).eq("user_id", int(user_id)).eq("vocab_id", vocab_id).execute()
        
        # Security Monitor: Log action
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'vocab_learn', success=True, metadata={'vocab_id': vocab_id, 'action': 'mark_learned'})
        except Exception:
            pass  # Fail silently if security monitor not available
        
        return True
    except Exception as e:
        # Security Monitor: Log failed action
        try:
            from core.security_monitor import SecurityMonitor
            SecurityMonitor.log_user_action(user_id, 'vocab_learn', success=False, metadata={'vocab_id': vocab_id, 'error': str(e)})
        except Exception:
            pass
        return False

def remove_word_from_srs(user_id, vocab_id):
    """Xóa từ khỏi lộ trình học (Reset)."""
    if not supabase: return False
    try:
        supabase.table("UserVocabulary").delete().eq("user_id", int(user_id)).eq("vocab_id", vocab_id).execute()
        return True
    except: return False

def get_daily_learning_batch(user_id: int, target_level: str = 'A1', limit: int = 10, topic: str = "General") -> List[Dict[str, Any]]:
    """
    Lấy danh sách từ mới để học hôm nay.
    Ưu tiên từ chưa có trong UserVocab và thuộc level mục tiêu.
    """
    if not supabase: return []
    try:
        # 1. Lấy danh sách ID các từ đã học
        learned_res = supabase.table("UserVocabulary").select("vocab_id").eq("user_id", int(user_id)).execute()
        learned_ids = [item['vocab_id'] for item in learned_res.data] if learned_res.data else []
        
        # 2. Query bảng Vocabulary
        query = supabase.table("Vocabulary").select("*").eq("level", target_level)
        
        if topic and topic != "General":
            query = query.ilike("topic", f"%{topic}%")
        
        if learned_ids:
            query = query.not_.in_("id", learned_ids)
            
        res = query.limit(limit).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Error getting daily batch: {e}")
        return []

def bulk_master_levels(user_id, levels):
    """
    Đánh dấu toàn bộ từ vựng thuộc các level trong danh sách là đã thuộc (Mastered).
    Dùng cho tính năng kiểm tra đầu vào (Placement Test).
    """
    if not supabase or not levels: return False
    try:
        # 1. Lấy danh sách ID từ vựng của các level này
        vocab_res = supabase.table("Vocabulary").select("id").in_("level", levels).execute()
        vocab_ids = [item['id'] for item in vocab_res.data] if vocab_res.data else []
        
        if not vocab_ids: return True
        
        # 2. Chuẩn bị dữ liệu upsert
        # Mastered: streak=10, interval=30, next_review=now+30days
        now_utc = datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00'))
        next_rev = (now_utc + timedelta(days=30)).isoformat()
        now = get_vn_now_utc()
        
        records = []
        for vid in vocab_ids:
            records.append({
                "user_id": int(user_id),
                "vocab_id": vid,
                "status": "mastered",
                "streak": 10,
                "interval": 30,
                "ease_factor": 2.5,
                "due_date": next_rev,
                "last_reviewed_at": now
            })
            
        # 3. Thực hiện Upsert (Batch) để tránh lỗi request quá lớn
        chunk_size = 1000
        for i in range(0, len(records), chunk_size):
            batch = records[i:i + chunk_size]
            supabase.table("UserVocabulary").upsert(batch, on_conflict="user_id, vocab_id").execute()
            
        return True
    except Exception as e:
        print(f"Error bulk mastering levels: {e}")
        return False

def get_irregular_verbs_list():
    """Trả về danh sách động từ bất quy tắc phổ biến (Static Data)."""
    return [
        {"base": "be", "v2": "was/were", "v3": "been", "meaning": "thì, là, ở", "group": "ABC"},
        {"base": "become", "v2": "became", "v3": "become", "meaning": "trở thành", "group": "ABA"},
        {"base": "begin", "v2": "began", "v3": "begun", "meaning": "bắt đầu", "group": "ABC"},
        {"base": "break", "v2": "broke", "v3": "broken", "meaning": "làm vỡ", "group": "ABC"},
        {"base": "bring", "v2": "brought", "v3": "brought", "meaning": "mang đến", "group": "ABB"},
        {"base": "build", "v2": "built", "v3": "built", "meaning": "xây dựng", "group": "ABB"},
        {"base": "buy", "v2": "bought", "v3": "bought", "meaning": "mua", "group": "ABB"},
        {"base": "catch", "v2": "caught", "v3": "caught", "meaning": "bắt, chụp", "group": "ABB"},
        {"base": "choose", "v2": "chose", "v3": "chosen", "meaning": "chọn", "group": "ABC"},
        {"base": "come", "v2": "came", "v3": "come", "meaning": "đến", "group": "ABA"},
        {"base": "cost", "v2": "cost", "v3": "cost", "meaning": "trị giá", "group": "AAA"},
        {"base": "cut", "v2": "cut", "v3": "cut", "meaning": "cắt", "group": "AAA"},
        {"base": "do", "v2": "did", "v3": "done", "meaning": "làm", "group": "ABC"},
        {"base": "draw", "v2": "drew", "v3": "drawn", "meaning": "vẽ", "group": "ABC"},
        {"base": "drink", "v2": "drank", "v3": "drunk", "meaning": "uống", "group": "ABC"},
        {"base": "drive", "v2": "drove", "v3": "driven", "meaning": "lái xe", "group": "ABC"},
        {"base": "eat", "v2": "ate", "v3": "eaten", "meaning": "ăn", "group": "ABC"},
        {"base": "fall", "v2": "fell", "v3": "fallen", "meaning": "ngã", "group": "ABC"},
        {"base": "feel", "v2": "felt", "v3": "felt", "meaning": "cảm thấy", "group": "ABB"},
        {"base": "find", "v2": "found", "v3": "found", "meaning": "tìm thấy", "group": "ABB"},
        {"base": "fly", "v2": "flew", "v3": "flown", "meaning": "bay", "group": "ABC"},
        {"base": "forget", "v2": "forgot", "v3": "forgotten", "meaning": "quên", "group": "ABC"},
        {"base": "get", "v2": "got", "v3": "got", "meaning": "nhận được", "group": "ABB"},
        {"base": "give", "v2": "gave", "v3": "given", "meaning": "cho", "group": "ABC"},
        {"base": "go", "v2": "went", "v3": "gone", "meaning": "đi", "group": "ABC"},
        {"base": "grow", "v2": "grew", "v3": "grown", "meaning": "lớn lên", "group": "ABC"},
        {"base": "have", "v2": "had", "v3": "had", "meaning": "có", "group": "ABB"},
        {"base": "hear", "v2": "heard", "v3": "heard", "meaning": "nghe", "group": "ABB"},
        {"base": "keep", "v2": "kept", "v3": "kept", "meaning": "giữ", "group": "ABB"},
        {"base": "know", "v2": "knew", "v3": "known", "meaning": "biết", "group": "ABC"},
        {"base": "leave", "v2": "left", "v3": "left", "meaning": "rời đi", "group": "ABB"},
        {"base": "make", "v2": "made", "v3": "made", "meaning": "làm", "group": "ABB"},
        {"base": "meet", "v2": "met", "v3": "met", "meaning": "gặp", "group": "ABB"},
        {"base": "pay", "v2": "paid", "v3": "paid", "meaning": "trả tiền", "group": "ABB"},
        {"base": "put", "v2": "put", "v3": "put", "meaning": "đặt", "group": "AAA"},
        {"base": "read", "v2": "read", "v3": "read", "meaning": "đọc", "group": "AAA"},
        {"base": "run", "v2": "ran", "v3": "run", "meaning": "chạy", "group": "ABA"},
        {"base": "say", "v2": "said", "v3": "said", "meaning": "nói", "group": "ABB"},
        {"base": "see", "v2": "saw", "v3": "seen", "meaning": "thấy", "group": "ABC"},
        {"base": "sell", "v2": "sold", "v3": "sold", "meaning": "bán", "group": "ABB"},
        {"base": "send", "v2": "sent", "v3": "sent", "meaning": "gửi", "group": "ABB"},
        {"base": "speak", "v2": "spoke", "v3": "spoken", "meaning": "nói", "group": "ABC"},
        {"base": "spend", "v2": "spent", "v3": "spent", "meaning": "tiêu xài", "group": "ABB"},
        {"base": "take", "v2": "took", "v3": "taken", "meaning": "cầm, lấy", "group": "ABC"},
        {"base": "teach", "v2": "taught", "v3": "taught", "meaning": "dạy", "group": "ABB"},
        {"base": "tell", "v2": "told", "v3": "told", "meaning": "kể", "group": "ABB"},
        {"base": "think", "v2": "thought", "v3": "thought", "meaning": "nghĩ", "group": "ABB"},
        {"base": "understand", "v2": "understood", "v3": "understood", "meaning": "hiểu", "group": "ABB"},
        {"base": "write", "v2": "wrote", "v3": "written", "meaning": "viết", "group": "ABC"}
    ]

@st.cache_data(ttl=60, show_spinner=False)  # Cache 60s - level progress changes infrequently
def get_user_level_progress(user_id: int) -> Dict[str, Dict[str, int]]:
    """
    Lấy tiến độ học theo level của user.
    Trả về dict: {level: {total: int, learned: int}}
    Cached for 60 seconds to improve performance.
    """
    if not supabase or not user_id: return {}
    
    try:
        # Try RPC first
        res = supabase.rpc('get_user_level_progress', {'p_user_id': int(user_id)}).execute()
        level_progress = {}
        
        if res.data:
            for item in res.data:
                try:
                    # RPC có thể trả về 'level' hoặc 'lvl', xử lý cả hai
                    level_key = item.get('lvl') or item.get('level')
                    if not level_key:
                        logger.warning(f"Missing level key in item: {item}")
                        continue
                    level_progress[level_key] = {
                        'total': item.get('total_count', item.get('total', item.get('total_words', 0))), 
                        'learned': item.get('learned_count', item.get('learned', item.get('learned_words', 0)))
                    }
                except Exception as e:
                    logger.warning(f"Error processing level progress item: {e}, item: {item}")
                    continue
            return level_progress
        
        # If RPC returns empty, fallback to direct query
        logger.warning("RPC returned empty, using fallback query")
        from core.config import LEVELS
        
        for level in LEVELS:
            # Get total vocab for this level
            total_res = supabase.table('Vocabulary').select('id', count='exact').eq('level', level).execute()
            total_count = total_res.count if total_res.count else 0
            
            # Get learned vocab (status = mastered)
            learned_res = supabase.table('UserVocabulary')\
                .select('vocab_id', count='exact')\
                .eq('user_id', user_id)\
                .eq('status', 'mastered')\
                .execute()
            
            # Get vocab IDs that are learned
            learned_vocab_ids = [item['vocab_id'] for item in (learned_res.data or [])]
            
            # Count how many of those are in this level
            if learned_vocab_ids:
                level_learned_res = supabase.table('Vocabulary')\
                    .select('id', count='exact')\
                    .eq('level', level)\
                    .in_('id', learned_vocab_ids)\
                    .execute()
                learned_count = level_learned_res.count if level_learned_res.count else 0
            else:
                learned_count = 0
            
            level_progress[level] = {
                'total': total_count,
                'learned': learned_count
            }
        
        return level_progress
        
    except Exception as e:
        logger.error(f"Error getting level progress: {e}")
        # Return empty progress for all levels
        from core.config import LEVELS
        return {lvl: {'total': 0, 'learned': 0} for lvl in LEVELS}

"""
AI Cache Service - Cache AI responses để giảm chi phí API
"""
import hashlib
import json
from typing import Optional, Dict, Any
from core.database import supabase
from core.timezone_utils import get_vn_now_utc
import logging

logger = logging.getLogger(__name__)

def generate_cache_key(prompt: str, feature_type: str = 'general') -> str:
    """
    Tạo cache key từ prompt và feature_type
    
    Args:
        prompt: Prompt text
        feature_type: Loại feature (listening, speaking, reading, writing, etc.)
    
    Returns:
        str: MD5 hash của prompt + feature_type
    """
    combined = f"{feature_type}:{prompt}".encode('utf-8')
    return hashlib.md5(combined).hexdigest()

def get_cached_response(prompt: str, feature_type: str = 'general') -> Optional[Dict[str, Any]]:
    """
    Lấy cached response từ database
    
    Returns:
        Dict với keys: 'response', 'hit_count' hoặc None nếu không có cache
    """
    if not supabase:
        return None
    
    try:
        cache_key = generate_cache_key(prompt, feature_type)
        
        # Select only needed columns to avoid 406 errors
        result = supabase.table("AICache").select("id,response,hit_count").eq("cache_key", cache_key).maybe_single().execute()
        
        if result.data:
            # Update hit_count and last_used_at
            try:
                supabase.table("AICache").update({
                    "hit_count": result.data.get('hit_count', 1) + 1,
                    "last_used_at": get_vn_now_utc()
                }).eq("id", result.data['id']).execute()
            except Exception as e:
                logger.warning(f"Failed to update cache hit count: {e}")
            
            return {
                'response': result.data.get('response'),
                'hit_count': result.data.get('hit_count', 1)
            }
    except Exception as e:
        logger.debug(f"Cache lookup error (non-critical): {e}")
    
    return None

def cache_response(prompt: str, response: Any, feature_type: str = 'general') -> bool:
    """
    Lưu response vào cache
    
    Args:
        prompt: Prompt text
        response: Response data (sẽ được convert sang JSONB)
        feature_type: Loại feature
    
    Returns:
        bool: True nếu cache thành công
    """
    if not supabase:
        return False
    
    try:
        cache_key = generate_cache_key(prompt, feature_type)
        prompt_hash = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        
        # Convert response to JSON-compatible format
        try:
            if isinstance(response, str):
                # Try to parse as JSON first
                try:
                    response_json = json.loads(response)
                except:
                    response_json = {"text": response}
            else:
                response_json = response if isinstance(response, dict) else {"data": response}
        except:
            response_json = {"text": str(response)}
        
        # Upsert cache entry
        supabase.table("AICache").upsert({
            "cache_key": cache_key,
            "feature_type": feature_type,
            "prompt_hash": prompt_hash,
            "response": response_json,
            "hit_count": 1,
            "last_used_at": get_vn_now_utc()
        }, on_conflict="cache_key").execute()
        
        return True
    except Exception as e:
        # Log error but don't fail - caching is not critical
        error_msg = str(e)
        # Only log if it's not an RLS error (to reduce noise)
        if 'row-level security' not in error_msg.lower() and '42501' not in error_msg:
            logger.warning(f"Failed to cache response: {e}")
        return False

def clear_old_cache(days_old: int = 30) -> int:
    """
    Xóa cache cũ hơn N ngày (maintenance function)
    
    Returns:
        int: Số lượng entries đã xóa
    """
    if not supabase:
        return 0
    
    try:
        from datetime import datetime, timedelta
        from core.timezone_utils import get_vn_now_utc
        cutoff_date = (datetime.fromisoformat(get_vn_now_utc().replace('Z', '+00:00')) - timedelta(days=days_old)).isoformat()
        
        result = supabase.table("AICache").delete().lt("last_used_at", cutoff_date).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        logger.error(f"Failed to clear old cache: {e}")
        return 0

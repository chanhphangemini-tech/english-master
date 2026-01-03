"""
TTS Audio Cache Service
Service để cache TTS audio files trong Supabase Storage
"""
import hashlib
import logging
from typing import Optional, Tuple, Dict, Any
from core.database import supabase
from core.timezone_utils import get_vn_now_utc

logger = logging.getLogger(__name__)

BUCKET_NAME = "tts-audio"

def generate_text_hash(text: str, voice: str) -> str:
    """
    Generate MD5 hash từ text + voice.
    
    Args:
        text: Text cần hash
        voice: Voice name (e.g., 'en-US-AriaNeural')
    
    Returns:
        MD5 hash string
    """
    combined = f"{text}|{voice}".encode('utf-8')
    return hashlib.md5(combined).hexdigest()

def get_cached_audio_url(text: str, voice: str = "en-US-AriaNeural") -> Optional[str]:
    """
    Chỉ lấy file_url từ cache (không download bytes) - nhanh hơn nhiều.
    Dùng khi chỉ cần URL để hiển thị audio player.
    
    Args:
        text: Text cần audio
        voice: Voice name
    
    Returns:
        file_url string hoặc None nếu không có cache
    """
    if not supabase or not text or not text.strip():
        return None
    
    try:
        text_hash = generate_text_hash(text, voice)
        
        # Query cache metadata (chỉ lấy URL, không download file)
        result = supabase.table("TTSAudioCache").select(
            "file_url, text_hash"
        ).eq("text_hash", text_hash).maybe_single().execute()
        
        # Check if result exists and has data
        if result and hasattr(result, 'data') and result.data:
            file_url = result.data.get('file_url')
            if file_url:
                return file_url
        
        return None
        
    except Exception as e:
        # Log error but don't fail - this is a cache lookup, not critical
        error_msg = str(e)
        # Only log if it's not a 406 (RLS policy issue) to reduce noise
        if '406' not in error_msg and 'Not Acceptable' not in error_msg:
            logger.error(f"Error getting cached audio URL: {e}")
        return None

def get_cached_audio(text: str, voice: str = "en-US-AriaNeural") -> Optional[Tuple[bytes, str]]:
    """
    Lấy cached audio từ database và Supabase Storage.
    
    Args:
        text: Text cần audio
        voice: Voice name
    
    Returns:
        Tuple (audio_bytes, file_url) hoặc None nếu không có cache
    """
    if not supabase or not text or not text.strip():
        return None
    
    try:
        text_hash = generate_text_hash(text, voice)
        
        # Query cache metadata
        result = supabase.table("TTSAudioCache").select(
            "file_path, file_url, text_hash"
        ).eq("text_hash", text_hash).maybe_single().execute()
        
        # Check if result exists and has data
        if not result or not hasattr(result, 'data') or not result.data:
            return None
        
        file_path = result.data.get('file_path')
        file_url = result.data.get('file_url')
        
        if not file_path:
            logger.warning(f"Cache entry found but file_path is missing for hash {text_hash}")
            return None
        
        # Download file from Supabase Storage
        try:
            audio_response = supabase.storage.from_(BUCKET_NAME).download(file_path)
            
            if audio_response:
                # Update usage_count and last_used_at using RPC function
                try:
                    # Get current usage_count first
                    current = supabase.table("TTSAudioCache").select("usage_count").eq("text_hash", text_hash).maybe_single().execute()
                    current_count = 0
                    if current and hasattr(current, 'data') and current.data:
                        current_count = current.data.get('usage_count', 0)
                    
                    new_count = current_count + 1
                    rpc_result = supabase.rpc('update_tts_cache_usage_count', {
                        'p_text_hash': text_hash,
                        'p_usage_count': new_count,
                        'p_last_used_at': get_vn_now_utc()
                    }).execute()
                    
                    # If RPC fails, try direct update as fallback
                    if not rpc_result.data or (isinstance(rpc_result.data, str) and rpc_result.data.startswith('ERROR:')):
                        logger.debug(f"RPC update failed, trying direct: {rpc_result.data}")
                        supabase.table("TTSAudioCache").update({
                            "usage_count": new_count,
                            "last_used_at": get_vn_now_utc()
                        }).eq("text_hash", text_hash).execute()
                except Exception as e:
                    # Silently fail - updating usage count is not critical
                    logger.debug(f"Failed to update cache usage: {e}")
                
                return (audio_response, file_url or "")
            
        except Exception as e:
            logger.warning(f"Failed to download audio from Storage: {e}")
            # File might not exist, but cache entry exists
            # Return None to trigger regeneration
            return None
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached audio: {e}")
        return None

def cache_audio(
    text: str,
    voice: str,
    audio_bytes: bytes,
    audio_length_seconds: Optional[int] = None
) -> Optional[str]:
    """
    Lưu audio vào Supabase Storage và metadata vào database.
    
    Args:
        text: Text đã được convert sang audio
        voice: Voice name được sử dụng
        audio_bytes: Audio bytes data
        audio_length_seconds: Length của audio (optional)
    
    Returns:
        file_url nếu thành công, None nếu thất bại
    """
    if not supabase or not text or not text.strip() or not audio_bytes:
        return None
    
    try:
        text_hash = generate_text_hash(text, voice)
        file_path = f"{text_hash}.mp3"
        
        # Upload to Storage
        upload_result = supabase.storage.from_(BUCKET_NAME).upload(
            file_path,
            audio_bytes,
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )
        
        if not upload_result:
            logger.warning(f"Failed to upload audio to Storage for hash {text_hash}")
            return None
        
        # Get public URL
        public_url_result = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        file_url = public_url_result if isinstance(public_url_result, str) else None
        
        # If no public URL, construct it manually
        if not file_url:
            # Supabase Storage public URL format
            project_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
            if isinstance(project_url, str):
                file_url = project_url
            else:
                # Fallback: construct URL manually
                # This is a workaround - should get from storage API
                logger.warning(f"Could not get public URL for {file_path}, using manual construction")
                # Note: This might not work in all cases, but is a fallback
                file_url = f"/storage/v1/object/public/{BUCKET_NAME}/{file_path}"
        
        # Insert/Update cache metadata
        cache_data = {
            "text_hash": text_hash,
            "text": text[:500],  # Limit text length
            "voice": voice,
            "file_path": file_path,
            "file_url": file_url,
            "file_size_bytes": len(audio_bytes),
            "audio_length_seconds": audio_length_seconds,
            "usage_count": 1,
            "last_used_at": get_vn_now_utc(),
            "created_at": get_vn_now_utc()
        }
        
        # Upsert cache entry using RPC function to bypass RLS
        try:
            result = supabase.rpc('upsert_tts_audio_cache', {
                'p_text_hash': text_hash,
                'p_text': text[:500],  # Limit text length
                'p_voice': voice,
                'p_file_path': file_path,
                'p_file_url': file_url,
                'p_file_size_bytes': len(audio_bytes),
                'p_audio_length_seconds': audio_length_seconds,
                'p_usage_count': 1,
                'p_last_used_at': get_vn_now_utc()
            }).execute()
            
            # Check if RPC call was successful
            if result.data and isinstance(result.data, str):
                if result.data.startswith('SUCCESS:'):
                    logger.info(f"Cached audio for text hash {text_hash}")
                    return file_url
                else:
                    logger.warning(f"RPC returned error: {result.data}")
                    # Fallback to direct upsert
                    supabase.table("TTSAudioCache").upsert(
                        cache_data,
                        on_conflict="text_hash"
                    ).execute()
                    return file_url
            else:
                logger.info(f"Cached audio for text hash {text_hash}")
                return file_url
        except Exception as rpc_error:
            # Fallback to direct upsert if RPC fails
            logger.debug(f"RPC upsert failed, trying direct: {rpc_error}")
            try:
                supabase.table("TTSAudioCache").upsert(
                    cache_data,
                    on_conflict="text_hash"
                ).execute()
                logger.info(f"Cached audio for text hash {text_hash} via direct upsert")
                return file_url
            except Exception as fallback_error:
                # Direct upsert also failed (likely RLS) - this is expected
                # Cache failure is non-critical - audio was already uploaded to Storage
                logger.debug(f"Direct upsert also failed (non-critical): {fallback_error}")
                # Return file_url anyway since upload to Storage succeeded
                return file_url
        
    except Exception as e:
        # Log error but don't fail - cache is optimization, not critical
        error_msg = str(e)
        # Check if it's an RLS error (expected in some cases)
        if 'row-level security policy' in error_msg or '403' in error_msg or 'Unauthorized' in error_msg:
            logger.debug(f"Cache error (non-critical, RLS): {e}")
        else:
            logger.warning(f"Error caching audio (non-critical): {e}")
        # Return file_url if we have it (upload to Storage might have succeeded)
        # Otherwise return None (caller will handle it)
        return file_url if 'file_url' in locals() and file_url else None

def verify_audio_exists(text_hash: str) -> bool:
    """
    Verify xem audio file có tồn tại trong Storage không.
    
    Args:
        text_hash: Text hash để check
    
    Returns:
        True nếu file exists, False nếu không
    """
    if not supabase:
        return False
    
    try:
        file_path = f"{text_hash}.mp3"
        # Try to get file info (this will fail if file doesn't exist)
        files = supabase.storage.from_(BUCKET_NAME).list(file_path)
        return bool(files)
    except Exception:
        return False

def get_cache_stats() -> Dict[str, Any]:
    """
    Lấy thống kê về cache.
    
    Returns:
        Dict với các thống kê về cache
    """
    if not supabase:
        return {}
    
    try:
        # Get total count
        count_result = supabase.table("TTSAudioCache").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get total size (approximate)
        size_result = supabase.table("TTSAudioCache").select("file_size_bytes").execute()
        total_size = sum(item.get('file_size_bytes', 0) for item in (size_result.data or []))
        
        return {
            "total_entries": total_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {}

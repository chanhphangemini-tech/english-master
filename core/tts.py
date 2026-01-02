import edge_tts
import asyncio
import streamlit as st

async def text_to_speech(text, voice="en-US-AriaNeural", max_retries=3, use_cache=True):
    """
    Chuyển đổi văn bản thành âm thanh sử dụng Edge TTS.
    Voice mặc định: en-US-AriaNeural (Giọng nữ Mỹ tự nhiên).
    Các giọng khác: en-GB-SoniaNeural (Anh), en-US-GuyNeural (Nam Mỹ).
    
    Edge TTS có giới hạn ~5000 ký tự mỗi request. Nếu text quá dài, sẽ tự động chia nhỏ.
    
    Args:
        text: Text to convert to speech
        voice: Voice name (default: en-US-AriaNeural)
        max_retries: Maximum retry attempts
        use_cache: Whether to use DB cache (default: True)
    """
    if not text or not text.strip():
        return None
    
    # Check cache first (if enabled)
    if use_cache:
        try:
            from services.tts_cache_service import get_cached_audio
            cached_result = get_cached_audio(text, voice)
            if cached_result:
                audio_bytes, file_url = cached_result
                if audio_bytes:
                    return audio_bytes
        except Exception as e:
            # If cache check fails, continue to generate new audio
            pass
    
    async def _try_communicate(text_chunk, voice_name, retry_count=0):
        """Try to get audio with retry logic"""
        import asyncio
        try:
            communicate = edge_tts.Communicate(text_chunk, voice_name)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            if audio_data and len(audio_data) > 0:
                return audio_data
            else:
                # Empty audio - retry if possible
                if retry_count < max_retries:
                    await asyncio.sleep(0.5 * (retry_count + 1))  # Exponential backoff
                    return await _try_communicate(text_chunk, voice_name, retry_count + 1)
                return None
        except Exception as e:
            error_msg = str(e)
            # Retry on specific errors
            if retry_count < max_retries and ("No audio" in error_msg or "timeout" in error_msg.lower() or "rate" in error_msg.lower()):
                await asyncio.sleep(1.0 * (retry_count + 1))  # Exponential backoff
                return await _try_communicate(text_chunk, voice_name, retry_count + 1)
            print(f"TTS Error: {e}")
            return None
    
    try:
        # Edge TTS có giới hạn ~5000 ký tự, chia nhỏ nếu cần
        max_length = 4000  # An toàn hơn để tránh lỗi
        if len(text) > max_length:
            # Chia text thành các đoạn nhỏ hơn tại dấu câu
            import re
            sentences = re.split(r'([.!?]\s+)', text)
            chunks = []
            current_chunk = ""
            
            for i in range(0, len(sentences), 2):
                sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
                if len(current_chunk) + len(sentence) <= max_length:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            if current_chunk:
                chunks.append(current_chunk)
            
            # Tạo audio cho từng chunk và ghép lại
            audio_data = b""
            for chunk_text in chunks:
                chunk_audio = await _try_communicate(chunk_text, voice)
                if chunk_audio:
                    audio_data += chunk_audio
                # Add small delay between chunks to avoid rate limiting
                await asyncio.sleep(0.1)
            final_audio = audio_data if audio_data else None
        else:
            # Text ngắn, xử lý bình thường với retry
            final_audio = await _try_communicate(text, voice)
        
        # Save to cache if audio was generated and caching is enabled
        if final_audio and use_cache:
            try:
                from services.tts_cache_service import cache_audio
                # Calculate audio length (approximate, assuming ~16KB/s for MP3)
                audio_length_seconds = len(final_audio) // 16000 if len(final_audio) > 0 else None
                cache_audio(text, voice, final_audio, audio_length_seconds)
            except Exception as e:
                # Cache save failure is non-critical, just log and continue
                pass
        
        return final_audio
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def get_tts_audio(text, voice="en-US-AriaNeural"):
    """
    Hàm wrapper đồng bộ để gọi TTS an toàn trong Streamlit.
    Tự động xử lý Event Loop và sử dụng DB cache (TTSAudioCache).
    Cache is handled by text_to_speech() internally.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(text_to_speech(text, voice, use_cache=True))

def get_tts_audio_no_cache(text, voice="en-US-AriaNeural"):
    """
    Hàm tạo TTS audio KHÔNG dùng cache - dùng cho podcast để đảm bảo audio đầy đủ.
    Note: This function does NOT use DB cache or Streamlit cache.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(text_to_speech(text, voice, use_cache=False))
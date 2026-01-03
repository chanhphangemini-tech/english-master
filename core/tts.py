import edge_tts
import asyncio
import streamlit as st
import re
import io

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

async def text_to_speech_dialogue(script, voice1="en-US-GuyNeural", voice2="en-US-AriaNeural", use_cache=True):
    """
    Tạo audio cho dialogue/conversation với 2 giọng khác nhau.
    
    Format script có thể là:
    - "Speaker 1: Hello. Speaker 2: Hi there."
    - "A: Hello. B: Hi there."
    - "Male: Hello. Female: Hi there."
    - Hoặc format tự nhiên với newline giữa các câu
    
    Args:
        script: Dialogue script text
        voice1: Voice cho speaker đầu tiên (default: en-US-GuyNeural - Nam Mỹ)
        voice2: Voice cho speaker thứ hai (default: en-US-AriaNeural - Nữ Mỹ)
        use_cache: Whether to use cache
    
    Returns:
        bytes: Audio data (MP3 format)
    """
    if not script or not script.strip():
        return None
    
    # Check cache first
    cache_key = f"dialogue_{script[:100]}_{voice1}_{voice2}"
    if use_cache:
        try:
            from services.tts_cache_service import get_cached_audio
            cached_result = get_cached_audio(cache_key, voice1)  # Use voice1 as cache key
            if cached_result:
                audio_bytes, file_url = cached_result
                if audio_bytes:
                    return audio_bytes
        except Exception as e:
            pass
    
    # Parse script to extract dialogue parts
    # Try multiple patterns to match different formats
    dialogue_parts = []
    
    # Common male and female names for gender detection
    male_names = ['mark', 'ben', 'john', 'mike', 'david', 'tom', 'james', 'robert', 'william', 'richard', 'joe', 'chris', 'daniel', 'michael', 'peter', 'paul', 'steve', 'bob']
    female_names = ['sarah', 'anna', 'anna', 'emily', 'lisa', 'mary', 'jane', 'linda', 'susan', 'karen', 'nancy', 'betty', 'helen', 'sandra', 'donna', 'carol', 'michelle', 'laura', 'amy']
    
    # Pattern 1: Match explicit speaker labels (Speaker 1/2, A/B, names, etc.)
    pattern1 = r'([A-Za-z\s]+?):\s*(.+?)(?=[A-Za-z\s]+?:|$)'
    matches1 = list(re.finditer(pattern1, script, re.IGNORECASE | re.DOTALL))
    
    if len(matches1) >= 2:  # At least 2 speakers found
        for i, match in enumerate(matches1):
            # Extract speaker label and text
            full_match = match.group(0)
            if ':' in full_match:
                parts = full_match.split(':', 1)
                speaker_label = parts[0].strip()
                text = parts[1].strip()
            else:
                continue
            
            if text:
                # Determine which voice to use based on speaker label
                label_lower = speaker_label.lower()
                
                # Check for explicit gender keywords
                if any(keyword in label_lower for keyword in ['male', 'man', 'guy', 'boy']):
                    voice = voice1  # Male voice
                elif any(keyword in label_lower for keyword in ['female', 'woman', 'lady', 'girl']):
                    voice = voice2  # Female voice
                # Check for common names
                elif any(name in label_lower for name in male_names):
                    voice = voice1  # Male voice
                elif any(name in label_lower for name in female_names):
                    voice = voice2  # Female voice
                # Check for numeric/letter labels (Speaker 1, A, etc.)
                elif any(keyword in label_lower for keyword in ['1', 'a']) and 'speaker' in label_lower:
                    voice = voice1  # Speaker 1/A typically male
                elif any(keyword in label_lower for keyword in ['2', 'b']) and 'speaker' in label_lower:
                    voice = voice2  # Speaker 2/B typically female
                else:
                    # Alternate based on index as fallback
                    voice = voice1 if i % 2 == 0 else voice2
                dialogue_parts.append((text, voice))
    
    # If pattern matching didn't work, try splitting by sentences (fallback)
    if not dialogue_parts:
        # Split by sentence endings (. ! ?) to create dialogue turns
        # This handles plain text conversations without explicit labels
        sentences = re.split(r'([.!?]\s+)', script)
        # Recombine sentences with their punctuation
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        # Filter out empty sentences
        combined_sentences = [s.strip() for s in combined_sentences if s.strip()]
        
        if len(combined_sentences) >= 2:
            # Alternate voices for each sentence
            for i, sentence in enumerate(combined_sentences):
                # Remove any speaker labels if present
                text = re.sub(r'^(?:Speaker\s*[12]|Person\s*[12]|A|B|Male|Female|Man|Woman|Ben|Anna):\s*', '', sentence, flags=re.IGNORECASE).strip()
                if text:
                    voice = voice1 if i % 2 == 0 else voice2
                    dialogue_parts.append((text, voice))
        elif len(combined_sentences) == 1:
            # Single sentence - try to split by comma or and/or
            text = combined_sentences[0]
            # Remove any speaker labels
            text = re.sub(r'^(?:Speaker\s*[12]|Person\s*[12]|A|B|Male|Female|Man|Woman|Ben|Anna):\s*', '', text, flags=re.IGNORECASE).strip()
            # Split by common conjunctions
            parts = re.split(r'\s+(and|or|but)\s+', text, flags=re.IGNORECASE)
            if len(parts) >= 3:  # At least 2 parts with conjunction
                for i, part in enumerate(parts):
                    if part.strip() and part.lower() not in ['and', 'or', 'but']:
                        voice = voice1 if i % 2 == 0 else voice2
                        dialogue_parts.append((part.strip(), voice))
            else:
                # Can't split further - use single voice
                dialogue_parts.append((text, voice1))
        else:
            # No sentences found - use whole script with single voice
            text = script.strip()
            text = re.sub(r'^(?:Speaker\s*[12]|Person\s*[12]|A|B|Male|Female|Man|Woman|Ben|Anna):\s*', '', text, flags=re.IGNORECASE).strip()
            if text:
                dialogue_parts.append((text, voice1))
    
    # Final fallback: if still no parts, use whole script with voice1
    if not dialogue_parts:
        text = script.strip()
        text = re.sub(r'^(?:Speaker\s*[12]|Person\s*[12]|A|B|Male|Female|Man|Woman|Ben|Anna):\s*', '', text, flags=re.IGNORECASE).strip()
        if text:
            dialogue_parts.append((text, voice1))
    
    # Generate audio for each part
    audio_parts = []
    for text, voice in dialogue_parts:
        audio = await text_to_speech(text, voice, use_cache=False)  # Don't cache individual parts
        if audio:
            audio_parts.append(audio)
            # Small pause between speakers (add silence - 0.3 seconds of silence)
            # Edge TTS audio is MP3, we can't easily add silence without pydub
            # So we'll just concatenate directly - the natural pause in speech should be enough
            await asyncio.sleep(0.1)  # Small delay to avoid rate limiting
    
    # Concatenate all audio parts
    if audio_parts:
        final_audio = b"".join(audio_parts)
        
        # Cache the result
        if use_cache and final_audio:
            try:
                from services.tts_cache_service import cache_audio
                audio_length_seconds = len(final_audio) // 16000 if len(final_audio) > 0 else None
                cache_audio(cache_key, voice1, final_audio, audio_length_seconds)
            except Exception as e:
                pass
        
        return final_audio
    
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

def get_tts_dialogue_audio(script, voice1="en-US-GuyNeural", voice2="en-US-AriaNeural"):
    """
    Hàm wrapper đồng bộ để tạo dialogue audio với 2 giọng.
    
    Args:
        script: Dialogue script text (có thể có format "Speaker 1: ... Speaker 2: ..." hoặc tự nhiên)
        voice1: Voice cho speaker đầu tiên (default: en-US-GuyNeural - Nam Mỹ)
        voice2: Voice cho speaker thứ hai (default: en-US-AriaNeural - Nữ Mỹ)
    
    Returns:
        bytes: Audio data (MP3 format)
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(text_to_speech_dialogue(script, voice1, voice2, use_cache=True))

# core/llm.py
import time
import streamlit as st
import json
import logging
import re
import os
import random
from datetime import datetime, timedelta

# Thư viện đúng cho google-genai mới
try:
    from google import genai
    from google.genai import types # Import thêm types để xử lý lỗi kỹ hơn nếu cần
except ImportError:
    st.error("⚠️ Thư viện `google-genai` chưa được cài đặt. Vui lòng chạy: `pip install google-genai`")
    raise

# Cấu hình log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. SESSION MANAGEMENT ---
def check_session_timeout():
    last_activity = st.session_state.get('last_activity')
    if last_activity:
        if datetime.now() - last_activity > timedelta(hours=2):
            st.session_state.logged_in = False
            st.session_state.user_info = {}
            st.rerun()
    st.session_state.last_activity = datetime.now()

# --- 2. GEMINI CONFIGURATION ---
def _get_gemini_client():
    # Kiểm tra trong session state xem đã có client chưa
    if "gemini_client" in st.session_state and st.session_state.gemini_client:
        return st.session_state.gemini_client

    diag = {"api_key_source": None, "ok": False, "error": None}
    
    # 1. Thử lấy từ st.secrets
    try:
        google_creds = st.secrets.get("google_credentials", {})
        api_key = google_creds.get("google_api_key")
        if api_key:
            diag['api_key_source'] = 'secrets'
    except Exception:
        api_key = None

    # 2. Thử lấy từ biến môi trường
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            diag['api_key_source'] = 'env'

    st.session_state['gemini_diag'] = diag

    if not api_key:
        diag['error'] = 'No API key found.'
        logging.warning('Gemini API key not found in st.secrets or environment variables.')
        return None

    try:
        # Khởi tạo Client (Lưu ý: Chỉ khởi tạo Client, không gọi model ở đây)
        client = genai.Client(api_key=api_key)
        
        # Lưu client vào session_state
        st.session_state.gemini_client = client
        diag['ok'] = True
        return client
    except (genai.types.APIError, Exception) as e: # Catch specific APIError or general Exception
        diag['error'] = str(e)
        logging.error(f'Gemini configuration error: {e}')
        return None

# --- 3. CORE AI CALL ---
def _call_model_text(client, prompt, model_name="gemini-2.5-flash"):
    if client is None:
        return False, 'Client is None'
    try:
        # Cấu hình Safety Settings để tránh bị chặn nội dung (BLOCK_NONE)
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]
        config = types.GenerateContentConfig(safety_settings=safety_settings)

        # CÚ PHÁP ĐÚNG CỦA SDK MỚI: gọi qua client.models
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        text = response.text
        return True, text
    except (genai.types.APIError, Exception) as e: # Catch specific APIError or general Exception
        return False, str(e)

def parse_json_response(raw_text):
    if not raw_text:
        return None
    text = raw_text.strip()
    # Regex để tìm JSON trong markdown code block
    match = re.search(r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        # Regex tìm JSON trần
        match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if match:
            text = match.group(0)
    try:
        return json.loads(text)
    except Exception:
        return None

def generate_response_with_fallback(prompt, fallback_responses=None, max_retries=3, feature_type='general'):
    """
    Generate AI response with caching support.
    
    Args:
        prompt: Prompt text
        fallback_responses: List of fallback responses if AI fails
        max_retries: Maximum retry attempts
        feature_type: Feature type for caching (listening, speaking, reading, writing, general)
    """
    # --- AI Cache: Check cache first ---
    try:
        from services.ai_cache_service import get_cached_response, cache_response
        cached = get_cached_response(prompt, feature_type)
        if cached and cached.get('response'):
            response_data = cached['response']
            # Extract text from cached response
            if isinstance(response_data, dict):
                cached_text = response_data.get('text') or response_data.get('data') or str(response_data)
            else:
                cached_text = str(response_data)
            
            if cached_text and cached_text.strip():
                logger.debug(f"Cache hit for feature_type={feature_type}, hit_count={cached.get('hit_count', 1)}")
                # Don't track usage for cached responses (already counted before)
                return cached_text
    except Exception as e:
        logger.debug(f"Cache check error (non-critical): {e}")
    
    client = _get_gemini_client()
    if not client:
        return random.choice(fallback_responses or ["Lỗi kết nối AI (Không tìm thấy Client)."])

    # --- Security Monitor: Log AI call ---
    try:
        if st.session_state.get('logged_in'):
            user_id = st.session_state.user_info.get('id')
            if user_id:
                from core.security_monitor import SecurityMonitor
                SecurityMonitor.log_user_action(user_id, 'ai_call', success=True, metadata={'prompt_length': len(prompt)})
    except Exception as e:
        logger.debug(f"Security monitor log error (non-critical): {e}")

    # --- DEBUG: Lưu prompt để kiểm tra ---
    st.session_state['last_gemini_prompt'] = prompt

    # Reset lỗi cũ trước khi gọi mới
    if 'last_gemini_error' in st.session_state:
        del st.session_state['last_gemini_error']

    for _ in range(max_retries):
        ok, text = _call_model_text(client, prompt)
        if ok and text and text.strip(): # Check if text is not empty or just whitespace
            # Nếu thành công, xóa lỗi cũ (nếu có do retry) để tránh gây hiểu lầm
            if 'last_gemini_error' in st.session_state: del st.session_state['last_gemini_error']
            
            # --- AI Cache: Save to cache ---
            try:
                from services.ai_cache_service import cache_response
                cache_response(prompt, text, feature_type)
            except Exception as e:
                logger.debug(f"Cache save error (non-critical): {e}")
            
            # Log Premium usage (after successful call)
            try:
                if st.session_state.get('logged_in'):
                    user_id = st.session_state.user_info.get('id')
                    user_plan = st.session_state.user_info.get('plan', 'free')
                    if user_id and user_plan == 'premium':
                        from services.premium_usage_service import track_premium_ai_usage
                        track_premium_ai_usage(user_id, feature_type, success=True, metadata={'prompt_length': len(prompt)})
            except Exception as e:
                logger.debug(f"Premium usage tracking error (non-critical): {e}")
            
            return text
        elif not ok:
            logger.warning(f"Gemini call failed: {text}")
            st.session_state['last_gemini_error'] = text  # <--- Lưu lỗi cụ thể để debug
            # Log failed AI call
            try:
                if st.session_state.get('logged_in'):
                    user_id = st.session_state.user_info.get('id')
                    if user_id:
                        from core.security_monitor import SecurityMonitor
                        SecurityMonitor.log_user_action(user_id, 'ai_call', success=False, metadata={'error': str(text)})
            except:
                pass
        else: # ok is True, but text is empty/whitespace
            logger.warning(f"Gemini call returned empty text for prompt: {prompt[:100]}...")
            st.session_state['last_gemini_error'] = "AI trả về nội dung rỗng (Có thể do Safety Filter chặn)."
        time.sleep(1)
    logger.error(f"All Gemini retries failed for prompt: {prompt[:100]}...") # Fallback after all retries

    return random.choice(fallback_responses or ["Hệ thống AI đang bận."])

# --- 4. CÁC HÀM CHỨC NĂNG CỤ THỂ ---
def generate_grammar_test_questions(level, topic, num_questions=10, allow_local_fallback=False):
    """
    Generate grammar test questions with caching support.
    Tries to get questions from cache first, then generates new ones if needed.
    """
    # Try to get cached questions first
    cached_questions = []
    exercise_ids = []
    
    # Get user_id if logged in
    user_id = None
    if st.session_state.get('logged_in'):
        user_id = st.session_state.user_info.get('id')
    
    # Try to get unseen questions from cache (up to num_questions)
    if user_id:
        try:
            from services.exercise_cache_service import get_unseen_exercise, save_exercise, mark_exercise_seen
            for _ in range(num_questions):
                cached_exercise = get_unseen_exercise(user_id, "grammar_question", level, topic)
                if cached_exercise:
                    exercise_data = cached_exercise.get('exercise_data', {})
                    if exercise_data:  # Ensure it's a valid question
                        cached_questions.append(exercise_data)
                        exercise_ids.append(cached_exercise.get('id'))
                        mark_exercise_seen(user_id, cached_exercise.get('id'))
                else:
                    break  # No more cached questions
        except Exception as e:
            logger.warning(f"Error getting cached grammar questions: {e}")
    
    # Calculate how many questions we still need
    remaining = num_questions - len(cached_questions)
    
    # Generate new questions if needed
    new_questions = []
    if remaining > 0:
        client = _get_gemini_client()
        if not client:
            # If no client and we have some cached questions, return those
            if cached_questions:
                return cached_questions[:num_questions]
            return None

        prompt = f"""
        Create {remaining} multiple-choice grammar questions for level {level} on "{topic}".
        Format: JSON list. Keys: "question", "options" (list of 4), "answer", "explanation" (in Vietnamese).
        Strictly JSON.
        """

        try:
            ok, text = _call_model_text(client, prompt)
            if ok:
                parsed_json = parse_json_response(text)
                if parsed_json and isinstance(parsed_json, list):
                    new_questions = parsed_json
                    # Save new questions to cache
                    if user_id:
                        try:
                            from services.exercise_cache_service import save_exercise, mark_exercise_seen
                            for question in new_questions:
                                exercise_id = save_exercise(
                                    exercise_type="grammar_question",
                                    level=level,
                                    topic=topic,
                                    exercise_data=question,
                                    user_id=user_id
                                )
                                if exercise_id:
                                    mark_exercise_seen(user_id, exercise_id)
                        except Exception as e:
                            logger.warning(f"Error saving grammar questions to cache: {e}")
                else:
                    logger.error(f"Failed to parse JSON from Gemini response for test questions. Raw text: {text[:500]}...")
        except Exception as e:
            logger.error(f"Error generating grammar test questions: {e}")
    
    # Combine cached and new questions
    all_questions = cached_questions + new_questions
    
    # Return up to num_questions
    if all_questions:
        return all_questions[:num_questions]
    
    return None

def get_writing_feedback(topic, user_text, level):
    # Prompt ngắn gọn, súc tích
    prompt = f"Grade this writing (Level {level}) on '{topic}':\n'{user_text}'\nOutput in Vietnamese: Score, Errors, Fixes."
    return generate_response_with_fallback(prompt, ["Không thể chấm bài lúc này."], feature_type='writing')

def generate_vocab_mnemonics(word, meaning):
    prompt = f"Mẹo nhớ từ '{word}' ({meaning}). Trả về JSON: {{'mnemonic': '...', 'story': '...'}}"
    res = generate_response_with_fallback(prompt)
    return parse_json_response(res)

def evaluate_placement_test(inputs):
    """
    Đánh giá bài kiểm tra đầu vào 4 kỹ năng.
    inputs: dict chứa {listening_score, reading_score, writing_text, speaking_transcript}
    """
    prompt = f"""
    Act as a professional IELTS/CEFR Examiner. Evaluate this English Placement Test to determine the student's current level.
    
    DATA:
    1. Listening Score: {inputs.get('listening_score')}/5 (MCQ)
    2. Reading Score: {inputs.get('reading_score')}/5 (MCQ)
    3. Writing Sample: "{inputs.get('writing_text')}"
    4. Speaking Transcript: "{inputs.get('speaking_text')}"

    TASK:
    Analyze vocabulary, grammar, coherence, and comprehension.
    Determine the overall CEFR Level (A1, A2, B1, B2, C1, or C2).
    All analysis and recommendation text MUST be in Vietnamese.
    
    OUTPUT JSON STRICTLY:
    {{
        "overall_level": "B1",
        "skills_analysis": {{ "listening": "Phân tích kỹ năng nghe...", "reading": "Phân tích kỹ năng đọc...", "writing": "Phân tích kỹ năng viết...", "speaking": "Phân tích kỹ năng nói..." }},
        "strengths": "Điểm mạnh của học viên...",
        "weaknesses": "Điểm yếu cần cải thiện...",
        "recommendation": "Lời khuyên cụ thể về lộ trình học tiếp theo."
    }}
    """
    res = generate_response_with_fallback(prompt)
    return parse_json_response(res)
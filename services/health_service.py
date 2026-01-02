import streamlit as st
from core.database import supabase
from core.llm import generate_response_with_fallback
from core.tts import get_tts_audio
import time
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

def check_db_connection():
    """
    Kiểm tra kết nối và khả năng truy vấn cơ sở dữ liệu Supabase.
    Returns: (bool, str, str) -> (status, message, debug_info)
    """
    if not supabase:
        return False, "Lỗi: Biến `supabase` chưa được khởi tạo.", "Supabase Client is None"
    
    start_time = time.time()
    try:
        # Thực hiện một truy vấn đơn giản và nhẹ nhàng để kiểm tra kết nối
        res = supabase.table("Users").select("id", count="exact").limit(1).execute()
        duration = (time.time() - start_time) * 1000
        
        # PostgREST sẽ trả về lỗi nếu có vấn đề, nếu không sẽ có data hoặc count
        if res:
             return True, f"Kết nối ổn định ({duration:.2f} ms)", f"Query OK. Count: {res.count}"
        else:
            return False, "Kết nối thất bại.", "No response data from Supabase"

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        return False, f"Lỗi ngoại lệ ({duration:.2f} ms)", str(e)

def check_ai_service():
    """
    Kiểm tra kết nối và khả năng phản hồi của dịch vụ AI (Gemini).
    Returns: (bool, str, str) -> (status, message, debug_info)
    """
    start_time = time.time()
    try:
        # Gửi một prompt đơn giản để kiểm tra
        prompt = "Say 'OK' in one word."
        response = generate_response_with_fallback(prompt, ["ERROR_AI"])
        duration = (time.time() - start_time) * 1000

        if response and "ok" in response.lower():
            return True, f"AI phản hồi tốt ({duration:.2f} ms)", f"Response: {response}"
        elif response == "ERROR_AI":
            error_detail = st.session_state.get('last_gemini_error', 'Không có chi tiết.')
            return False, "AI gặp lỗi.", error_detail
        else:
            return False, "Phản hồi bất thường.", f"Expected 'OK', got '{response}'"

    except Exception as e:
        duration = (time.time() - start_time) * 1000
        return False, f"Lỗi ngoại lệ ({duration:.2f} ms)", str(e)

def check_storage_service():
    """Kiểm tra kết nối tới Supabase Storage."""
    if not supabase: return False, "No Client", "Client None"
    start_time = time.time()
    try:
        # List buckets
        res = supabase.storage.list_buckets()
        duration = (time.time() - start_time) * 1000
        if isinstance(res, list):
            return True, f"Storage OK ({duration:.2f} ms)", f"Buckets found: {len(res)}"
        return False, "Không lấy được danh sách Bucket", str(res)
    except Exception as e:
        return False, "Lỗi Storage", str(e)

def check_tts_service():
    """Kiểm tra dịch vụ chuyển văn bản thành giọng nói (Edge TTS)."""
    start_time = time.time()
    try:
        audio = get_tts_audio("Test")
        duration = (time.time() - start_time) * 1000
        if audio and len(audio) > 0:
            return True, f"TTS OK ({duration:.2f} ms)", f"Audio bytes: {len(audio)}"
        return False, "TTS không trả về dữ liệu", "Empty bytes"
    except Exception as e:
        return False, "Lỗi TTS", str(e)

def _benchmark_step(step_name, func, logs, results):
    """Hàm helper để chạy một bước benchmark và ghi log."""
    log_entry = lambda msg, status: logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [{status}] {step_name}: {msg}")
    
    start_time = time.time()
    try:
        func()
        duration = (time.time() - start_time) * 1000
        results[step_name.lower()] = duration
        log_entry(f"Hoàn thành trong {duration:.2f} ms", "OK")
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        results[step_name.lower()] = -1 # Đánh dấu lỗi
        log_entry(f"Thất bại sau {duration:.2f} ms. Lỗi: {e}", "ERROR")

def run_system_benchmark():
    """
    Chạy bài test toàn diện để đo hiệu năng hệ thống.
    """
    logs = []
    results = {}
    
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [START] INIT: Bắt đầu Benchmark toàn hệ thống...")

    # Lấy user_id của admin đang chạy để test DB Write
    admin_user_id = st.session_state.get("user_info", {}).get("id")
    if not admin_user_id:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] SETUP: Không tìm thấy admin user_id để test.")
        return {}, logs

    # --- Định nghĩa các bước test ---
    def db_read_test():
        # Dùng count để test nhẹ nhàng nhất
        supabase.table("Users").select("id", count="exact").limit(1).execute()

    def db_write_test():
        # Sửa lỗi: Ghi vào cột user_id thay vì username
        supabase.table("ActivityLog").insert({
            "action_type": "benchmark_test",
            "value": 1,
            "user_id": admin_user_id
        }).execute()

    def ai_gen_test():
        generate_response_with_fallback("Hello", ["ERR"])

    def tts_gen_test():
        get_tts_audio("Benchmark test audio generation.")

    # --- Chạy các bước ---
    _benchmark_step("DB_READ", db_read_test, logs, results)
    _benchmark_step("DB_WRITE", db_write_test, logs, results)
    _benchmark_step("AI_GEN", ai_gen_test, logs, results)
    _benchmark_step("TTS_GEN", tts_gen_test, logs, results)

    # --- Tính điểm ---
    # Nếu có bất kỳ bước nào lỗi, điểm không thể là 100
    if any(v == -1 for v in results.values()):
        score = 0
        # Tính điểm dựa trên các bước thành công
        successful_steps = {k: v for k, v in results.items() if v != -1}
        if successful_steps:
            # Trọng số: DB quan trọng hơn
            weights = {'db_read': 0.4, 'db_write': 0.4, 'ai_gen': 0.1, 'tts_gen': 0.1}
            # Ngưỡng (ms) để đạt điểm tối đa cho mỗi phần
            thresholds = {'db_read': 200, 'db_write': 250, 'ai_gen': 1500, 'tts_gen': 1000}
            
            for step, duration in successful_steps.items():
                step_score = max(0, 1 - (duration / thresholds[step])) # 0 to 1
                score += step_score * weights[step]
            
            score = int(score * 100)
        results['total_score'] = score

    else: # Tất cả thành công
        score = 100
        results['total_score'] = score

    total_time = sum([v for v in results.values() if v > 0])
    results['total_time'] = total_time
    
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [DONE] FINISH: Benchmark hoàn tất. Tổng thời gian: {total_time:.2f} ms. Score: {results['total_score']}/100")
    
    return results, logs
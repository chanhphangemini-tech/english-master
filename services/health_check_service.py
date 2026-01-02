"""
Comprehensive Health Check Service for Admin
Kiểm tra chi tiết từng tính năng trong app
"""
import streamlit as st
from core.database import supabase
from core.llm import generate_response_with_fallback
from core.tts import get_tts_audio
from services.vocab_service import get_daily_learning_batch, load_vocab_data
from services.user_service import get_user_stats
from services.shop_service import get_shop_items, get_user_inventory
from services.game_service import get_open_challenges
from services.admin_service import get_all_users, get_system_analytics
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class HealthCheckResult:
    """Kết quả của một health check"""
    def __init__(self, name: str, status: str, message: str = "", details: str = "", duration_ms: float = 0):
        self.name = name
        self.status = status  # 'success', 'warning', 'error'
        self.message = message
        self.details = details
        self.duration_ms = duration_ms
    
    def to_dict(self):
        return {
            'name': self.name,
            'status': self.status,
            'message': self.message,
            'details': self.details,
            'duration_ms': round(self.duration_ms, 2)
        }

def run_feature_health_check(feature_name: str) -> List[HealthCheckResult]:
    """
    Chạy health check cho một tính năng cụ thể
    
    Args:
        feature_name: Tên tính năng cần check (vd: 'vocabulary', 'mock_test', 'shop', etc.)
    
    Returns:
        List[HealthCheckResult]: Danh sách kết quả các tests
    """
    results = []
    
    if feature_name == 'vocabulary':
        results.extend(_check_vocabulary_features())
    elif feature_name == 'mock_test':
        results.extend(_check_mock_test_features())
    elif feature_name == 'shop':
        results.extend(_check_shop_features())
    elif feature_name == 'pvp':
        results.extend(_check_pvp_features())
    elif feature_name == 'grammar':
        results.extend(_check_grammar_features())
    elif feature_name == 'listening':
        results.extend(_check_listening_features())
    elif feature_name == 'speaking':
        results.extend(_check_speaking_features())
    elif feature_name == 'reading':
        results.extend(_check_reading_features())
    elif feature_name == 'writing':
        results.extend(_check_writing_features())
    elif feature_name == 'translation':
        results.extend(_check_translation_features())
    elif feature_name == 'dashboard':
        results.extend(_check_dashboard_features())
    elif feature_name == 'profile':
        results.extend(_check_profile_features())
    elif feature_name == 'all':
        # Check tất cả
        for feat in ['vocabulary', 'mock_test', 'shop', 'pvp', 'grammar', 'dashboard', 'profile']:
            results.extend(run_feature_health_check(feat))
    
    return results

def _check_vocabulary_features() -> List[HealthCheckResult]:
    """Check tính năng Vocabulary/SRS"""
    results = []
    user_id = st.session_state.get('user_info', {}).get('id')
    
    if not user_id:
        return [HealthCheckResult('Vocabulary - Auth', 'error', 'Không tìm thấy user_id')]
    
    # 1. Check load vocabulary data
    start = time.time()
    try:
        vocab_data = load_vocab_data()
        duration = (time.time() - start) * 1000
        if vocab_data and len(vocab_data) > 0:
            results.append(HealthCheckResult(
                'Vocabulary - Load Data',
                'success',
                f'Đã load {len(vocab_data)} từ vựng',
                f'Data size: {len(vocab_data)} items',
                duration
            ))
        else:
            results.append(HealthCheckResult(
                'Vocabulary - Load Data',
                'warning',
                'Không có dữ liệu từ vựng',
                'Vocab data is empty',
                duration
            ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Vocabulary - Load Data',
            'error',
            f'Lỗi load dữ liệu: {str(e)}',
            str(e),
            duration
        ))
    
    # 2. Check get daily learning batch
    start = time.time()
    try:
        batch = get_daily_learning_batch(user_id, limit=10)
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Vocabulary - Daily Batch',
            'success',
            f'Lấy được {len(batch) if batch else 0} từ cần học',
            f'Batch size: {len(batch) if batch else 0}',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Vocabulary - Daily Batch',
            'error',
            f'Lỗi lấy batch: {str(e)}',
            str(e),
            duration
        ))
    
    # 3. Check vocabulary table
    start = time.time()
    try:
        res = supabase.table("Vocabulary").select("id", count="exact").limit(1).execute()
        duration = (time.time() - start) * 1000
        count = res.count if res.count is not None else 0
        results.append(HealthCheckResult(
            'Vocabulary - Database',
            'success' if count > 0 else 'warning',
            f'Database có {count} từ vựng',
            f'Table accessible, count: {count}',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Vocabulary - Database',
            'error',
            f'Lỗi truy vấn database: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_mock_test_features() -> List[HealthCheckResult]:
    """Check tính năng Mock Test"""
    results = []
    user_id = st.session_state.get('user_info', {}).get('id')
    
    # 1. Check MockTestResults table
    start = time.time()
    try:
        res = supabase.table("MockTestResults").select("id", count="exact").limit(1).execute()
        duration = (time.time() - start) * 1000
        count = res.count if res.count is not None else 0
        results.append(HealthCheckResult(
            'Mock Test - Database',
            'success',
            f'Database có {count} kết quả thi',
            f'Table accessible, count: {count}',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Mock Test - Database',
            'error',
            f'Lỗi truy vấn database: {str(e)}',
            str(e),
            duration
        ))
    
    # 2. Check AI generation (test prompt)
    start = time.time()
    try:
        response = generate_response_with_fallback("Generate a simple English test question.", ["ERROR"])
        duration = (time.time() - start) * 1000
        if response and response != "ERROR":
            results.append(HealthCheckResult(
                'Mock Test - AI Generation',
                'success',
                'AI có thể generate câu hỏi',
                f'Response length: {len(response)} chars',
                duration
            ))
        else:
            results.append(HealthCheckResult(
                'Mock Test - AI Generation',
                'error',
                'AI không thể generate',
                'AI returned error',
                duration
            ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Mock Test - AI Generation',
            'error',
            f'Lỗi AI: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_shop_features() -> List[HealthCheckResult]:
    """Check tính năng Shop"""
    results = []
    user_id = st.session_state.get('user_info', {}).get('id')
    
    # 1. Check shop items
    start = time.time()
    try:
        items = get_shop_items()
        duration = (time.time() - start) * 1000
        if items and len(items) > 0:
            results.append(HealthCheckResult(
                'Shop - Get Items',
                'success',
                f'Có {len(items)} items trong shop',
                f'Items count: {len(items)}',
                duration
            ))
        else:
            results.append(HealthCheckResult(
                'Shop - Get Items',
                'warning',
                'Shop không có items',
                'Items list is empty',
                duration
            ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Shop - Get Items',
            'error',
            f'Lỗi lấy items: {str(e)}',
            str(e),
            duration
        ))
    
    # 2. Check user inventory
    if user_id:
        start = time.time()
        try:
            inventory = get_user_inventory(user_id)
            duration = (time.time() - start) * 1000
            results.append(HealthCheckResult(
                'Shop - User Inventory',
                'success',
                f'User có {len(inventory) if inventory else 0} items',
                f'Inventory accessible',
                duration
            ))
        except Exception as e:
            duration = (time.time() - start) * 1000
            results.append(HealthCheckResult(
                'Shop - User Inventory',
                'error',
                f'Lỗi lấy inventory: {str(e)}',
                str(e),
                duration
            ))
    
    return results

def _check_pvp_features() -> List[HealthCheckResult]:
    """Check tính năng PvP"""
    results = []
    
    # 1. Check PvPChallenges table
    start = time.time()
    try:
        res = supabase.table("PvPChallenges").select("id", count="exact").limit(1).execute()
        duration = (time.time() - start) * 1000
        count = res.count if res.count is not None else 0
        results.append(HealthCheckResult(
            'PvP - Database',
            'success',
            f'Database có {count} challenges',
            f'Table accessible, count: {count}',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'PvP - Database',
            'error',
            f'Lỗi truy vấn database: {str(e)}',
            str(e),
            duration
        ))
    
    # 2. Check get open challenges
    start = time.time()
    try:
        challenges = get_open_challenges()
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'PvP - Get Open Challenges',
            'success',
            f'Có {len(challenges) if challenges else 0} challenges mở',
            f'Function working',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'PvP - Get Open Challenges',
            'error',
            f'Lỗi lấy challenges: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_grammar_features() -> List[HealthCheckResult]:
    """Check tính năng Grammar"""
    results = []
    
    # Check GrammarLessons table
    start = time.time()
    try:
        res = supabase.table("GrammarLessons").select("id", count="exact").limit(1).execute()
        duration = (time.time() - start) * 1000
        count = res.count if res.count is not None else 0
        results.append(HealthCheckResult(
            'Grammar - Database',
            'success' if count > 0 else 'warning',
            f'Database có {count} bài học ngữ pháp',
            f'Table accessible, count: {count}',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Grammar - Database',
            'error',
            f'Lỗi truy vấn database: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_listening_features() -> List[HealthCheckResult]:
    """Check tính năng Listening"""
    results = []
    
    # Check TTS service
    start = time.time()
    try:
        audio = get_tts_audio("Test audio")
        duration = (time.time() - start) * 1000
        if audio and len(audio) > 0:
            results.append(HealthCheckResult(
                'Listening - TTS Service',
                'success',
                'TTS service hoạt động tốt',
                f'Audio size: {len(audio)} bytes',
                duration
            ))
        else:
            results.append(HealthCheckResult(
                'Listening - TTS Service',
                'error',
                'TTS không trả về audio',
                'Audio is empty',
                duration
            ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Listening - TTS Service',
            'error',
            f'Lỗi TTS: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_speaking_features() -> List[HealthCheckResult]:
    """Check tính năng Speaking"""
    results = []
    
    # Similar to listening - TTS check
    start = time.time()
    try:
        audio = get_tts_audio("Test")
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Speaking - TTS Service',
            'success' if audio and len(audio) > 0 else 'error',
            'TTS service accessible' if audio and len(audio) > 0 else 'TTS failed',
            f'Audio: {len(audio) if audio else 0} bytes',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Speaking - TTS Service',
            'error',
            f'Lỗi TTS: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_reading_features() -> List[HealthCheckResult]:
    """Check tính năng Reading"""
    results = []
    
    # Check AI generation for reading
    start = time.time()
    try:
        response = generate_response_with_fallback("Generate a short reading passage.", ["ERROR"])
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Reading - AI Generation',
            'success' if response and response != "ERROR" else 'error',
            'AI có thể generate' if response and response != "ERROR" else 'AI failed',
            f'Response: {len(response) if response else 0} chars',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Reading - AI Generation',
            'error',
            f'Lỗi AI: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_writing_features() -> List[HealthCheckResult]:
    """Check tính năng Writing"""
    results = []
    
    # Similar to reading - AI check
    start = time.time()
    try:
        response = generate_response_with_fallback("Say OK", ["ERROR"])
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Writing - AI Service',
            'success' if response and response != "ERROR" else 'error',
            'AI accessible' if response and response != "ERROR" else 'AI failed',
            f'AI response received',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Writing - AI Service',
            'error',
            f'Lỗi AI: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_translation_features() -> List[HealthCheckResult]:
    """Check tính năng Translation"""
    results = []
    
    # AI check
    start = time.time()
    try:
        response = generate_response_with_fallback("Translate: Hello", ["ERROR"])
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Translation - AI Service',
            'success' if response and response != "ERROR" else 'error',
            'AI accessible' if response and response != "ERROR" else 'AI failed',
            f'AI working',
            duration
        ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Translation - AI Service',
            'error',
            f'Lỗi AI: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_dashboard_features() -> List[HealthCheckResult]:
    """Check tính năng Dashboard"""
    results = []
    user_id = st.session_state.get('user_info', {}).get('id')
    
    if not user_id:
        return [HealthCheckResult('Dashboard - Auth', 'error', 'Không tìm thấy user_id')]
    
    # Check get_user_stats
    start = time.time()
    try:
        stats = get_user_stats(user_id)
        duration = (time.time() - start) * 1000
        if stats:
            results.append(HealthCheckResult(
                'Dashboard - User Stats',
                'success',
                'Lấy được user stats',
                f'Stats keys: {list(stats.keys())}',
                duration
            ))
        else:
            results.append(HealthCheckResult(
                'Dashboard - User Stats',
                'warning',
                'Stats rỗng',
                'No stats returned',
                duration
            ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Dashboard - User Stats',
            'error',
            f'Lỗi lấy stats: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def _check_profile_features() -> List[HealthCheckResult]:
    """Check tính năng Profile"""
    results = []
    user_id = st.session_state.get('user_info', {}).get('id')
    
    if not user_id:
        return [HealthCheckResult('Profile - Auth', 'error', 'Không tìm thấy user_id')]
    
    # Check Users table access
    start = time.time()
    try:
        res = supabase.table("Users").select("*").eq("id", user_id).single().execute()
        duration = (time.time() - start) * 1000
        if res.data:
            results.append(HealthCheckResult(
                'Profile - User Data',
                'success',
                'Lấy được user data',
                f'User: {res.data.get("username", "N/A")}',
                duration
            ))
        else:
            results.append(HealthCheckResult(
                'Profile - User Data',
                'error',
                'Không tìm thấy user',
                'User not found',
                duration
            ))
    except Exception as e:
        duration = (time.time() - start) * 1000
        results.append(HealthCheckResult(
            'Profile - User Data',
            'error',
            f'Lỗi truy vấn: {str(e)}',
            str(e),
            duration
        ))
    
    return results

def get_health_check_summary(results: List[HealthCheckResult]) -> Dict[str, Any]:
    """Tạo summary từ kết quả health check"""
    total = len(results)
    success = len([r for r in results if r.status == 'success'])
    warning = len([r for r in results if r.status == 'warning'])
    error = len([r for r in results if r.status == 'error'])
    
    avg_duration = sum(r.duration_ms for r in results) / total if total > 0 else 0
    
    return {
        'total': total,
        'success': success,
        'warning': warning,
        'error': error,
        'success_rate': round((success / total * 100) if total > 0 else 0, 2),
        'avg_duration_ms': round(avg_duration, 2),
        'timestamp': get_vn_now_utc()
    }


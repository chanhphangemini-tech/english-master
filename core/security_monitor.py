"""
Security Monitor - Chống spam và tấn công
Theo dõi và chặn các hành vi phá hoại từ users
"""
import streamlit as st
from core.database import supabase
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Optional, Tuple
import time
from core.timezone_utils import get_vn_now_utc

logger = logging.getLogger(__name__)

class SecurityMonitor:
    """Monitor và chặn các hành vi phá hoại"""
    
    # Các hành vi nghi ngờ
    SUSPICIOUS_PATTERNS = {
        'rapid_actions': {'threshold': 50, 'window_seconds': 60, 'action': 'warn'},  # 50 actions trong 60s
        'failed_requests': {'threshold': 20, 'window_seconds': 300, 'action': 'warn'},  # 20 failed trong 5 phút
        'excessive_ai_calls': {'threshold': 100, 'window_seconds': 600, 'action': 'disable'},  # 100 AI calls trong 10 phút - TỰ ĐỘNG DISABLE
        'abnormal_vocab_learning': {'threshold': 500, 'window_seconds': 3600, 'action': 'warn'},  # 500 từ trong 1 giờ
        'repeated_errors': {'threshold': 30, 'window_seconds': 300, 'action': 'warn'},  # 30 errors trong 5 phút
    }
    
    # Số lần flag trước khi auto-disable
    AUTO_DISABLE_THRESHOLD = 3  # Sau 3 lần flag trong 24h sẽ auto-disable
    
    @staticmethod
    def log_user_action(user_id: int, action_type: str, success: bool = True, metadata: Dict = None):
        """
        Log hành động của user để theo dõi
        
        Args:
            user_id: ID của user
            action_type: Loại hành động (vd: 'ai_call', 'vocab_learn', 'pvp_create', etc.)
            success: Thành công hay thất bại
            metadata: Thông tin bổ sung
        """
        if not supabase:
            return
        
        try:
            # Log vào ActivityLog
            supabase.table("ActivityLog").insert({
                "user_id": user_id,
                "action_type": action_type,
                "value": 1 if success else 0,
                "metadata": metadata or {}
            }).execute()
            
            # Kiểm tra patterns nghi ngờ
            SecurityMonitor._check_suspicious_patterns(user_id, action_type, success)
        except Exception as e:
            logger.error(f"Error logging user action: {e}")
    
    @staticmethod
    def _check_suspicious_patterns(user_id: int, action_type: str, success: bool):
        """Kiểm tra các patterns nghi ngờ"""
        try:
            # Use VN timezone for timestamp calculations (convert to UTC for database)
            now_utc_str = get_vn_now_utc()
            from datetime import datetime, timezone
            now = datetime.fromisoformat(now_utc_str.replace('Z', '+00:00'))
            
            # 1. Check rapid actions
            window = timedelta(seconds=60)
            recent_actions = supabase.table("ActivityLog")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", (now - window).isoformat())\
                .execute()
            
            if recent_actions.count and recent_actions.count > SecurityMonitor.SUSPICIOUS_PATTERNS['rapid_actions']['threshold']:
                SecurityMonitor._handle_suspicious_activity(
                    user_id, 
                    'rapid_actions',
                    f"User thực hiện {recent_actions.count} actions trong 60s"
                )
            
            # 2. Check failed requests
            if not success:
                window = timedelta(seconds=300)
                failed_count = supabase.table("ActivityLog")\
                    .select("id", count="exact")\
                    .eq("user_id", user_id)\
                    .eq("value", 0)\
                    .gte("created_at", (now - window).isoformat())\
                    .execute()
                
                if failed_count.count and failed_count.count > SecurityMonitor.SUSPICIOUS_PATTERNS['failed_requests']['threshold']:
                    SecurityMonitor._handle_suspicious_activity(
                        user_id,
                        'failed_requests',
                        f"User có {failed_count.count} failed requests trong 5 phút"
                    )
            
            # 3. Check excessive AI calls
            if action_type in ['ai_call', 'ai_generation']:
                window = timedelta(seconds=600)
                ai_calls = supabase.table("ActivityLog")\
                    .select("id", count="exact")\
                    .eq("user_id", user_id)\
                    .eq("action_type", action_type)\
                    .gte("created_at", (now - window).isoformat())\
                    .execute()
                
                if ai_calls.count and ai_calls.count > SecurityMonitor.SUSPICIOUS_PATTERNS['excessive_ai_calls']['threshold']:
                    SecurityMonitor._handle_suspicious_activity(
                        user_id,
                        'excessive_ai_calls',
                        f"User có {ai_calls.count} AI calls trong 10 phút",
                        block=True,
                        auto_disable=True  # Tự động disable cho excessive AI calls
                    )
        
        except Exception as e:
            logger.error(f"Error checking suspicious patterns: {e}")
    
    @staticmethod
    def _handle_suspicious_activity(user_id: int, pattern_type: str, message: str, block: bool = False, auto_disable: bool = False):
        """
        Xử lý khi phát hiện hành vi nghi ngờ
        
        Args:
            user_id: ID của user
            pattern_type: Loại pattern (vd: 'rapid_actions')
            message: Thông báo
            block: Có block user không
            auto_disable: Có tự động disable user không (cho các trường hợp nghiêm trọng)
        """
        try:
            # Log vào ActivityLog với metadata đặc biệt
            supabase.table("ActivityLog").insert({
                "user_id": user_id,
                "action_type": "security_alert",
                "value": 1,
                "metadata": {
                    "pattern_type": pattern_type,
                    "message": message,
                    "blocked": block,
                    "auto_disable": auto_disable
                }
            }).execute()
            
            # Nếu cần block, đánh dấu user
            if block:
                SecurityMonitor._flag_user(user_id, pattern_type, message)
            
            # Nếu cần auto-disable (cho các trường hợp nghiêm trọng)
            if auto_disable:
                SecurityMonitor._auto_disable_user(user_id, pattern_type, message)
            
            # Kiểm tra nếu số lần flag đã vượt ngưỡng
            if block:
                SecurityMonitor._check_auto_disable_threshold(user_id)
            
            logger.warning(f"Security Alert - User {user_id}: {message} (block={block}, auto_disable={auto_disable})")
        except Exception as e:
            logger.error(f"Error handling suspicious activity: {e}")
    
    @staticmethod
    def _flag_user(user_id: int, reason: str, details: str):
        """
        Đánh dấu user là nghi ngờ
        
        Có thể:
        1. Cập nhật status user thành 'flagged'
        2. Tạo bản ghi trong bảng SecurityFlags (nếu có)
        3. Tạm thời disable một số tính năng
        """
        try:
            # Log vào ActivityLog với metadata
            supabase.table("ActivityLog").insert({
                "user_id": user_id,
                "action_type": "user_flagged",
                "value": 1,
                "metadata": {
                    "reason": reason,
                    "details": details,
                    "flagged_at": get_vn_now_utc()
                }
            }).execute()
            
            logger.warning(f"User {user_id} flagged: {reason} - {details}")
        except Exception as e:
            logger.error(f"Error flagging user: {e}")
    
    @staticmethod
    def _auto_disable_user(user_id: int, reason: str, details: str):
        """
        Tự động disable user do hành vi nghi ngờ nghiêm trọng
        
        Args:
            user_id: ID của user
            reason: Lý do disable
            details: Chi tiết
        """
        try:
            # Kiểm tra xem user có phải admin không (không disable admin)
            user = supabase.table("Users")\
                .select("role, status")\
                .eq("id", user_id)\
                .single()\
                .execute()
            
            if user.data:
                role = str(user.data.get('role', 'user')).lower()
                if role == 'admin':
                    logger.warning(f"Cannot auto-disable admin user {user_id}")
                    return
                
                # Chỉ disable nếu user chưa bị disabled
                current_status = str(user.data.get('status', 'active')).lower()
                if current_status == 'disabled':
                    logger.info(f"User {user_id} already disabled")
                    return
            
            # Disable user bằng cách update status
            supabase.table("Users").update({"status": "disabled"}).eq("id", user_id).execute()
            
            # Log vào ActivityLog
            supabase.table("ActivityLog").insert({
                "user_id": user_id,
                "action_type": "user_auto_disabled",
                "value": 1,
                "metadata": {
                    "reason": reason,
                    "details": details,
                    "disabled_at": get_vn_now_utc(),
                    "auto_disabled": True
                }
            }).execute()
            
            logger.warning(f"User {user_id} AUTO-DISABLED: {reason} - {details}")
        except Exception as e:
            logger.error(f"Error auto-disabling user: {e}")
    
    @staticmethod
    def _check_auto_disable_threshold(user_id: int):
        """
        Kiểm tra nếu số lần flag đã vượt ngưỡng -> auto-disable
        
        Args:
            user_id: ID của user
        """
        try:
            # Đếm số lần flag trong 24h
            window = timedelta(hours=24)
            flags_count = supabase.table("ActivityLog")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("action_type", "user_flagged")\
                .gte("created_at", (datetime.now(timezone.utc) - window).isoformat())\
                .execute()
            
            if flags_count.count and flags_count.count >= SecurityMonitor.AUTO_DISABLE_THRESHOLD:
                # Kiểm tra xem đã bị disable chưa (tránh disable nhiều lần)
                user = supabase.table("Users")\
                    .select("status, role")\
                    .eq("id", user_id)\
                    .single()\
                    .execute()
                
                if user.data:
                    role = str(user.data.get('role', 'user')).lower()
                    current_status = str(user.data.get('status', 'active')).lower()
                    
                    # Không disable admin và user đã disabled
                    if role != 'admin' and current_status != 'disabled':
                        SecurityMonitor._auto_disable_user(
                            user_id,
                            'multiple_flags',
                            f"User đã bị flag {flags_count.count} lần trong 24h (threshold: {SecurityMonitor.AUTO_DISABLE_THRESHOLD})"
                        )
        except Exception as e:
            logger.error(f"Error checking auto-disable threshold: {e}")
    
    @staticmethod
    def check_user_status(user_id: int) -> Tuple[bool, str]:
        """
        Kiểm tra status của user (có bị block/flag không)
        
        Returns:
            (is_allowed, message): (True/False, message)
        """
        if not supabase:
            return True, "OK"
        
        try:
            # Check recent security alerts (skip if connection issue)
            try:
                window = timedelta(hours=24)
                recent_alerts = supabase.table("ActivityLog")\
                    .select("metadata")\
                    .eq("user_id", user_id)\
                    .eq("action_type", "user_flagged")\
                    .gte("created_at", (datetime.now(timezone.utc) - window).isoformat())\
                    .limit(1)\
                    .execute()
                
                if recent_alerts.data and len(recent_alerts.data) > 0:
                    # User đã bị flag trong 24h qua
                    return False, "Tài khoản của bạn đã bị đánh dấu do hành vi bất thường. Vui lòng liên hệ admin."
            except Exception as alert_error:
                # Log warning but continue - connection issue với ActivityLog không critical
                logger.debug(f"Could not check security alerts for user {user_id}: {alert_error}")
            
            # Check user status (critical check)
            try:
                user = supabase.table("Users")\
                    .select("status")\
                    .eq("id", user_id)\
                    .maybe_single()\
                    .execute()
                
                if user.data and user.data.get("status") == "disabled":
                    return False, "Tài khoản của bạn đã bị vô hiệu hóa."
            except Exception as user_error:
                # Log warning but continue - connection issue
                logger.debug(f"Could not check user status for user {user_id}: {user_error}")
            
            return True, "OK"
        
        except Exception as e:
            # Log error only for unexpected exceptions
            error_str = str(e)
            if "Resource temporarily unavailable" in error_str or "Errno 11" in error_str:
                # This is a connection pool/timeout issue - log as debug to reduce noise
                logger.debug(f"Connection issue checking user status for user {user_id}: {e}")
            else:
                logger.error(f"Error checking user status for user {user_id}: {e}")
            # Fail open - cho phép user nếu có lỗi (security best practice)
            return True, "OK"
    
    @staticmethod
    def get_user_security_stats(user_id: int) -> Dict:
        """Lấy thống kê security của user (cho admin)"""
        try:
            # Use VN timezone for timestamp calculations
            now_utc_str = get_vn_now_utc()
            from datetime import datetime, timezone
            now = datetime.fromisoformat(now_utc_str.replace('Z', '+00:00'))
            stats = {}
            
            # Actions trong 24h
            window_24h = timedelta(hours=24)
            actions_24h = supabase.table("ActivityLog")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .gte("created_at", (now - window_24h).isoformat())\
                .execute()
            stats['actions_24h'] = actions_24h.count or 0
            
            # Failed requests trong 24h
            failed_24h = supabase.table("ActivityLog")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("value", 0)\
                .gte("created_at", (now - window_24h).isoformat())\
                .execute()
            stats['failed_24h'] = failed_24h.count or 0
            
            # Security alerts trong 7 ngày
            window_7d = timedelta(days=7)
            alerts_7d = supabase.table("ActivityLog")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("action_type", "security_alert")\
                .gte("created_at", (now - window_7d).isoformat())\
                .execute()
            stats['security_alerts_7d'] = alerts_7d.count or 0
            
            # User flags
            flags = supabase.table("ActivityLog")\
                .select("metadata")\
                .eq("user_id", user_id)\
                .eq("action_type", "user_flagged")\
                .order("created_at", desc=True)\
                .limit(5)\
                .execute()
            stats['recent_flags'] = flags.data or []
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting user security stats: {e}")
            return {}

